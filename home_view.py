import customtkinter as ctk
from PIL import Image
import os
from theme import theme

class HomeView(ctk.CTkFrame):
    def __init__(self, master, db, app, current_user, current_role, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.app = app
        self.current_user = current_user
        self.current_role = current_role
        
        self.settings = self.db.get_settings()
        self.theme_color = theme.PRIMARY
        
        self.setup_ui()

    def setup_ui(self):
        # Welcome Header
        welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        welcome_frame.pack(fill="x", pady=(20, 40), padx=40)
        
        welcome_text = f"Welcome, {self.current_user}!"
        ctk.CTkLabel(welcome_frame, text=welcome_text, font=theme.header_font(), text_color=self.theme_color).pack(side="left")
        
        # Dashboard Grid
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(expand=True, fill="both", padx=40)
        grid_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Quick Stats / Actions
        self.create_action_card(grid_frame, "Check-In", "Register a new guest", self.app.show_checkin, 0, 0)
        self.create_action_card(grid_frame, "Rooms", "View room availability", self.app.show_rooms, 0, 1)
        self.create_action_card(grid_frame, "Active Guests", "Manage checked-in guests", self.app.show_active_guests, 0, 2)
        
        self.create_action_card(grid_frame, "Inventory", "Bar & kitchen stock", self.app.show_inventory, 1, 0)
        
        if str(self.current_role).lower() == 'admin':
            self.create_action_card(grid_frame, "Staff Management", "Manage system users", self.app.show_staff, 1, 1)
            self.create_action_card(grid_frame, "Settings", "Configure system", self.app.show_settings, 1, 2)

    def create_action_card(self, master, title, subtitle, command, row, col):
        card = ctk.CTkFrame(master, fg_color=theme.BG_DARK, corner_radius=15, height=150)
        card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        card.grid_propagate(False)
        
        ctk.CTkLabel(card, text=title, font=theme.subheader_font(), text_color=self.theme_color).pack(pady=(25, 5))
        ctk.CTkLabel(card, text=subtitle, font=theme.small_font(), text_color=theme.TEXT_GRAY).pack()
        
        btn = ctk.CTkButton(card, text="Open", fg_color="transparent", border_width=1, border_color=self.theme_color, 
                            hover_color=self.theme_color, font=theme.body_font(), command=command)
        btn.pack(side="bottom", pady=20)
