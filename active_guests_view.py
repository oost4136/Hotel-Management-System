import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from pdf_generator import PDFGenerator
import os
import subprocess
import sys

class ActiveGuestsView(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.settings = self.db.get_settings()
        self.theme_color = self.settings.get('primary_color', '#2ecc71')
        self.currency = self.settings.get('currency_symbol', '₦')
        
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkLabel(header, text="ACTIVE GUESTS", font=("Arial", 24, "bold"), text_color=self.theme_color).pack(side="left")

        # Scrollable Grid
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.load_guests()

    def load_guests(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        bookings = self.db.get_active_bookings()
        if not bookings:
            ctk.CTkLabel(self.grid_frame, text="No guests are currently checked in.", text_color="gray", font=("Arial", 16)).pack(pady=50)
            return

        for idx, b in enumerate(bookings):
            card = ctk.CTkFrame(self.grid_frame, fg_color="#2b2b2b")
            card.pack(fill="x", pady=5)
            
            # Guest Info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", padx=15, pady=15)
            
            ctk.CTkLabel(info_frame, text=f"{b['customer_name']}", font=("Arial", 18, "bold")).pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Room: {b['room_name']} ({self.currency}{b['room_price']:,.2f}/night)", text_color="gray").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"Phone: {b['guest_phone']} | Check-In: {b['check_in']}").pack(anchor="w")
            if b.get('check_out'):
                ctk.CTkLabel(info_frame, text=f"Expected Checkout: {b['check_out']}", text_color="#f39c12").pack(anchor="w")

            # Actions
            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(side="right", padx=15, pady=15)
            
            ctk.CTkButton(action_frame, text="Extend Stay", width=120, fg_color="#f39c12", hover_color="#d68910",
                          command=lambda booking=b: self.open_extend_modal(booking)).pack(pady=2)
            ctk.CTkButton(action_frame, text="Checkout Guest", width=120, fg_color="#e74c3c", hover_color="#c0392b",
                          command=lambda booking=b: self.process_checkout(booking)).pack(pady=2)

    def process_checkout(self, booking):
        CheckoutModal(self, self.db, booking, self.load_guests, self.currency)

    def open_extend_modal(self, booking):
        ExtendStayModal(self, self.db, booking, self.load_guests)

class ExtendStayModal(ctk.CTkToplevel):
    def __init__(self, parent, db, booking, refresh_callback):
        super().__init__(parent)
        self.title("Extend Stay")
        self.geometry("400x300")
        self.db = db
        self.booking = booking
        self.refresh_callback = refresh_callback
        
        # Keep modal on top
        self.attributes("-topmost", True)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text=f"Extend Stay: {self.booking['customer_name']}", font=("Arial", 18, "bold")).pack(pady=20)
        
        ctk.CTkLabel(self, text="New Expected Checkout Date:").pack(pady=5)
        
        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.pack(pady=10)

        years = [str(y) for y in range(2026, 2031)]
        self.year_var = ctk.StringVar(value="2026")
        ctk.CTkOptionMenu(date_frame, values=years, variable=self.year_var, width=80).pack(side="left", padx=2)

        months = [f"{m:02d}" for m in range(1, 13)]
        self.month_var = ctk.StringVar(value="05")
        ctk.CTkOptionMenu(date_frame, values=months, variable=self.month_var, width=60).pack(side="left", padx=2)

        days = [f"{d:02d}" for d in range(1, 32)]
        self.day_var = ctk.StringVar(value="10")
        ctk.CTkOptionMenu(date_frame, values=days, variable=self.day_var, width=60).pack(side="left", padx=2)

        if self.booking.get('check_out'):
            # Try to parse existing YYYY-MM-DD
            parts = self.booking['check_out'].split('-')
            if len(parts) >= 3:
                self.year_var.set(parts[0][:4])
                self.month_var.set(parts[1][:2])
                self.day_var.set(parts[2][:2][:2])

        ctk.CTkButton(self, text="Save Extension", fg_color="#2ecc71", command=self.save).pack(pady=20)

    def save(self):
        new_date = f"{self.year_var.get()}-{self.month_var.get()}-{self.day_var.get()}"
        if not new_date:
            messagebox.showerror("Error", "Please enter a valid date.")
            return

        if self.db.extend_stay(self.booking['booking_id'], new_date):
            messagebox.showinfo("Success", "Stay extended successfully!")
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to update database.")

class CheckoutModal(ctk.CTkToplevel):
    def __init__(self, parent, db, booking, refresh_callback, currency='₦'):
        super().__init__(parent)
        self.title("Process Checkout")
        self.geometry("500x600")
        self.db = db
        self.booking = booking
        self.refresh_callback = refresh_callback
        self.currency = currency
        
        # Keep modal on top
        self.attributes("-topmost", True)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        ctk.CTkLabel(self, text=f"Checkout: {self.booking['customer_name']}", font=("Arial", 20, "bold")).pack(pady=20)

        # Calculate days stayed
        check_in_str = self.booking['check_in']
        try:
            check_in_dt = datetime.strptime(check_in_str, "%Y-%m-%d %H:%M:%S")
            diff = datetime.now() - check_in_dt
            self.days_stayed = max(1, diff.days)
        except Exception:
            self.days_stayed = 1
            
        self.rate = self.booking['room_price']
        self.caution = self.booking['caution_fee']
        self.total_room = (self.rate * self.days_stayed)

        self.unpaid_orders = self.db.get_unpaid_orders_for_booking(self.booking['booking_id'])
        self.inventory_total = sum(order['total'] for order in self.unpaid_orders)
        self.grand_total = self.total_room + self.inventory_total

        details_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        details_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(details_frame, text=f"Room: {self.booking['room_name']}", font=("Arial", 14)).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(details_frame, text=f"Check-In: {check_in_str}", font=("Arial", 14)).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(details_frame, text=f"Duration: {self.days_stayed} Day(s)", font=("Arial", 14, "bold")).pack(anchor="w", padx=15, pady=5)
        
        ctk.CTkLabel(details_frame, text=f"Room Rate: {self.currency}{self.rate:,.2f}/night", font=("Arial", 14)).pack(anchor="w", padx=15, pady=5)
        ctk.CTkLabel(details_frame, text=f"Caution Fee Paid: {self.currency}{self.caution:,.2f}", font=("Arial", 14)).pack(anchor="w", padx=15, pady=5)

        ctk.CTkLabel(details_frame, text=f"Total Room Cost: {self.currency}{self.total_room:,.2f}", font=("Arial", 16, "bold"), text_color="#f39c12").pack(anchor="w", padx=15, pady=(15, 5))

        if self.inventory_total > 0:
            ctk.CTkLabel(details_frame, text=f"Inventory Charges: {self.currency}{self.inventory_total:,.2f}", font=("Arial", 16, "bold"), text_color="#e74c3c").pack(anchor="w", padx=15, pady=5)

        ctk.CTkLabel(details_frame, text=f"GRAND TOTAL: {self.currency}{self.grand_total:,.2f}", font=("Arial", 18, "bold"), text_color="#2ecc71").pack(anchor="w", padx=15, pady=15)

        ctk.CTkButton(self, text="Finalize Checkout & Generate Receipt", fg_color="#e74c3c", height=50, command=self.finalize_checkout).pack(pady=30)

    def finalize_checkout(self):
        # 1. Update Database
        if not self.db.complete_checkout(self.booking['booking_id'], self.booking['room_id']):
            messagebox.showerror("Error", "Failed to update database.")
            return

        # 2. Generate PDF
        pdf_gen = PDFGenerator()
        data = {
            'settings': self.db.get_settings(),
            'guest_name': self.booking['customer_name'],
            'room_name': self.booking['room_name'],
            'check_in': self.booking['check_in'],
            'days_stayed': self.days_stayed,
            'rate': self.rate,
            'caution_fee': self.caution,
            'inventory_orders': self.unpaid_orders,
            'inventory_total': self.inventory_total,
            'grand_total': self.grand_total
        }
        
        try:
            pdf_path = pdf_gen.create_hotel_receipt(data)
            messagebox.showinfo("Success", f"Checkout successful!\nReceipt saved to:\n{pdf_path}")
            
            # Open PDF
            if sys.platform == "win32":
                os.startfile(pdf_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", pdf_path])
            else:
                subprocess.call(["xdg-open", pdf_path])
        except Exception as e:
            messagebox.showerror("PDF Error", f"Checkout successful, but PDF generation failed:\n{e}")

        self.refresh_callback()
        self.destroy()
