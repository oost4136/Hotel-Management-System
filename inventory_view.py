import customtkinter as ctk
from tkinter import messagebox, filedialog
import os
import shutil
from PIL import Image

class InventoryView(ctk.CTkFrame):
    def __init__(self, parent, db, username, role):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.username = username
        self.role = role
        self.settings = self.db.get_settings()
        self.theme_color = self.settings.get('primary_color', '#2ecc71')
        self.currency = self.settings.get('currency_symbol', '₦')
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header, text="BAR / RESTAURANT INVENTORY", font=("Arial", 24, "bold"), text_color=self.theme_color).pack(side="left")
        
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="left", padx=20)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.load_inventory())
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search items...", textvariable=self.search_var, width=200)
        self.search_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(search_frame, text="Search", width=60, fg_color=self.theme_color, command=self.load_inventory).pack(side="left")

        if self.role == 'admin':
            ctk.CTkButton(header, text="+ Add Item", fg_color=self.theme_color, command=self.open_add_modal).pack(side="right")

        # Scrollable Grid
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.load_inventory()

    def load_inventory(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        items = self.db.get_inventory()
        
        if hasattr(self, 'search_var'):
            query = self.search_var.get().strip().lower()
            if query:
                items = [item for item in items if query in str(item.get('item_name', '')).lower() or query in str(item.get('category', '')).lower()]

        if not items:
            ctk.CTkLabel(self.grid_frame, text="No items found.", text_color="gray", font=("Arial", 16)).pack(pady=50)
            return

        for idx, item in enumerate(items):
            card = ctk.CTkFrame(self.grid_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5)
            
            # Image Section
            img_path = item.get('image_path', '')
            try:
                if img_path and os.path.exists(img_path):
                    pil_img = Image.open(img_path)
                else:
                    pil_img = Image.new('RGB', (80, 80), color='#444444') 
                
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(80, 80))
                img_label = ctk.CTkLabel(card, image=ctk_img, text="")
                img_label.image = ctk_img # Keep reference
                img_label.pack(side="left", padx=15, pady=10)
            except Exception:
                pass

            # Item Info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=15)
            
            ctk.CTkLabel(info_frame, text=f"{item['item_name']}", font=("Arial", 18, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Category: {item.get('category', 'Uncategorized')} | Price: {self.currency}{item['price']:,.2f}", text_color="gray").pack(anchor="w")
            
            stock = item['stock_level']
            stock_color = "#e74c3c" if stock < 5 else "#2ecc71"
            ctk.CTkLabel(info_frame, text=f"Current Stock: {stock}", text_color=stock_color, font=("Arial", 14, "bold")).pack(anchor="w")

            # Actions
            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(side="right", padx=15, pady=15)
            
            ctk.CTkButton(action_frame, text="Sell", width=80, fg_color="#f39c12", hover_color="#d68910", command=lambda i=item: self.open_sell_modal(i)).pack(side="left", padx=15)
            ctk.CTkButton(action_frame, text="-1", width=40, fg_color="#e74c3c", command=lambda i=item: self.adjust_stock(i, -1)).pack(side="left", padx=5)
            ctk.CTkButton(action_frame, text="+1", width=40, fg_color="#2ecc71", command=lambda i=item: self.adjust_stock(i, 1)).pack(side="left", padx=5)
            ctk.CTkButton(action_frame, text="+10", width=40, fg_color="#3498db", command=lambda i=item: self.adjust_stock(i, 10)).pack(side="left", padx=5)

    def adjust_stock(self, item, amount):
        new_stock = max(0, item['stock_level'] + amount)
        self.db.update_stock(item['id'], new_stock)
        self.db.log_action(self.username, "Stock Adjusted", f"{item['item_name']}: {item['stock_level']} -> {new_stock}")
        self.load_inventory()

    def open_sell_modal(self, item):
        if item['stock_level'] <= 0:
            messagebox.showerror("Out of Stock", "Cannot sell this item. Stock is zero.")
            return
        SellItemModal(self, self.db, self.username, item, self.load_inventory, self.currency)

    def open_add_modal(self):
        AddItemModal(self, self.db, self.username, self.load_inventory)

class AddItemModal(ctk.CTkToplevel):
    def __init__(self, parent, db, username, refresh_callback):
        super().__init__(parent)
        self.title("Add Inventory Item")
        self.geometry("400x550")
        self.db = db
        self.username = username
        self.refresh_callback = refresh_callback
        self.selected_image_path = ""
        
        self.attributes("-topmost", True)
        self.grab_set()
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="New Item Details", font=("Arial", 20, "bold")).pack(pady=20)
        
        # Image Picker
        self.img_btn = ctk.CTkButton(self, text="Upload Image", fg_color="gray", command=self.pick_image)
        self.img_btn.pack(pady=5)

        ctk.CTkLabel(self, text="Category:").pack(pady=(10, 0))
        self.cat_entry = ctk.CTkEntry(self, width=250, placeholder_text="e.g. Drinks, Food")
        self.cat_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Item Name:").pack()
        self.name_entry = ctk.CTkEntry(self, width=250)
        self.name_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Price (currency):").pack()
        self.price_entry = ctk.CTkEntry(self, width=250)
        self.price_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Initial Stock:").pack()
        self.stock_entry = ctk.CTkEntry(self, width=250)
        self.stock_entry.pack(pady=5)

        ctk.CTkButton(self, text="Save Item", fg_color="#2ecc71", command=self.save).pack(pady=20)

    def pick_image(self):
        self.attributes("-topmost", False)
        filepath = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        self.attributes("-topmost", True)
        if filepath:
            self.selected_image_path = filepath
            self.img_btn.configure(text="Image Selected ✓", fg_color="#2ecc71")

    def save(self):
        name = self.name_entry.get().strip()
        cat = self.cat_entry.get().strip() or "Uncategorized"
        price_str = self.price_entry.get().strip()
        stock_str = self.stock_entry.get().strip()

        if not name or not price_str or not stock_str:
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            price = float(price_str)
            stock = int(stock_str)
        except ValueError:
            messagebox.showerror("Error", "Price must be a number and stock must be an integer.")
            return

        final_img_path = ""
        if self.selected_image_path:
            assets_dir = "assets"
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)
            ext = os.path.splitext(self.selected_image_path)[1]
            safe_name = name.replace(" ", "_").lower()
            final_img_path = os.path.join(assets_dir, f"item_{safe_name}{ext}")
            shutil.copy(self.selected_image_path, final_img_path)

        if self.db.add_inventory_item(name, price, stock, cat, final_img_path):
            self.db.log_action(self.username, "Added Item", f"[{cat}] {name} (Stock: {stock})")
            messagebox.showinfo("Success", f"{name} added to inventory!")
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Item already exists or database error.")

