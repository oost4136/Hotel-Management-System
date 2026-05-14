import sys
import os
import base64
import re
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt

# Ensure the parent directory is in the path so we can import the original py files
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import LuxuryDB
from pdf_generator import PDFGenerator

# --- CONFIGURATION ---
SECRET_KEY = os.getenv("LUXURY_PMS_SECRET_KEY", "change-this-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize the existing database logic
db = LuxuryDB()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
LOGOS_DIR = ASSETS_DIR / "logos"
RECEIPTS_DIR = PROJECT_ROOT / "receipts"
LOGOS_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)

def rows_to_dicts(rows):
    return [dict(row) for row in rows]

def receipt_url_from_path(path: str) -> str:
    return f"/receipts/{Path(path).name}"

def safe_upload_filename(filename: str) -> str:
    stem = Path(filename).stem or "logo"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Logo must be a PNG, JPG, or JPEG image")
    clean_stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", stem).strip("-") or "logo"
    return f"{clean_stem}-{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"

class RoomCreate(BaseModel):
    name: str
    price: float
    caution_fee: float
    image_url: str = ""
    amenities: str = ""

class StaffCreate(BaseModel):
    username: str
    password: str
    role: str = "staff"

class SettingsUpdate(BaseModel):
    business_name: str
    primary_color: str
    secondary_color: str = "#3498db"
    font_family: str = "Arial"
    caution_fee: float
    logo_path: str = ""
    currency_symbol: str = ""

class AmenityCreate(BaseModel):
    name: str

class BookingCreate(BaseModel):
    customer_name: str
    guest_phone: str
    room_id: int
    adults: int = 1
    children: int = 0
    caution_fee: float

class ExtendStayUpdate(BaseModel):
    new_checkout_date: str

class InventoryItemCreate(BaseModel):
    item_name: str
    price: float
    stock_level: int
    category: str = "Uncategorized"
    image_path: str = ""

class StockUpdate(BaseModel):
    new_stock: int

class SaleCreate(BaseModel):
    booking_id: Optional[int] = None
    guest_name: str
    item_id: int
    item_name: str
    quantity: int
    price: float
    payment_status: str

class SupportMessage(BaseModel):
    message: str

class ImageUpload(BaseModel):
    filename: str
    data_url: str

# --- SECURITY ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- APP ---
app = FastAPI(title="Luxury PMS API")
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/receipts", StaticFiles(directory=str(RECEIPTS_DIR)), name="receipts")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Use existing database logic to find user
    users = db.get_all_users()
    user = next((u for u in users if u["username"] == username), None)
    if user is None:
        raise credentials_exception
    return user

# --- AUTH ENDPOINTS ---
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Use existing verify_login logic from database.py
    role_data = db.verify_login(form_data.username, form_data.password)
    
    if not role_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract role correctly from Row/dict
    role = role_data["role"] if hasattr(role_data, "__getitem__") else role_data
    access_token = create_access_token(data={"sub": form_data.username, "role": role})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/public/settings")
def read_public_settings():
    settings = db.get_settings()
    return {
        "business_name": settings.get("business_name", ""),
        "logo_path": settings.get("logo_path", ""),
    }

@app.get("/settings")
def read_settings(current_user: dict = Depends(get_current_user)):
    return db.get_settings()

