import sqlite3
import os
from datetime import datetime
import bcrypt

class LuxuryDB:
    def __init__(self):
        self.db_path = 'luxury_data.db'
        
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row 
        self.create_tables()

        # Database Upgrades
        try:
            self.conn.execute("ALTER TABLE settings ADD COLUMN logo_path TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass 
            
        try:
            self.conn.execute("ALTER TABLE rooms ADD COLUMN amenities TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass
            
        try:
            self.conn.execute("ALTER TABLE inventory ADD COLUMN category TEXT DEFAULT 'Uncategorized'")
            self.conn.execute("ALTER TABLE inventory ADD COLUMN image_path TEXT DEFAULT ''")
        except sqlite3.OperationalError:
            pass

        try:
            self.conn.execute("ALTER TABLE settings ADD COLUMN currency_symbol TEXT DEFAULT '₦'")
        except sqlite3.OperationalError:
            pass

        self.conn.commit()
        self.initialize_settings()
        self.initialize_amenities()
        self._migrate_plain_text_passwords()

    def execute_query(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_non_query(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, business_name TEXT, primary_color TEXT, caution_fee REAL, logo_path TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, caution_fee REAL, is_available INTEGER DEFAULT 1, image_url TEXT, amenities TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, guest_phone TEXT, room_id INTEGER, adults INTEGER DEFAULT 1, children INTEGER DEFAULT 0, caution_fee REAL DEFAULT 0, check_in TEXT, check_out TEXT, status TEXT DEFAULT 'Active', FOREIGN KEY (room_id) REFERENCES rooms (id))''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password TEXT NOT NULL, role TEXT DEFAULT 'staff')''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS activity_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, action TEXT, details TEXT, timestamp TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS amenities (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS amenities (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT UNIQUE NOT NULL, price REAL DEFAULT 0.0, stock_level INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, booking_id INTEGER, guest_name TEXT, item_id INTEGER, item_name TEXT, quantity INTEGER, price REAL, total REAL, payment_status TEXT, timestamp TEXT)''')

        default_admin_username = os.getenv("LUXURY_PMS_DEFAULT_ADMIN_USERNAME", "admin")
        default_admin_password = os.getenv("LUXURY_PMS_DEFAULT_ADMIN_PASSWORD", "1234")
        default_admin_role = os.getenv("LUXURY_PMS_DEFAULT_ADMIN_ROLE", "admin")

        cursor.execute("SELECT * FROM users WHERE username = ?", (default_admin_username,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (default_admin_username, default_admin_password, default_admin_role),
            )
        
        self.conn.commit()

    def initialize_settings(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM settings WHERE id = 1')
        if not cursor.fetchone():
            cursor.execute("INSERT INTO settings (id, business_name, primary_color, caution_fee, logo_path, currency_symbol) VALUES (1, 'Hotel Management System', '#2ecc71', 50000, '', '₦')")
            self.conn.commit()

    def initialize_amenities(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM amenities')
        result = cursor.fetchone()
        if result['count'] == 0:
            defaults = ["24/7 electricity", "Free Wi-Fi", "Smart TV", "Gym", "Fully equipped kitchen", "Security"]
            for amenity in defaults:
                cursor.execute("INSERT INTO amenities (name) VALUES (?)", (amenity,))
            self.conn.commit()

    def verify_login(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT role, password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if not result:
            return None
        stored_pw = result['password']
        try:
            # Check against bcrypt hash
            if bcrypt.checkpw(password.encode('utf-8'), stored_pw.encode('utf-8')):
                return result
        except Exception:
            # Fallback: plain text match (should not happen after migration)
            if stored_pw == password:
                return result
        return None

    def _migrate_plain_text_passwords(self):
        """Auto-migrate any plain-text passwords to bcrypt hashes on startup."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, password FROM users")
        users = cursor.fetchall()
        for user in users:
            pw = user['password']
            is_hashed = pw.startswith('$2b$') or pw.startswith('$2a$')
            if not is_hashed:
                hashed = bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, user['id']))
        self.conn.commit()

    # --- SETTINGS ---
    def get_settings(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM settings WHERE id = 1')
        row = cursor.fetchone()
        return dict(row) if row else {}

    def save_settings(self, data):
        try:
            self.execute_non_query(
                "UPDATE settings SET business_name=?, primary_color=?, caution_fee=?, logo_path=?, currency_symbol=? WHERE id=1",
                (data['business_name'], data['primary_color'], data['caution_fee'], data['logo_path'], data.get('currency_symbol', '₦'))
            )
            return True
        except Exception as e:
            print("Database Error:", e)
            return False

    # --- ROOMS ---
    def get_all_rooms(self):
        return self.execute_query("SELECT * FROM rooms")

    def register_new_room(self, name, price, caution, img, amenities=""):
        try:
            self.execute_non_query(
                "INSERT INTO rooms (name, price, caution_fee, image_url, amenities) VALUES (?, ?, ?, ?, ?)",
                (name, price, caution, img, amenities)
            )
            return True
        except Exception as e:
            print("Database Error:", e)
            return False

    def delete_room(self, room_id):
        try:
            self.execute_non_query("DELETE FROM rooms WHERE id = ?", (room_id,))
            return True
        except Exception as e:
            print("Database Error:", e)
            return False

    # --- AMENITIES ---
    def get_all_amenities(self):
        return [row['name'] for row in self.execute_query("SELECT name FROM amenities")]

    def add_amenity(self, name):
        try:
            self.execute_non_query("INSERT INTO amenities (name) VALUES (?)", (name,))
            return True
        except sqlite3.IntegrityError:
            return False # Already exists

    def delete_amenity(self, name):
        try:
            self.execute_non_query("DELETE FROM amenities WHERE name = ?", (name,))
            return True
        except Exception as e:
            return False

    # --- CHECK-IN / BOOKINGS ---
    def get_available_rooms(self):
        return self.execute_query("SELECT * FROM rooms WHERE is_available = 1")

    def create_booking(self, customer_name, guest_phone, room_id, adults, children, caution_fee):
        try:
            check_in_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_non_query(
                "INSERT INTO bookings (customer_name, guest_phone, room_id, adults, children, caution_fee, check_in, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')",
                (customer_name, guest_phone, room_id, adults, children, caution_fee, check_in_date)
            )
            # Update room to unavailable
            self.execute_non_query("UPDATE rooms SET is_available = 0 WHERE id = ?", (room_id,))
            return True
        except Exception as e:
            print("Database Error:", e)
            return False

    # --- OTHERS (Restored) ---
    def get_active_bookings(self):
        try:
            return [dict(row) for row in self.execute_query("""
                SELECT b.id as booking_id, b.customer_name, b.guest_phone, b.check_in, b.check_out, 
                       b.caution_fee, b.room_id, r.name as room_name, r.price as room_price
                FROM bookings b JOIN rooms r ON b.room_id = r.id WHERE b.status = 'Active'
            """)]
        except: return []

    def extend_stay(self, booking_id, new_checkout_date):
        try:
            self.execute_non_query("UPDATE bookings SET check_out = ? WHERE id = ?", (new_checkout_date, booking_id))
            return True
        except Exception as e:
            print("Database Error:", e)
            return False

    def complete_checkout(self, b_id, r_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE bookings SET status = 'Completed' WHERE id = ?", (b_id,))
        cursor.execute("UPDATE rooms SET is_available = 1 WHERE id = ?", (r_id,))
        self.conn.commit()
        return True

    def get_all_users(self):
        return [dict(row) for row in self.execute_query("SELECT id, username, role FROM users")]

    def add_user(self, username, password, role):
        try:
            hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            self.execute_non_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, hashed, role))
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_user(self, user_id):
        try:
            if int(user_id) == 1:
                return False
            self.execute_non_query("DELETE FROM users WHERE id = ?", (user_id,))
            return True
        except Exception:
            return False

    # --- INVENTORY ---
    def get_inventory(self):
        return [dict(row) for row in self.execute_query("SELECT * FROM inventory ORDER BY item_name")]
        
    def add_inventory_item(self, name, price, stock, category="Uncategorized", image_path=""):
        try:
            self.execute_non_query(
                "INSERT INTO inventory (item_name, price, stock_level, category, image_path) VALUES (?, ?, ?, ?, ?)", 
                (name, price, stock, category, image_path)
            )
            return True
        except sqlite3.IntegrityError:
            return False
            
    def update_stock(self, item_id, new_stock):
        self.execute_non_query("UPDATE inventory SET stock_level = ? WHERE id = ?", (new_stock, item_id))

    def add_order(self, booking_id, guest_name, item_id, item_name, quantity, price, payment_status):
        try:
            total = quantity * price
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.execute_non_query(
                "INSERT INTO orders (booking_id, guest_name, item_id, item_name, quantity, price, total, payment_status, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (booking_id, guest_name, item_id, item_name, quantity, price, total, payment_status, timestamp)
            )
            # Decrement stock
            self.execute_non_query("UPDATE inventory SET stock_level = stock_level - ? WHERE id = ?", (quantity, item_id))
            return True
        except Exception as e:
            print("Database Error:", e)
            return False

    def get_unpaid_orders_for_booking(self, booking_id):
        return [dict(row) for row in self.execute_query("SELECT * FROM orders WHERE booking_id = ? AND payment_status = 'Charge to Room'", (booking_id,))]

    # --- LOGS ---
    def log_action(self, username, action, details=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute_non_query("INSERT INTO activity_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)", (username, action, details, timestamp))

    def get_logs(self):
        return [dict(r) for r in self.execute_query("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 100")]
