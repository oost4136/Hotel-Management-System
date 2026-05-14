import customtkinter as ctk
import tkinter.messagebox as messagebox
from theme import theme

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_login_success):
        super().__init__(parent)
        self.db = db
        self.on_success = on_login_success
        
        # Load theme from current settings immediately
        settings = self.db.get_settings()
        theme.load_from_settings(settings)
        
        # UI Elements
        self.logo_label = ctk.CTkLabel(self, text=settings.get('business_name', 'LUXURY PMS').upper(), 
                                       font=theme.header_font(), text_color=theme.PRIMARY)
        self.logo_label.pack(pady=(100, 20))

        self.username = ctk.CTkEntry(self, placeholder_text="Username", width=250, height=45, font=theme.body_font())
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250, height=45, font=theme.body_font())
        self.password.pack(pady=10)

        self.login_btn = ctk.CTkButton(self, text="Login", width=250, height=45, font=theme.body_font(bold=True),
                                       fg_color=theme.PRIMARY, command=self.attempt_login)
        self.login_btn.pack(pady=30)

    def attempt_login(self):
        user = self.username.get()
        pw = self.password.get()
        
        role = self.db.verify_login(user, pw)
        
        if role:
            # Trigger the success function passed from main.py
            self.on_success(user, role)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