@app.put("/settings")
def update_settings(data: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update settings")
    if not db.save_settings(data.model_dump()):
        raise HTTPException(status_code=400, detail="Could not save settings")
    db.log_action(current_user["username"], "Updated Settings", data.business_name)
    return db.get_settings()

@app.post("/uploads/image")
def upload_image(payload: ImageUpload, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload images")
    if "," not in payload.data_url:
        raise HTTPException(status_code=400, detail="Invalid image data")

    header, encoded = payload.data_url.split(",", 1)
    if not header.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Logo must be an image")

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data")

    filename = safe_upload_filename(payload.filename)
    file_path = ASSETS_DIR / filename
    file_path.write_bytes(image_bytes)
    return {"image_path": str(file_path), "image_url": f"/assets/{filename}"}

@app.post("/uploads/logo")
def upload_logo(payload: ImageUpload, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload logos")
    if "," not in payload.data_url:
        raise HTTPException(status_code=400, detail="Invalid image data")

    header, encoded = payload.data_url.split(",", 1)
    if not header.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Logo must be an image")

    try:
        image_bytes = base64.b64decode(encoded, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data")

    if len(image_bytes) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Logo image must be 2MB or smaller")

    filename = safe_upload_filename(payload.filename)
    file_path = LOGOS_DIR / filename
    file_path.write_bytes(image_bytes)
    db.log_action(current_user["username"], "Uploaded Logo", filename)
    return {"logo_path": str(file_path), "logo_url": f"/assets/logos/{filename}"}

# --- ROOM ENDPOINTS ---
@app.get("/rooms")
def read_rooms(current_user: dict = Depends(get_current_user)):
    return rows_to_dicts(db.get_all_rooms())

@app.post("/rooms")
def create_room(room: RoomCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create rooms")
    if not db.register_new_room(room.name, room.price, room.caution_fee, room.image_url, room.amenities):
        raise HTTPException(status_code=400, detail="Could not create room")
    db.log_action(current_user["username"], "Created Room", room.name)
    return {"ok": True}

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete rooms")
    if not db.delete_room(room_id):
        raise HTTPException(status_code=400, detail="Could not delete room")
    db.log_action(current_user["username"], "Deleted Room", str(room_id))
    return {"ok": True}

@app.get("/amenities")
def read_amenities(current_user: dict = Depends(get_current_user)):
    return db.get_all_amenities()

@app.post("/amenities")
def create_amenity(amenity: AmenityCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage amenities")
    if not db.add_amenity(amenity.name):
        raise HTTPException(status_code=400, detail="Amenity already exists")
    db.log_action(current_user["username"], "Created Amenity", amenity.name)
    return db.get_all_amenities()

@app.delete("/amenities/{name}")
def delete_amenity(name: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage amenities")
    if not db.delete_amenity(name):
        raise HTTPException(status_code=400, detail="Could not delete amenity")
    db.log_action(current_user["username"], "Deleted Amenity", name)
    return db.get_all_amenities()

# --- STAFF ENDPOINTS ---
@app.get("/staff")
def read_staff(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage staff")
    return db.get_all_users()

@app.post("/staff")
def create_staff(staff: StaffCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage staff")
    if not db.add_user(staff.username, staff.password, staff.role):
        raise HTTPException(status_code=400, detail="Username already exists")
    db.log_action(current_user["username"], "Created Staff", f"Added new {staff.role}: {staff.username}")
    return db.get_all_users()

@app.delete("/staff/{user_id}")
def delete_staff(user_id: int, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can manage staff")
    if not db.delete_user(user_id):
        raise HTTPException(status_code=400, detail="Could not delete user")
    db.log_action(current_user["username"], "Deleted Staff", f"Removed user id: {user_id}")
    return db.get_all_users()

@app.get("/bookings/recent")
def read_recent_bookings(current_user: dict = Depends(get_current_user)):
    rows = db.execute_query("""
        SELECT b.id, b.customer_name, b.status, b.caution_fee, b.check_in,
               r.name as room_name, r.price as room_price
        FROM bookings b
        LEFT JOIN rooms r ON b.room_id = r.id
        ORDER BY b.id DESC
        LIMIT 10
    """)
    return rows_to_dicts(rows)

@app.get("/activity-logs/recent")
def read_recent_activity_logs(current_user: dict = Depends(get_current_user)):
    return db.get_logs()[:10]

@app.get("/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    # Calculate real stats from the existing database
    rooms = db.get_all_rooms()
    active_bookings = db.get_active_bookings()
    
    available_rooms = [r for r in rooms if r["is_available"]]
    
    return {
        "total_rooms": len(rooms),
        "active_guests": len(active_bookings),
        "available_rooms": len(available_rooms),
        "total_bookings": len(db.execute_query("SELECT id FROM bookings")) # Direct query for total historical
    }

# --- INVENTORY ENDPOINTS ---
@app.get("/inventory")
def read_inventory(current_user: dict = Depends(get_current_user)):
    return db.get_inventory()

@app.post("/inventory")
def create_inventory_item(item: InventoryItemCreate, current_user: dict = Depends(get_current_user)):
    if not db.add_inventory_item(item.item_name, item.price, item.stock_level, item.category, item.image_path):
        raise HTTPException(status_code=400, detail="Item already exists or database error")
    db.log_action(current_user["username"], "Added Item", f"[{item.category}] {item.item_name}")
    return {"ok": True}

@app.put("/inventory/{item_id}/stock")
def update_inventory_stock(item_id: int, data: StockUpdate, current_user: dict = Depends(get_current_user)):
    db.update_stock(item_id, data.new_stock)
    return {"ok": True}

@app.post("/inventory/sell")
def sell_inventory_item(sale: SaleCreate, current_user: dict = Depends(get_current_user)):
    if not db.add_order(
        sale.booking_id, sale.guest_name, sale.item_id, sale.item_name,
        sale.quantity, sale.price, sale.payment_status
    ):
        raise HTTPException(status_code=400, detail="Could not record sale")
    db.log_action(current_user["username"], "Inventory Sale", f"Sold {sale.quantity}x {sale.item_name} to {sale.guest_name}")
    return {"ok": True}

# --- BOOKING ENDPOINTS ---
@app.get("/rooms/available")
def read_available_rooms(current_user: dict = Depends(get_current_user)):
    return rows_to_dicts(db.get_available_rooms())

@app.post("/bookings")
def create_booking(booking: BookingCreate, current_user: dict = Depends(get_current_user)):
    if not db.create_booking(
        booking.customer_name, booking.guest_phone, booking.room_id,
        booking.adults, booking.children, booking.caution_fee
    ):
        raise HTTPException(status_code=400, detail="Could not create booking")
    db.log_action(current_user["username"], "Guest Check-In", f"{booking.customer_name} into room {booking.room_id}")
    return {"ok": True}

@app.get("/bookings/active")
def read_active_bookings(current_user: dict = Depends(get_current_user)):
    return db.get_active_bookings()

@app.put("/bookings/{booking_id}/extend")
def extend_stay(booking_id: int, data: ExtendStayUpdate, current_user: dict = Depends(get_current_user)):
    if not db.extend_stay(booking_id, data.new_checkout_date):
        raise HTTPException(status_code=400, detail="Could not extend stay")
    db.log_action(current_user["username"], "Extend Stay", f"Booking ID: {booking_id} to {data.new_checkout_date}")
    return {"ok": True}

@app.post("/bookings/{booking_id}/checkout")
def complete_checkout(booking_id: int, room_id: int, current_user: dict = Depends(get_current_user)):
    booking = next((item for item in db.get_active_bookings() if item["booking_id"] == booking_id), None)
    if booking is None:
        raise HTTPException(status_code=404, detail="Active booking not found")

    check_in = booking.get("check_in", "")
    try:
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d %H:%M:%S")
        days_stayed = max(1, (datetime.now() - check_in_dt).days)
    except Exception:
        days_stayed = 1

    unpaid_orders = db.get_unpaid_orders_for_booking(booking_id)
    inventory_total = sum(float(order.get("total", 0) or 0) for order in unpaid_orders)
    room_total = float(booking.get("room_price", 0) or 0) * days_stayed
    receipt_data = {
        "settings": db.get_settings(),
        "guest_name": booking.get("customer_name", "Guest"),
        "room_name": booking.get("room_name", "Room"),
        "check_in": check_in,
        "days_stayed": days_stayed,
        "rate": float(booking.get("room_price", 0) or 0),
        "caution_fee": float(booking.get("caution_fee", 0) or 0),
        "inventory_orders": unpaid_orders,
        "inventory_total": inventory_total,
        "grand_total": room_total + inventory_total,
    }

    try:
        receipt_path = PDFGenerator().create_hotel_receipt(receipt_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not generate receipt: {exc}")

    if not db.complete_checkout(booking_id, room_id):
        raise HTTPException(status_code=400, detail="Could not complete checkout")
    db.log_action(current_user["username"], "Guest Checkout", f"Booking ID: {booking_id}")
    return {"ok": True, "receipt_url": receipt_url_from_path(receipt_path)}

# --- SUPPORT ENDPOINTS ---
@app.post("/support")
def send_support_message(msg: SupportMessage, current_user: dict = Depends(get_current_user)):
    db.log_action(current_user["username"], "Support Request", f"Message: {msg.message}")
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "Luxury PMS API connected to legacy core."}
