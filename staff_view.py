import customtkinter as ctk
from tkinter import messagebox
from theme import theme

class StaffView(ctk.CTkFrame):
    def __init__(self, parent, db, username):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.username = username
        self.settings = self.db.get_settings()
        self.theme_color = theme.PRIMARY
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header, text="STAFF MANAGEMENT", font=theme.header_font(), text_color=self.theme_color).pack(side="left")
        ctk.CTkButton(header, text="+ Add Staff", fg_color=self.theme_color, font=theme.body_font(), command=self.open_add_modal).pack(side="right")

        # Scrollable Grid
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.load_staff()

    def load_staff(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        users = self.db.get_all_users()
        if not users:
            ctk.CTkLabel(self.grid_frame, text="No users found.", text_color=theme.TEXT_GRAY, font=theme.subheader_font()).pack(pady=50)
            return

        for user in users:
            card = ctk.CTkFrame(self.grid_frame, fg_color=theme.BG_DARK)
            card.pack(fill="x", pady=5)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=15, fill="x", expand=True)
            
            ctk.CTkLabel(info_frame, text=f"Username: {user['username']}", font=theme.card_font()).pack(side="left", padx=10)
            
            role_color = self.theme_color if str(user['role']).lower() == 'admin' else theme.SECONDARY
            ctk.CTkLabel(info_frame, text=f"ROLE: {str(user['role']).upper()}", font=theme.body_font(bold=True), text_color=role_color).pack(side="left", padx=20)
            
            # Don't allow deleting ID 1 (master admin)
            if user['id'] != 1:
                ctk.CTkButton(card, text="Delete", fg_color=theme.DANGER, width=80, font=theme.small_font(),
                              command=lambda u_id=user['id'], name=user['username']: self.delete_staff(u_id, name)).pack(side="right", padx=20, pady=15)
            else:
                ctk.CTkLabel(card, text="Master Admin", text_color=theme.TEXT_GRAY, font=theme.small_font(italic=True)).pack(side="right", padx=20, pady=15)

    def delete_staff(self, user_id, username):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the account for '{username}'?"):
            if self.db.delete_user(user_id):
                self.db.log_action(self.username, "Deleted Staff", f"Removed user: {username}")
                messagebox.showinfo("Success", f"User '{username}' deleted successfully.")
                self.load_staff()
            else:
                messagebox.showerror("Error", "Could not delete user. (Master Admin cannot be deleted).")

    def open_add_modal(self):
        AddStaffModal(self, self.db, self.username, self.load_staff)

class AddStaffModal(ctk.CTkToplevel):
    def __init__(self, parent, db, username, refresh_callback):
        super().__init__(parent)
        self.title("Add New Staff")
        self.geometry("400x450")
        self.db = db
        self.username = username
        self.refresh_callback = refresh_callback
        
        self.attributes("-topmost", True)
        self.grab_set()
        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text="New Account Details", font=theme.subheader_font()).pack(pady=20)
        
        ctk.CTkLabel(self, text="Username:", font=theme.body_font()).pack()
        self.name_entry = ctk.CTkEntry(self, width=250, font=theme.body_font())
        self.name_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Password:", font=theme.body_font()).pack()
        self.pass_entry = ctk.CTkEntry(self, width=250, show="*", font=theme.body_font())
        self.pass_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Account Role:", font=theme.body_font()).pack(pady=(10, 0))
        self.role_var = ctk.StringVar(value="staff")
        
        radio_frame = ctk.CTkFrame(self, fg_color="transparent")
        radio_frame.pack(pady=5)
        ctk.CTkRadioButton(radio_frame, text="Staff", variable=self.role_var, value="staff", font=theme.body_font()).pack(side="left", padx=10)
        ctk.CTkRadioButton(radio_frame, text="Admin", variable=self.role_var, value="admin", font=theme.body_font()).pack(side="left", padx=10)

        ctk.CTkButton(self, text="Create Account", fg_color=theme.PRIMARY, font=theme.body_font(bold=True), command=self.save).pack(pady=30)

    def save(self):
        name = self.name_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        role = self.role_var.get()

        if not name or not pwd:
            messagebox.showerror("Error", "Username and Password are required.")
            return

        if self.db.add_user(name, pwd, role):
            self.db.log_action(self.username, "Created Staff", f"Added new {role}: {name}")
            messagebox.showinfo("Success", f"Account for '{name}' created successfully!")
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Username already exists! Please choose another.")
