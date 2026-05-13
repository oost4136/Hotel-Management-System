import customtkinter as ctk
import tkinter.messagebox as messagebox

class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, db, on_login_success):
        super().__init__(parent)
        self.db = db
        self.on_success = on_login_success
        
        # UI Elements
        self.logo_label = ctk.CTkLabel(self, text="LUXURY PMS", font=("Arial", 28, "bold"), text_color="#2fa572")
        self.logo_label.pack(pady=(50, 20))

        self.username = ctk.CTkEntry(self, placeholder_text="Username", width=250, height=40)
        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250, height=40)
        self.password.pack(pady=10)

        self.login_btn = ctk.CTkButton(self, text="Login", width=250, height=40, 
                                       fg_color="#2fa572", command=self.attempt_login)
        self.login_btn.pack(pady=20)

    def attempt_login(self):
        user = self.username.get()
        pw = self.password.get()
        
        role = self.db.verify_login(user, pw)
        
        if role:
            # Trigger the success function passed from main.py
            self.on_success(user, role)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password")
