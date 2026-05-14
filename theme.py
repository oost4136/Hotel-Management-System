import customtkinter as ctk

class Theme:
    def __init__(self):
        # Defaults
        self.PRIMARY = "#2ecc71"
        self.SECONDARY = "#3498db"
        self.DANGER = "#e74c3c"
        self.WARNING = "#f39c12"
        self.SUCCESS = "#2ecc71"
        self.BG_DARK = "#2b2b2b"
        self.TEXT_GRAY = "gray"
        self.TRANSPARENT = "transparent"
        self.FONT_FAMILY = "Arial"

    def load_from_settings(self, settings):
        if not settings: return
        self.PRIMARY = settings.get('primary_color', self.PRIMARY)
        self.SECONDARY = settings.get('secondary_color', self.SECONDARY)
        self.FONT_FAMILY = settings.get('font_family', self.FONT_FAMILY)

    def get_font(self, size=14, weight="normal"):
        return (self.FONT_FAMILY, size, weight)

    def header_font(self):
        return (self.FONT_FAMILY, 24, "bold")

    def subheader_font(self):
        return (self.FONT_FAMILY, 20, "bold")

    def body_font(self, bold=False):
        return (self.FONT_FAMILY, 14, "bold" if bold else "normal")

    def card_font(self):
        return (self.FONT_FAMILY, 16, "bold")

    def small_font(self, italic=False):
        return (self.FONT_FAMILY, 12, "italic" if italic else "normal")

# Global instance
theme = Theme()
