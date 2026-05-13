import customtkinter as ctk

class HelpView(ctk.CTkFrame):
    def __init__(self, parent, db, current_user):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.current_user = current_user
        
        settings = self.db.get_settings()
        theme_color = settings.get('primary_color', '#2ecc71')
        
        # Header
        header = ctk.CTkLabel(self, text="Help & Support", font=("Arial", 24, "bold"))
        header.pack(pady=(20, 10), anchor="w", padx=20)
        
        desc = ctk.CTkLabel(self, text="Need assistance? Reach out to the developer.", font=("Arial", 14), text_color="gray")
        desc.pack(pady=(0, 20), anchor="w", padx=20)
        
        # Contact Info Frame
        info_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        info_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(info_frame, text="Developer Contact Information", font=("Arial", 16, "bold")).pack(pady=(15, 10))
        ctk.CTkLabel(info_frame, text="Email: hmsupport@oyinoost.com.ng", font=("Arial", 14)).pack(pady=5)
        ctk.CTkLabel(info_frame, text="Phone: +2348030796540", font=("Arial", 14)).pack(pady=(5, 15))
        
        # Message Form Frame
        form_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        form_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        ctk.CTkLabel(form_frame, text="Send a Message to Developer", font=("Arial", 16, "bold")).pack(pady=(15, 10))
        
        self.msg_textbox = ctk.CTkTextbox(form_frame, height=150)
        self.msg_textbox.pack(pady=10, padx=20, fill="x")
        
        btn = ctk.CTkButton(form_frame, text="Send Message", fg_color=theme_color, text_color="black", hover_color="#27ae60", command=self.send_message)
        btn.pack(pady=15)
        
        self.status_label = ctk.CTkLabel(form_frame, text="", font=("Arial", 14))
        self.status_label.pack(pady=5)
        
    def send_message(self):
        msg = self.msg_textbox.get("1.0", "end-1c").strip()
        if not msg:
            self.status_label.configure(text="Please enter a message.", text_color="#e74c3c")
            return
            
        # Log this in the system or save to DB. For now, log_action
        self.db.log_action(self.current_user, "Support Request", f"Message: {msg}")
        
        self.msg_textbox.delete("1.0", "end")
        self.status_label.configure(text="Message sent successfully! The developer will check the logs.", text_color="#2ecc71")