class SellItemModal(ctk.CTkToplevel):
    def __init__(self, parent, db, username, item, refresh_callback, currency='₦'):
        super().__init__(parent)
        self.title(f"Sell {item['item_name']}")
        self.geometry("400x550")
        self.db = db
        self.username = username
        self.item = item
        self.refresh_callback = refresh_callback
        self.currency = currency
        
        self.attributes("-topmost", True)
        self.grab_set()
        
        self.bookings = self.db.get_active_bookings()
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text=f"Sell: {self.item['item_name']}", font=("Arial", 20, "bold")).pack(pady=15)
        ctk.CTkLabel(self, text=f"Price: {self.currency}{self.item['price']:,.2f} | Stock: {self.item['stock_level']}").pack(pady=5)
        
        # Quantity
        qty_frame = ctk.CTkFrame(self, fg_color="transparent")
        qty_frame.pack(pady=10)
        ctk.CTkLabel(qty_frame, text="Quantity:").pack(side="left", padx=10)
        self.qty_var = ctk.StringVar(value="1")
        self.qty_entry = ctk.CTkEntry(qty_frame, textvariable=self.qty_var, width=60)
        self.qty_entry.pack(side="left")

        # Customer Type
        self.customer_type = ctk.StringVar(value="Walk-in")
        type_frame = ctk.CTkFrame(self, fg_color="transparent")
        type_frame.pack(pady=10)
        
        ctk.CTkRadioButton(type_frame, text="Walk-in", variable=self.customer_type, value="Walk-in", command=self.on_type_change).pack(side="left", padx=10)
        ctk.CTkRadioButton(type_frame, text="Active Guest", variable=self.customer_type, value="Guest", command=self.on_type_change).pack(side="left", padx=10)

        # Walk-in or Guest Selection Area
        self.selection_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.selection_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(self.selection_frame, text="Walk-in Customer Name (Optional):").pack(pady=(10, 2))
        self.walkin_name = ctk.CTkEntry(self.selection_frame, width=250)
        self.walkin_name.pack(pady=(0, 10))

        ctk.CTkLabel(self.selection_frame, text="Select Active Guest:").pack(pady=(5, 2))
        self.guest_options = [f"{b['room_name']} - {b['customer_name']}" for b in self.bookings]
        self.guest_var = ctk.StringVar(value=self.guest_options[0] if self.guest_options else "No active guests")
        self.guest_dropdown = ctk.CTkOptionMenu(self.selection_frame, values=self.guest_options if self.guest_options else ["None"], variable=self.guest_var, width=250)
        self.guest_dropdown.pack(pady=(0, 10))

        # Payment Option
        self.payment_var = ctk.StringVar(value="Paid")
        self.payment_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.payment_frame.pack(pady=10)
        
        ctk.CTkLabel(self.payment_frame, text="Payment Method:").pack(pady=5)
        self.paid_radio = ctk.CTkRadioButton(self.payment_frame, text="Paid (Cash/Card)", variable=self.payment_var, value="Paid")
        self.paid_radio.pack(anchor="w", pady=5)
        self.charge_radio = ctk.CTkRadioButton(self.payment_frame, text="Charge to Room", variable=self.payment_var, value="Charge to Room")
        self.charge_radio.pack(anchor="w", pady=5)

        self.on_type_change() # Init state

        ctk.CTkButton(self, text="Confirm Sale", fg_color="#2ecc71", command=self.process_sale).pack(pady=20)

    def on_type_change(self):
        if self.customer_type.get() == "Walk-in":
            self.guest_dropdown.configure(state="disabled")
            self.walkin_name.configure(state="normal")
            self.payment_var.set("Paid")
            self.charge_radio.configure(state="disabled")
        else:
            if not self.guest_options:
                self.customer_type.set("Walk-in")
                messagebox.showwarning("No Guests", "There are no active guests to charge.")
                return
            self.guest_dropdown.configure(state="normal")
            self.walkin_name.configure(state="disabled")
            self.charge_radio.configure(state="normal")

    def process_sale(self):
        try:
            qty = int(self.qty_var.get())
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer.")
            return

        if qty > self.item['stock_level']:
            messagebox.showerror("Error", "Not enough stock available.")
            return

        is_guest = self.customer_type.get() == "Guest"
        payment_status = self.payment_var.get()
        
        booking_id = None
        guest_name = "Walk-in"

        if is_guest:
            # Find selected booking
            idx = self.guest_options.index(self.guest_var.get())
            booking = self.bookings[idx]
            booking_id = booking['booking_id']
            guest_name = booking['customer_name']
        else:
            entered_name = self.walkin_name.get().strip()
            if entered_name:
                guest_name = f"Walk-in ({entered_name})"

        success = self.db.add_order(
            booking_id=booking_id,
            guest_name=guest_name,
            item_id=self.item['id'],
            item_name=self.item['item_name'],
            quantity=qty,
            price=self.item['price'],
            payment_status=payment_status
        )

        if success:
            self.db.log_action(self.username, "Inventory Sale", f"Sold {qty}x {self.item['item_name']} to {guest_name} ({payment_status})")
            messagebox.showinfo("Success", f"Sale recorded successfully!\nTotal: {self.currency}{qty * self.item['price']:,.2f}")
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to record sale in database.")
