import os
import json
from core.pdf_renderer import BaseRenderer

from templates.usd_open_item.config import (
    PAGE_W,
    PAGE_H,
    COORDS,
    ADDRESS_BOX,
    CHARGES_TBL,
)

TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PDF = os.path.join(TEMPLATE_DIR, "layout.pdf")


class USDOpenItemRenderer(BaseRenderer):
    """
    Renderer for USD Open Item Bills (BILLSTYLE=21).
    Inherits from BaseRenderer for automated save() and path handling.
    """

    def __init__(self):
        super().__init__(TEMPLATE_PDF)

    def render(self, data):
        """
        The main rendering loop. The BaseRenderer automatically calls this
        and handles saving the output file behind the scenes.
        """
        self._draw_system_strings(data)
        self._draw_header(data)
        self._draw_barcode(data)
        self._draw_contact(data)
        self._draw_address(data)
        self._draw_charges(data)
        self._draw_bottom_barcode(data)
        self._draw_bottom_qr_code(data)

    # --------------------------------------------------
    # System Strings
    # --------------------------------------------------
    def _draw_system_strings(self, data):
        top_x = 40
        top_y = PAGE_H - 100

        self.text(top_x, top_y, data.get("file_info_string", ""), size=7.5)
        self.text(top_x, top_y - 8, data.get("customer_segment", "Int'l Operators"), size=7.5, bold=True)

    # --------------------------------------------------
    # Header
    # --------------------------------------------------
    def _draw_header(self, data):
        self.text(*COORDS["account_number"], data.get("account_number", ""))
        self.text(*COORDS["invoice_number"], data.get("invoice_number", ""))
        self.text(*COORDS["billing_date"], data.get("billing_date", ""))
        self.text(*COORDS["bill_period"], data.get("bill_period", ""), size=8)
        
        self.text(*COORDS["invoice_amount"], data.get("invoice_amount", ""), bold=True)
        self.text(*COORDS["payment_due_date"], data.get("payment_due_date", ""), bold=True)

    # --------------------------------------------------
    # Barcode
    # --------------------------------------------------
    def _draw_barcode(self, data):
        barcode_value = data.get("barcode") or data.get("account_number")

        if not barcode_value:
            return

        # Uses .get() with fallbacks just in case width/height aren't in config
        self.draw_barcode(
            *COORDS["barcode"],
            barcode_value,
            width=COORDS.get("barcode_width", 100),
            height=COORDS.get("barcode_height", 20)
        )

    # --------------------------------------------------
    # Bottom Barcode
    # --------------------------------------------------
    def _draw_bottom_barcode(self, data):
        # Extract the fields needed for the USB Open Item specific format
        item_code = data.get("item_code", "UNKNOWN")
        account_number = data.get("account_number", "")
        
        # Use invoice_amount, fallback to total_charges if missing
        amount = data.get("invoice_amount", data.get("total_charges", 0.0))
        
        # Format the barcode string just like the generator script
        barcode_value = data.get("bottom_barcode_string") or f"USB-{item_code}_{account_number}_{amount}"
        
        # Check config.py for coords, otherwise fallback to bottom-left (e.g., x=40, y=40)
        coords = COORDS.get("bottom_barcode", (40, 40))

        self.draw_barcode(
            *coords,
            barcode_value,
            width=COORDS.get("bottom_barcode_width", 150),
            height=COORDS.get("bottom_barcode_height", 20)
        )

    # --------------------------------------------------
    # Bottom QR Code
    # --------------------------------------------------
    def _draw_bottom_qr_code(self, data):
        # Construct the QR payload with key invoice data
        qr_payload = {
            "DocType": "USB_OPEN_ITEM",
            "ItemCode": data.get("item_code", ""),
            "AccountNo": data.get("account_number", ""),
            "Amount": data.get("invoice_amount", data.get("total_charges", 0.0))
        }
        
        qr_data_string = data.get("bottom_qr_string") or json.dumps(qr_payload)
        
        # Fallback coordinates places the QR code to the right of the barcode
        coords = COORDS.get("bottom_qr", (220, 40))
        size = COORDS.get("bottom_qr_size", 40)

        # Draw the QR code using the base class renderer methods
        if hasattr(self, 'draw_qrcode'):
            self.draw_qrcode(*coords, qr_data_string, size=size)
        elif hasattr(self, 'draw_qr'):
            self.draw_qr(*coords, qr_data_string, size=size)

    # --------------------------------------------------
    # Contact
    # --------------------------------------------------
    def _draw_contact(self, data):
        self.text(*COORDS["contact_line1"], data.get("contact_line1", ""), size=8)
        self.text(*COORDS["contact_line2"], data.get("contact_line2", ""), size=8)

    # --------------------------------------------------
    # Address
    # --------------------------------------------------
    def _draw_address(self, data):
        y = ADDRESS_BOX["y"]
        max_lines = ADDRESS_BOX.get("max_lines", 11)

        for i in range(1, max_lines + 1):
            value = data.get(f"address_line{i}", "").strip()
            if value:
                self.text(
                    ADDRESS_BOX["x"],
                    y,
                    value,
                    size=ADDRESS_BOX["font_size"],
                    bold=ADDRESS_BOX.get("bold", True)
                )
                y -= ADDRESS_BOX["line_h"]

    # --------------------------------------------------
    # Auto-fit helpers
    # --------------------------------------------------
    def _auto_fit_line_h(self, n, y_start, y_min, default_h, min_h=5):
        if n == 0:
            return default_h
        available = y_start - y_min
        needed = n * default_h
        return default_h if needed <= available else max(available / n, min_h)

    def _auto_fit_font(self, n, y_start, y_min, line_h, default_size, min_size=7):
        if n == 0:
            return default_size
        available = y_start - y_min
        needed = n * line_h
        if needed <= available:
            return default_size
        return max(int(default_size * (available / needed)), min_size)

    # --------------------------------------------------
    # Charges Table
    # --------------------------------------------------
    def _draw_charges(self, data):
        charges = data.get("charges", [])
        tbl = CHARGES_TBL

        line_h = self._auto_fit_line_h(len(charges), tbl["y_start"], tbl["y_min"], tbl["line_h"])
        font_size = self._auto_fit_font(len(charges), tbl["y_start"], tbl["y_min"], line_h, tbl["font_size"], tbl["min_font"])

        y = tbl["y_start"]

        for charge in charges:
            description = charge.get("description", "").strip()
            amount = charge.get("amount", None)
            level = charge.get("level", 3)

            if level == 1:
                x = tbl["indent_l1"] + 20
                bold = True
            elif level == 2:
                x = tbl["indent_l2"] + 20
                bold = False
            else:
                x = tbl["indent_l3"]
                bold = False

            self.text(x, y, description, size=font_size, bold=bold)

            if amount is not None:
                self.number(
                    tbl["amount_x"],
                    y,
                    amount,
                    size=font_size,
                    bold=bold,
                    align="right"
                )

            y -= line_h

        # ============================
        # Total Charges for the Period
        # ============================
        extracted_total = data.get("total_charges", 0.00)
        y -= (line_h * 0.25)
        
        line_left_x = tbl.get("indent_l1", 40)
        line_right_x = tbl.get("amount_x", PAGE_W - 40)
        
        # 1. Draw top line
        if hasattr(self, 'canvas'):  # Standard reportlab BaseRenderer wrapper
            self.canvas.setLineWidth(1)
            self.canvas.line(line_left_x + 20, y, line_right_x, y)
        elif hasattr(self, 'line'):  # Alternative BaseRenderer wrapper
            self.line(line_left_x + 20, y, line_right_x, y)
            
        y -= line_h
        
        # 2. Draw the text
        self.text(line_left_x + 20, y, "Total Charges for the Period", size=font_size, bold=True)
        self.number(
            line_right_x, 
            y, 
            extracted_total, 
            size=font_size, 
            bold=True, 
            align="right"
        )
        
        y -= (line_h * 0.5)
        
        # 3. Draw bottom line
        if hasattr(self, 'canvas'):
            self.canvas.line(line_left_x + 20, y, line_right_x, y)
        elif hasattr(self, 'line'):
            self.line(line_left_x + 20, y, line_right_x, y)