import customtkinter as ctk
from tkinter import messagebox

class CheckInView(ctk.CTkFrame):
    def __init__(self, parent, db, reload_callback=None):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.reload_callback = reload_callback
        
        self.settings = self.db.get_settings()
        self.theme_color = self.settings.get('primary_color', '#2ecc71')
        self.currency = self.settings.get('currency_symbol', '₦')
        
        self.available_rooms = self.db.get_available_rooms()
        self.selected_room = None
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        ctk.CTkLabel(self, text="GUEST CHECK-IN", font=("Arial", 24, "bold"), text_color=self.theme_color).pack(pady=20)
        
        if not self.available_rooms:
            ctk.CTkLabel(self, text="No rooms are currently available.", font=("Arial", 16), text_color="red").pack(pady=20)
            return

        form_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", width=500)
        form_frame.pack(pady=10, padx=20)

        # Room Selection
        ctk.CTkLabel(form_frame, text="Select Room:", font=("Arial", 14)).pack(pady=(20, 5))
        room_options = [f"{r['name']} - {self.currency}{r['price']:,.2f}/night" for r in self.available_rooms]
        self.room_var = ctk.StringVar(value=room_options[0])
        self.room_dropdown = ctk.CTkOptionMenu(form_frame, values=room_options, variable=self.room_var, command=self.update_caution_fee, width=300)
        self.room_dropdown.pack(pady=5)

        # Guest Name
        ctk.CTkLabel(form_frame, text="Guest Name:", font=("Arial", 14)).pack(pady=(15, 5))
        self.name_entry = ctk.CTkEntry(form_frame, width=300)
        self.name_entry.pack(pady=5)

        # Guest Phone
        ctk.CTkLabel(form_frame, text="Phone Number:", font=("Arial", 14)).pack(pady=(15, 5))
        self.phone_entry = ctk.CTkEntry(form_frame, width=300)
        self.phone_entry.pack(pady=5)

        # Occupants
        occ_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        occ_frame.pack(pady=15)
        
        ctk.CTkLabel(occ_frame, text="Adults:", font=("Arial", 12)).pack(side="left", padx=5)
        self.adults_entry = ctk.CTkEntry(occ_frame, width=60)
        self.adults_entry.insert(0, "1")
        self.adults_entry.pack(side="left", padx=5)

        ctk.CTkLabel(occ_frame, text="Children:", font=("Arial", 12)).pack(side="left", padx=5)
        self.children_entry = ctk.CTkEntry(occ_frame, width=60)
        self.children_entry.insert(0, "0")
        self.children_entry.pack(side="left", padx=5)

        # Caution Fee (Auto-filled from room)
        ctk.CTkLabel(form_frame, text="Caution Fee Required:", font=("Arial", 14)).pack(pady=(15, 5))
        self.caution_entry = ctk.CTkEntry(form_frame, width=300)
        self.caution_entry.pack(pady=5)

        # Init caution fee
        self.update_caution_fee(self.room_var.get())

        # Submit Button
        ctk.CTkButton(self, text="COMPLETE CHECK-IN", fg_color=self.theme_color, height=50, width=300, command=self.process_checkin).pack(pady=30)

    def update_caution_fee(self, selection):
        idx = self.room_dropdown._values.index(selection)
        room = self.available_rooms[idx]
        self.selected_room = room
        self.caution_entry.delete(0, 'end')
        self.caution_entry.insert(0, str(room['caution_fee']))

    def process_checkin(self):
        name = self.name_entry.get().strip()
        phone = self.phone_entry.get().strip()
        adults_str = self.adults_entry.get().strip()
        children_str = self.children_entry.get().strip()
        caution_str = self.caution_entry.get().strip()

        if not name or not phone or not adults_str or not caution_str:
            messagebox.showerror("Error", "Please fill all required fields.")
            return

        try:
            adults = int(adults_str)
            children = int(children_str) if children_str else 0
            caution = float(caution_str)
        except ValueError:
            messagebox.showerror("Error", "Adults, Children, and Caution Fee must be numbers.")
            return

        room_id = self.selected_room['id']

        if self.db.create_booking(name, phone, room_id, adults, children, caution):
            messagebox.showinfo("Success", f"{name} successfully checked into {self.selected_room['name']}!")
            if self.reload_callback:
                self.reload_callback() # Reload to clear form or switch views
        else:
            messagebox.showerror("Error", "Failed to process check-in.")
