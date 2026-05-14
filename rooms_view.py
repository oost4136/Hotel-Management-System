import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import shutil
from PIL import Image

class RoomsView(ctk.CTkFrame):
    def __init__(self, parent, db, role):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.role = role
        self.currency = self.db.get_settings().get('currency_symbol', '₦')
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header, text="ROOMS & APARTMENTS", font=("Arial", 24, "bold")).pack(side="left")
        
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.pack(side="left", padx=20)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.load_rooms())
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search rooms...", textvariable=self.search_var, width=200)
        self.search_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(search_frame, text="Search", width=60, fg_color="#2ecc71", command=self.load_rooms).pack(side="left")

        if self.role == 'admin':
            ctk.CTkButton(header, text="+ Add New Room", fg_color="#2ecc71", 
                          command=self.open_add_modal).pack(side="right")

        # Scrollable Grid
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.load_rooms()

    def load_rooms(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        rooms = self.db.get_all_rooms()
        
        if hasattr(self, 'search_var'):
            query = self.search_var.get().strip().lower()
            if query:
                rooms = [room for room in rooms if query in str(room['name'] or '').lower() or query in str(room['amenities'] or '').lower()]

        if not rooms:
            ctk.CTkLabel(self.grid_frame, text="No rooms found. Add one to get started!", text_color="gray").pack(pady=50)
            return

        for idx, room in enumerate(rooms):
            card = ctk.CTkFrame(self.grid_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5)
            
            # Image Section
            img_path = room['image_url'] if room['image_url'] else ''
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

            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=10)

            info = f"{room['name']} - {self.currency}{room['price']:,.2f}/night"
            ctk.CTkLabel(info_frame, text=info, font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=(5,0))
            
            if room['is_available']:
                status_text = "Available"
                status_color = "#2ecc71"
            else:
                status_text = "Checked-In (Unavailable)"
                status_color = "#e74c3c"
                
            ctk.CTkLabel(info_frame, text=status_text, text_color=status_color, font=("Arial", 12, "bold")).pack(anchor="w", padx=15, pady=2)
            
            if room['amenities']:
                am_label = ctk.CTkLabel(info_frame, text=f"Amenities: {room['amenities']}", text_color="gray")
                am_label.pack(anchor="w", padx=15)
            
            if self.role == 'admin':
                ctk.CTkButton(card, text="Delete", fg_color="#e74c3c", width=60,
                              command=lambda r=room: self.delete_room(r['id'], r['name'])).pack(side="right", padx=15)

    def delete_room(self, room_id, name):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {name}?"):
            if self.db.delete_room(room_id):
                self.load_rooms()
            else:
                messagebox.showerror("Error", "Could not delete room.")

    def open_add_modal(self):
        AddRoomModal(self, self.db, self.load_rooms)


class AddRoomModal(ctk.CTkToplevel):
    def __init__(self, parent, db, refresh_callback):
        super().__init__(parent)
        self.title("Add New Room")
        self.geometry("500x700")
        self.db = db
        self.refresh_callback = refresh_callback
        
        # Keep modal on top
        self.attributes("-topmost", True)
        self.grab_set()

        self.image_path = ""
        self.setup_ui()

    def setup_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(expand=True, fill="both", padx=20, pady=20)

        ctk.CTkLabel(self.scroll, text="New Room Details", font=("Arial", 20, "bold")).pack(pady=10)

        self.name = ctk.CTkEntry(self.scroll, placeholder_text="Room Name (e.g. Presidential Suite)", width=400)
        self.name.pack(pady=10)

        self.price = ctk.CTkEntry(self.scroll, placeholder_text="Price per Night (e.g. 75000)", width=400)
        self.price.pack(pady=10)

        self.caution = ctk.CTkEntry(self.scroll, placeholder_text="Caution Fee (e.g. 50000)", width=400)
        self.caution.pack(pady=10)

        # Image picker
        img_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        img_frame.pack(pady=10)
        ctk.CTkButton(img_frame, text="Pick Image", command=self.pick_image).pack(side="left", padx=5)
        self.img_label = ctk.CTkLabel(img_frame, text="No image selected")
        self.img_label.pack(side="left", padx=5)

        # Amenities
        ctk.CTkLabel(self.scroll, text="Select Amenities:", font=("Arial", 16, "bold")).pack(pady=(20, 5), anchor="w")
        
        self.checkboxes = {}
        all_amenities = self.db.get_all_amenities()
        for amenity in all_amenities:
            var = ctk.StringVar(value="off")
            cb = ctk.CTkCheckBox(self.scroll, text=amenity, variable=var, onvalue=amenity, offvalue="off")
            cb.pack(anchor="w", pady=2, padx=10)
            self.checkboxes[amenity] = var

        ctk.CTkButton(self.scroll, text="Save Room", fg_color="#2ecc71", height=40, command=self.save).pack(pady=30)

    def pick_image(self):
        # We need to temporarily release grab so filedialog can be interacted with smoothly on some OS
        self.grab_release()
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        self.grab_set()
        
        if file_path:
            if not os.path.exists("assets"):
                os.makedirs("assets")
            
            # Use unique filename to prevent collisions (Upload instead of just copy)
            ext = os.path.splitext(file_path)[1]
            unique_name = f"room_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
            new_path = os.path.join("assets", unique_name)
            
            try:
                shutil.copy(file_path, new_path)
                self.image_path = new_path
                self.img_label.configure(text=unique_name)
            except Exception as e:
                messagebox.showerror("Upload Error", f"Could not upload image: {e}")

    def save(self):
        name = self.name.get().strip()
        price_str = self.price.get().strip()
        caution_str = self.caution.get().strip()

        if not name or not price_str or not caution_str:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        try:
            price = float(price_str)
            caution = float(caution_str)
        except ValueError:
            messagebox.showerror("Error", "Price and Caution Fee must be numbers.")
            return

        # Gather selected amenities
        selected_amenities = []
        for am, var in self.checkboxes.items():
            if var.get() != "off":
                selected_amenities.append(am)
        
        amenities_str = ", ".join(selected_amenities)

        if self.db.register_new_room(name, price, caution, self.image_path, amenities_str):
            messagebox.showinfo("Success", "Room saved successfully!")
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Could not save room to database.")
