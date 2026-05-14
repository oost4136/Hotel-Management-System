from fpdf import FPDF
import os
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.output_dir = "receipts"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _safe_text(self, value):
        return str(value).encode('latin-1', 'replace').decode('latin-1')

    def _safe_currency(self, value):
        currency = str(value or '').strip()
        if currency in {'₦', 'â‚¦'}:
            return 'NGN '
        return self._safe_text(currency)

    def create_hotel_receipt(self, data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # 1. Setup Data & Theme Safely
        settings = data.get('settings', {})
        logo_path = settings.get('logo_path', '')
        currency = self._safe_currency(settings.get('currency_symbol', 'NGN '))
        
        # Clean text to prevent PDF encoding crashes
        biz_name = self._safe_text(settings.get('business_name', 'HOTEL PMS'))
        guest_name = self._safe_text(data.get('guest_name', 'Guest'))
        room_name = self._safe_text(data.get('room_name', 'Room'))
        
        theme_hex = settings.get('primary_color', '#2ecc71').lstrip('#')
        
        try:
            r, g, b = tuple(int(theme_hex[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            r, g, b = (46, 204, 113) # Fallback to default green if color is blank

        # 2. Add Logo Safely (Catches transparency/format errors)
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=85, y=10, w=40)
                pdf.ln(40) 
            except Exception as e:
                print(f"Skipping logo, unsupported PDF format: {e}")
                pdf.ln(10) # Add space instead of crashing
        
        # 3. Header - Dynamic Brand Identity
        pdf.set_font("Arial", 'B', 20)
        pdf.set_text_color(r, g, b) 
        pdf.cell(0, 10, biz_name.upper(), ln=True, align='C')
        
        pdf.set_font("Arial", size=10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 5, "Generated securely by Oyinoost PMS", ln=True, align='C')
        pdf.ln(10)

        # 4. Invoice Info
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"FINAL INVOICE: {datetime.now().strftime('%Y%m%d%H%M')}", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Date: {datetime.now().strftime('%d %B, %Y %I:%M %p')}", ln=True)
        pdf.ln(5)

        # 5. Guest & Room Details
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, " GUEST DETAILS", ln=True, fill=True)
        pdf.set_font("Arial", size=11)
        pdf.cell(95, 10, f"Guest: {guest_name}")
        pdf.cell(95, 10, f"Room: {room_name}", ln=True)
        pdf.cell(95, 10, f"Check-In: {data.get('check_in', 'N/A')}")
        pdf.cell(95, 10, f"Check-Out: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(5)

        # 6. Payment Table
        days = float(data.get('days_stayed', 1.0))
        rate = float(data.get('rate', 0.0))
        caution = float(data.get('caution_fee', 0.0))
        total_room_cost = rate * days
        
        inventory_orders = data.get('inventory_orders', [])
        inventory_total = float(data.get('inventory_total', 0.0))
        grand_total = float(data.get('grand_total', total_room_cost))

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(130, 10, "Description", border=1)
        pdf.cell(60, 10, "Amount", border=1, ln=True, align='C')
        
        pdf.set_font("Arial", size=11)
        pdf.cell(130, 10, f"Room Rate ({room_name}) x {days:g} days", border=1)
        pdf.cell(60, 10, f"{currency}{total_room_cost:,.2f}", border=1, ln=True, align='R')
        
        pdf.cell(130, 10, "Caution Fee (Refunded / Processed)", border=1)
        pdf.cell(60, 10, f"{currency}{caution:,.2f}", border=1, ln=True, align='R')

        if inventory_orders:
            pdf.set_font("Arial", 'B', 11)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(190, 8, "Inventory Purchases (Charged to Room)", border=1, ln=True, fill=True)
            pdf.set_font("Arial", size=10)
            for order in inventory_orders:
                item_name = self._safe_text(order['item_name'])
                pdf.cell(130, 8, f"  - {item_name} (Qty: {order['quantity']} @ {currency}{order['price']:,.2f})", border=1)
                pdf.cell(60, 8, f"{currency}{order['total']:,.2f}", border=1, ln=True, align='R')

        # 7. Total with Theme Color
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(r, g, b)
        pdf.cell(130, 12, "FINAL BALANCE SETTLED", border=1)
        pdf.cell(60, 12, f"{currency}{grand_total:,.2f}", border=1, ln=True, align='R')

        # 8. Footer
        pdf.ln(20)
        pdf.set_text_color(150, 150, 150)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, f"Thank you for choosing {biz_name}. Please visit us again!", ln=True, align='C')

        # 9. FINAL STEP: Save the file securely
        safe_filename = guest_name.replace(' ', '_').replace('/', '_')
        filename = f"Receipt_{safe_filename}_{datetime.now().strftime('%H%M%S')}.pdf"
        file_path = os.path.join(self.output_dir, filename)
        
        pdf.output(file_path)
        
        return os.path.abspath(file_path)
