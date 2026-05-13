import customtkinter as ctk

class ActivityLogsView(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.settings = self.db.get_settings()
        self.theme_color = self.settings.get('primary_color', '#2ecc71')
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header, text="SYSTEM ACTIVITY LOGS", font=("Arial", 24, "bold"), text_color=self.theme_color).pack(side="left")

        # Scrollable Grid
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.load_logs()

    def load_logs(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        logs = self.db.get_logs()
        if not logs:
            ctk.CTkLabel(self.grid_frame, text="No system logs found.", text_color="gray", font=("Arial", 16)).pack(pady=50)
            return

        for idx, log in enumerate(logs):
            card = ctk.CTkFrame(self.grid_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=2)
            
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=10, pady=10, fill="x", expand=True)
            
            # Timestamp & User
            ctk.CTkLabel(info_frame, text=f"[{log['timestamp']}]", font=("Consolas", 12), text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(info_frame, text=f"User: {log['username']}", font=("Arial", 12, "bold"), text_color=self.theme_color).pack(side="left", padx=10)
            
            # Action & Details
            ctk.CTkLabel(info_frame, text=f"ACTION: {log['action']}", font=("Arial", 12, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(info_frame, text=f"| {log['details']}", font=("Arial", 12)).pack(side="left", padx=5)
