import customtkinter as ctk

class HomeView(ctk.CTkFrame):
    def __init__(self, master, db, app, current_user, current_role, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.app = app
        self.current_user = current_user
        self.current_role = current_role
        
        self.settings = self.db.get_settings()
        self.theme_color = self.settings.get('primary_color', '#2ecc71')

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkLabel(self, text=f"Welcome back, {self.current_user}!", font=("Arial", 28, "bold"))
        header.pack(pady=(20, 10), anchor="w", padx=30)
        
        sub_header = ctk.CTkLabel(self, text="What would you like to do today? Select an option below.", font=("Arial", 16), text_color="gray")
        sub_header.pack(pady=(0, 30), anchor="w", padx=30)

        # Quick Actions Grid
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=30)

        grid_frame.columnconfigure((0, 1), weight=1)

        # Action Cards
        self.create_action_card(grid_frame, "Rooms & Apartments", "View and manage all rooms", self.app.show_rooms, 0, 0)
        self.create_action_card(grid_frame, "Check-In Guest", "Register a new guest", self.app.show_checkin, 0, 1)
        self.create_action_card(grid_frame, "Active Guests", "View currently checked-in guests", self.app.show_active_guests, 1, 0)
        self.create_action_card(grid_frame, "Live Inventory", "Manage hotel items and stock", self.app.show_inventory, 1, 1)

        if str(self.current_role).lower() == 'admin':
            self.create_action_card(grid_frame, "System Settings", "Configure application settings", self.app.show_settings, 2, 0)
            self.create_action_card(grid_frame, "Staff Management", "Manage system users", self.app.show_staff, 2, 1)

    def create_action_card(self, parent, title, description, command, row, col):
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=10)
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        btn = ctk.CTkButton(card, text=title, font=("Arial", 18, "bold"), 
                            fg_color=self.theme_color, hover_color="#1e8449", text_color="white",
                            height=50, command=command)
        btn.pack(pady=(20, 5), padx=20, fill="x")
        
        desc = ctk.CTkLabel(card, text=description, font=("Arial", 12), text_color="gray")
        desc.pack(pady=(0, 20), padx=20)
