import customtkinter as ctk
from tkinter import messagebox, filedialog
from tkinter.colorchooser import askcolor
import os
import shutil
from datetime import datetime
from theme import theme

class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, db, refresh_callback):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.refresh_callback = refresh_callback
        
        self.current_settings = self.db.get_settings()
        self.selected_color = self.current_settings.get('primary_color', '#2ecc71')
        self.secondary_color = self.current_settings.get('secondary_color', '#3498db')
        self.font_family = self.current_settings.get('font_family', 'Arial')
        self.logo_path = self.current_settings.get('logo_path', '')
        self.currency_symbol = self.current_settings.get('currency_symbol', '₦')

        self.setup_ui()

    def setup_ui(self):
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(expand=True, fill="both")

        ctk.CTkLabel(self.scroll_frame, text="SYSTEM SETTINGS", font=theme.header_font(), text_color=self.selected_color).pack(pady=20)

        # Basic Info
        basic_frame = ctk.CTkFrame(self.scroll_frame, fg_color=theme.BG_DARK)
        basic_frame.pack(pady=10, padx=20, fill="x")

        ctk.CTkLabel(basic_frame, text="Hotel Name:", font=theme.body_font()).pack(pady=(15,5))
        self.name_entry = ctk.CTkEntry(basic_frame, width=400, height=40, font=theme.body_font())
        self.name_entry.pack(pady=5)
        self.name_entry.insert(0, self.current_settings.get('business_name', ''))

        ctk.CTkLabel(basic_frame, text="Default Caution Fee:", font=theme.body_font()).pack(pady=(15,5))
        self.caution_entry = ctk.CTkEntry(basic_frame, width=400, height=40, font=theme.body_font())
        self.caution_entry.pack(pady=5)
        self.caution_entry.insert(0, str(self.current_settings.get('caution_fee', 50000)))

        ctk.CTkLabel(basic_frame, text="Currency Symbol (e.g. ₦, $, €, £):", font=theme.body_font()).pack(pady=(15,5))
        self.currency_entry = ctk.CTkEntry(basic_frame, width=400, height=40, font=theme.body_font())
        self.currency_entry.pack(pady=(0, 20))
        self.currency_entry.insert(0, self.currency_symbol)

        # Logo Section
        logo_frame = ctk.CTkFrame(self.scroll_frame, fg_color=theme.BG_DARK)
        logo_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(logo_frame, text="Hotel Logo:", font=theme.body_font()).pack(pady=(15,5))
        
        row1 = ctk.CTkFrame(logo_frame, fg_color="transparent")
        row1.pack(pady=5)
        ctk.CTkButton(row1, text="Browse Image", font=theme.small_font(), command=self.upload_logo).pack(side="left", padx=5)
        
        status_text = os.path.basename(self.logo_path) if self.logo_path else "No logo selected"
        self.logo_label = ctk.CTkLabel(row1, text=status_text, font=theme.small_font())
        self.logo_label.pack(side="left", padx=10)

        # Theme Section
        theme_frame = ctk.CTkFrame(self.scroll_frame, fg_color=theme.BG_DARK)
        theme_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(theme_frame, text="Theme Customization:", font=theme.subheader_font()).pack(pady=(15,10))
        
        # Colors
        color_grid = ctk.CTkFrame(theme_frame, fg_color="transparent")
        color_grid.pack(pady=5)

        # Primary
        ctk.CTkLabel(color_grid, text="Primary Color:", font=theme.body_font()).grid(row=0, column=0, padx=10, pady=5)
        self.prim_btn = ctk.CTkButton(color_grid, text="", fg_color=self.selected_color, width=30, height=30, command=self.pick_primary)
        self.prim_btn.grid(row=0, column=1, padx=10, pady=5)

        # Secondary
        ctk.CTkLabel(color_grid, text="Secondary Color:", font=theme.body_font()).grid(row=1, column=0, padx=10, pady=5)
        self.sec_btn = ctk.CTkButton(color_grid, text="", fg_color=self.secondary_color, width=30, height=30, command=self.pick_secondary)
        self.sec_btn.grid(row=1, column=1, padx=10, pady=5)

        # Font
        ctk.CTkLabel(theme_frame, text="System Font Family:", font=theme.body_font()).pack(pady=(10, 0))
        fonts = ["Arial", "Helvetica", "Verdana", "Tahoma", "Times New Roman", "Courier New"]
        self.font_var = ctk.StringVar(value=self.font_family)
        self.font_menu = ctk.CTkOptionMenu(theme_frame, values=fonts, variable=self.font_var, font=theme.body_font())
        self.font_menu.pack(pady=10)

        # Amenities
        amenity_frame = ctk.CTkFrame(self.scroll_frame, fg_color=theme.BG_DARK)
        amenity_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(amenity_frame, text="Manage Amenities & Facilities", font=theme.subheader_font()).pack(pady=(15,5))
        
        add_row = ctk.CTkFrame(amenity_frame, fg_color="transparent")
        add_row.pack(pady=5)
        self.new_amenity_entry = ctk.CTkEntry(add_row, placeholder_text="New Amenity Name", width=200, font=theme.body_font())
        self.new_amenity_entry.pack(side="left", padx=5)
        ctk.CTkButton(add_row, text="Add", width=80, fg_color=self.selected_color, font=theme.body_font(), command=self.add_amenity).pack(side="left", padx=5)

        self.amenities_list_frame = ctk.CTkFrame(amenity_frame, fg_color="transparent")
        self.amenities_list_frame.pack(pady=10, fill="x", padx=20)
        self.load_amenities()

        # --- Backup & Restore ---
        backup_frame = ctk.CTkFrame(self.scroll_frame, fg_color=theme.BG_DARK)
        backup_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(backup_frame, text="Backup & Restore", font=theme.subheader_font()).pack(pady=(15, 5))
        ctk.CTkLabel(backup_frame, text="Save a copy of your database to a safe location.",
                     text_color=theme.TEXT_GRAY, font=theme.small_font(), wraplength=450).pack(pady=(0, 10))

        btn_row = ctk.CTkFrame(backup_frame, fg_color="transparent")
        btn_row.pack(pady=(0, 15))
        ctk.CTkButton(btn_row, text="💾  Backup Now", fg_color=theme.SECONDARY, width=150, font=theme.small_font(),
                      command=self.backup_database).pack(side="left", padx=10)
        ctk.CTkButton(btn_row, text="♻️  Restore Backup", fg_color="#7d3c98", width=150, font=theme.small_font(),
                      command=self.restore_database).pack(side="left", padx=10)

        ctk.CTkButton(self.scroll_frame, text="SAVE ALL CHANGES", fg_color=self.selected_color, 
                      height=50, width=300, font=theme.body_font(bold=True), command=self.save_settings).pack(pady=30)

    def load_amenities(self):
        for widget in self.amenities_list_frame.winfo_children():
            widget.destroy()
        amenities = self.db.get_all_amenities()
        for idx, amenity in enumerate(amenities):
            row = ctk.CTkFrame(self.amenities_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=amenity, anchor="w", font=theme.body_font()).pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="X", width=30, fg_color=theme.DANGER, command=lambda a=amenity: self.delete_amenity(a)).pack(side="right")

    def add_amenity(self):
        name = self.new_amenity_entry.get().strip()
        if name:
            if self.db.add_amenity(name):
                self.new_amenity_entry.delete(0, 'end')
                self.load_amenities()
            else:
                messagebox.showerror("Error", "Amenity already exists!")

    def delete_amenity(self, name):
        if messagebox.askyesno("Confirm", f"Delete amenity '{name}'?"):
            self.db.delete_amenity(name)
            self.load_amenities()

    def upload_logo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            if not os.path.exists("assets"):
                os.makedirs("assets")
            filename = os.path.basename(file_path)
            new_path = os.path.join("assets", filename)
            shutil.copy(file_path, new_path)
            self.logo_path = new_path
            self.logo_label.configure(text=filename)

    def pick_primary(self):
        c = askcolor(color=self.selected_color)
        if c and c[1]:
            self.selected_color = c[1]
            self.prim_btn.configure(fg_color=c[1])

    def pick_secondary(self):
        c = askcolor(color=self.secondary_color)
        if c and c[1]:
            self.secondary_color = c[1]
            self.sec_btn.configure(fg_color=c[1])

    def save_settings(self):
        try:
            cf = float(self.caution_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Caution fee must be a number.")
            return

        data = {
            'business_name': self.name_entry.get(),
            'primary_color': self.selected_color,
            'secondary_color': self.secondary_color,
            'font_family': self.font_var.get(),
            'caution_fee': cf,
            'logo_path': self.logo_path,
            'currency_symbol': self.currency_entry.get().strip() or '₦'
        }
        
        if self.db.save_settings(data):
            messagebox.showinfo("Success", "Settings Updated! Theme will refresh.")
            self.refresh_callback()

    def backup_database(self):
        dest_dir = filedialog.askdirectory(title="Choose Backup Destination Folder")
        if not dest_dir:
            return
        src = self.db.db_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(dest_dir, f"hotel_backup_{timestamp}.db")
        try:
            shutil.copy2(src, dest)
            messagebox.showinfo("Backup Successful", f"Database backed up to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Could not create backup:\n{e}")

    def restore_database(self):
        src = filedialog.askopenfilename(
            title="Select Backup File to Restore",
            filetypes=[("Database Files", "*.db")]
        )
        if not src:
            return
        confirm = messagebox.askyesno(
            "Confirm Restore",
            "WARNING: This will overwrite your current data with the backup.\n\nAre you absolutely sure?"
        )
        if confirm:
            try:
                shutil.copy2(src, self.db.db_path)
                messagebox.showinfo("Restore Successful", "Database restored! Please restart the application.")
            except Exception as e:
                messagebox.showerror("Restore Failed", f"Could not restore backup:\n{e}")

    def load_amenities(self):
        for widget in self.amenities_list_frame.winfo_children():
            widget.destroy()
        amenities = self.db.get_all_amenities()
        for idx, amenity in enumerate(amenities):
            row = ctk.CTkFrame(self.amenities_list_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=amenity, anchor="w").pack(side="left", fill="x", expand=True)
            ctk.CTkButton(row, text="X", width=30, fg_color="#e74c3c", command=lambda a=amenity: self.delete_amenity(a)).pack(side="right")

    def add_amenity(self):
        name = self.new_amenity_entry.get().strip()
        if name:
            if self.db.add_amenity(name):
                self.new_amenity_entry.delete(0, 'end')
                self.load_amenities()
            else:
                messagebox.showerror("Error", "Amenity already exists!")

    def delete_amenity(self, name):
        if messagebox.askyesno("Confirm", f"Delete amenity '{name}'?"):
            self.db.delete_amenity(name)
            self.load_amenities()

    def upload_logo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if file_path:
            if not os.path.exists("assets"):
                os.makedirs("assets")
            filename = os.path.basename(file_path)
            new_path = os.path.join("assets", filename)
            shutil.copy(file_path, new_path)
            self.logo_path = new_path
            self.logo_label.configure(text=filename)

    def set_color(self, hex_code):
        self.selected_color = hex_code
        messagebox.showinfo("Theme", f"Color picked ({hex_code})! Remember to click Save All Changes.")

    def pick_custom_color(self):
        color = askcolor()
        if color and color[1]: 
            self.set_color(color[1])

    def save_settings(self):
        try:
            cf = float(self.caution_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Caution fee must be a number.")
            return

        data = {
            'business_name': self.name_entry.get(),
            'primary_color': self.selected_color,
            'caution_fee': cf,
            'logo_path': self.logo_path,
            'currency_symbol': self.currency_entry.get().strip() or '₦'
        }
        
        if self.db.save_settings(data):
            messagebox.showinfo("Success", "Settings Updated!")
            self.refresh_callback()

    def backup_database(self):
        dest_dir = filedialog.askdirectory(title="Choose Backup Destination Folder")
        if not dest_dir:
            return
        src = self.db.db_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(dest_dir, f"hotel_backup_{timestamp}.db")
        try:
            shutil.copy2(src, dest)
            messagebox.showinfo("Backup Successful", f"Database backed up to:\n{dest}")
        except Exception as e:
            messagebox.showerror("Backup Failed", f"Could not create backup:\n{e}")

    def restore_database(self):
        src = filedialog.askopenfilename(
            title="Select Backup File to Restore",
            filetypes=[("Database Files", "*.db")]
        )
        if not src:
            return
        confirm = messagebox.askyesno(
            "Confirm Restore",
            "WARNING: This will overwrite your current data with the backup.\n\nAre you absolutely sure?"
        )
        if confirm:
            try:
                shutil.copy2(src, self.db.db_path)
                messagebox.showinfo("Restore Successful", "Database restored! Please restart the application.")
            except Exception as e:
                messagebox.showerror("Restore Failed", f"Could not restore backup:\n{e}")
