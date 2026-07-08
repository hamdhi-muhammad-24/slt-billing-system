# config.py

PAGE_W = 595.5
PAGE_H = 842.25

COORDS = {
    # Header fields
    "account_number":   (223, 718),
    "invoice_number":   (223, 697),
    "billing_date":     (223, 676),
    "bill_period":      (205, 656),
    "invoice_amount":   (223, 636),
    "payment_due_date": (462, 636),

    # Contact lines
    "contact_line1":    (285, 598),
    "contact_line2":    (285, 588),

    # --------------------------------------------------
    # Main Barcode Configuration
    # Account Number Barcode
    # --------------------------------------------------

    "barcode": (415, 665),
    "barcode_width": 100,
    "barcode_height": 20,

    "bottom_barcode": (300, 100), # Adjust the X and Y as needed for your layout
    "bottom_barcode_width": 150, 
    "bottom_barcode_height": 20, # Added missing comma here!

    # NEW: Bottom QR Code
    "bottom_qr": (502, 60),
    "bottom_qr_size": 50
}

# Dynamic Address Box Configuration
ADDRESS_BOX = {
    "x": 315,         # X position for all address lines
    "y": 750,         # Starting Y position (first line)
    "line_h": 11,     # Vertical spacing between lines
    "font_size": 8,   # Font size
    "bold": True,     # Draw address in bold
    "max_lines": 11   # Total address lines
}

CHARGES_TBL = {
    "amount_x": 540,
    "y_start": 520,
    "y_min": 295,
    "line_h": 10,
    "font_size": 8,
    "min_font": 7,

    "indent_l1": 38,
    "indent_l2": 46,
    "indent_l3": 54,
}

TOTAL_AMOUNT_X = 540
TOTAL_AMOUNT_Y = 270