import customtkinter as ctk
from database import LuxuryDB
from login_view import LoginFrame
from settings_view import SettingsView
from rooms_view import RoomsView
from checkin_view import CheckInView
from active_guests_view import ActiveGuestsView
from inventory_view import InventoryView
from activity_logs_view import ActivityLogsView
from staff_view import StaffView
from help_view import HelpView
from home_view import HomeView
from theme import theme
import sys
import os

def get_base_path():
    """Returns the correct base directory whether running as a script or .exe."""
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe — use the folder next to the executable
        return os.path.dirname(sys.executable)
    else:
        # Running as a normal Python script
        return os.path.dirname(os.path.abspath(__file__))

# Set working directory so all relative paths (db, assets, receipts) work correctly
os.chdir(get_base_path())

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Database & Branding
        self.db = LuxuryDB()
        self.settings = self.db.get_settings()
        theme.load_from_settings(self.settings)
        
        self.title(self.settings.get('business_name', 'Hotel Management System'))
        self.geometry("1100x700")
        
        # Start with login
        self.show_login()

    def show_login(self):
        for child in self.winfo_children(): child.destroy()
        self.login_screen = LoginFrame(self, self.db, self.handle_login_success)
        self.login_screen.pack(expand=True, fill="both")

    def handle_login_success(self, username, role):
        print(f"DEBUG: Login successful for {username}. Role detected: '{role}'") # Check your terminal!
        self.current_user = username 
        
        # Verify_login from DB returns a tuple/sqlite3.Row, extract string value
        if isinstance(role, tuple) or hasattr(role, "__getitem__"):
            self.current_role = role[0]
        else:
            self.current_role = role
            
        self.login_screen.destroy()
        self.load_dashboard(self.current_role)

    def load_dashboard(self, role):
        # Convert role to string and lowercase safely
        role_str = str(role).lower() if role else "staff"
        print(f"DEBUG: Loading dashboard for role: {role_str}")

        self.settings = self.db.get_settings()
        theme.load_from_settings(self.settings)
        
        biz_name = self.settings.get('business_name', 'LUXURY PMS')
        theme_color = theme.PRIMARY

        self.container = ctk.CTkFrame(self)
        self.container.pack(expand=True, fill="both")

        self.sidebar = ctk.CTkFrame(self.container, width=220, corner_radius=0, fg_color=theme.BG_DARK)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content_area = ctk.CTkFrame(self.container, fg_color="#1a1a1a") 
        self.content_area.pack(side="right", expand=True, fill="both", padx=20, pady=20)

        # Header
        self.header_label = ctk.CTkLabel(self.sidebar, text=biz_name.upper(), font=theme.header_font(), text_color=theme_color)
        self.header_label.pack(pady=(30, 5))
        
        user_display = f"Logged in as: {self.current_user}"
        ctk.CTkLabel(self.sidebar, text=user_display, font=theme.small_font(), text_color=theme.TEXT_GRAY).pack(pady=(0, 20))

        # Standard Buttons
        self.nav_btn("Home / Dashboard", self.show_home)
        self.nav_btn("Rooms/Apartments", self.show_rooms)
        self.nav_btn("Check-In Guest", self.show_checkin)
        self.nav_btn("Active Guests", self.show_active_guests)
        self.nav_btn("Live Inventory", self.show_inventory)
        self.nav_btn("Help/Support", self.show_help)
        
        # Admin Specific Buttons
        if role_str == 'admin':
            print("DEBUG: User is admin, showing extra buttons.")
            self.nav_btn("Staff Management", self.show_staff)
            self.nav_btn("System Settings", self.show_settings)
            self.nav_btn("System Logs", self.show_logs)

        ctk.CTkButton(self.sidebar, text="Logout", fg_color=theme.DANGER, command=self.show_login).pack(side="bottom", pady=20, padx=20, fill="x")
        self.show_home() # Set default view on login
        
    def reload_app_theme(self):
        # Update settings and reload
        self.settings = self.db.get_settings()
        theme.load_from_settings(self.settings)
        
        if hasattr(self, 'container'):
            self.container.destroy()
        self.load_dashboard(self.current_role)

    def nav_btn(self, text, command):
        theme_color = theme.PRIMARY
        
        ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", 
                      hover_color=theme_color, # Buttons glow with theme color
                      border_width=1, border_color=theme_color,
                      anchor="w", font=theme.body_font(),
                      command=command).pack(pady=5, padx=20, fill="x")

    def clear_screen(self):
        for widget in self.content_area.winfo_children(): widget.destroy()

    def show_home(self):
        self.clear_screen()
        HomeView(self.content_area, self.db, self, self.current_user, self.current_role).pack(expand=True, fill="both")

    def show_settings(self):
        self.clear_screen()
        SettingsView(self.content_area, self.db, self.reload_app_theme).pack(expand=True, fill="both")

    def show_rooms(self):
        self.clear_screen()
        RoomsView(self.content_area, self.db, self.current_role).pack(expand=True, fill="both")

    def show_checkin(self):
        self.clear_screen()
        CheckInView(self.content_area, self.db, self.show_rooms).pack(expand=True, fill="both")

    def show_active_guests(self):
        self.clear_screen()
        ActiveGuestsView(self.content_area, self.db).pack(expand=True, fill="both")

    def show_inventory(self):
        self.clear_screen()
        InventoryView(self.content_area, self.db, self.current_user, self.current_role).pack(expand=True, fill="both")

    def show_logs(self):
        self.clear_screen()
        ActivityLogsView(self.content_area, self.db).pack(expand=True, fill="both")

    def show_staff(self):
        self.clear_screen()
        StaffView(self.content_area, self.db, self.current_user).pack(expand=True, fill="both")

    def show_help(self):
        self.clear_screen()
        HelpView(self.content_area, self.db, self.current_user).pack(expand=True, fill="both")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = App()
    app.mainloop()
