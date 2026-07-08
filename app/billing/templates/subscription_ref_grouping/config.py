COORDS = {
    "slt_vat_reg_label":      (273.6, 748.2),
    "customer_vat_reg_label": (273.6, 739.5),

    "gen_id_line": (273, 590),
    "gen_id_line2": (273, 580.4),

    "account_number":       (155, 701),
    "invoice_number":       (155, 672),
    "billing_date":         (155, 643),
    "billing_period":       (155, 615),

    "customer_name":        (280, 725),
    "customer_business":    (280, 715),
    "customer_addr_start":  705,
    "customer_addr_x":      280,
    "customer_addr_line_h": 9,

    "badge_text":           (330, 612),

    "balance_bf":           (83, 512),
    "payments_received":    (188, 512),
    "charges_period":       (293, 512),
    "total_payable":        (406, 512),
    "payment_due_date":     (508, 512),

    "taxes_label":          (43.2, 300),
    "taxes_amount":         (553, 300),
    "taxes_line_h":         11,
    "total_charges_label":  (43.2, 248),
    "total_charges_amount": (553, 248),

    "payments_start":       (50, 220),
    "payments_amount_x":    288,
    "payments_line_h":      10,

    "barcode":              (375, 638),
    "barcode_width":        100,
    "barcode_height":       20,

    "qr_code":       (511.2, 88.4),
    "qr_size":       48,

    "payonline_qr":       (498, 689),
    "payonline_qr_size":  48,

    "slip_barcode": (309, 110),
    "slip_barcode_width": 138,
    "slip_barcode_height": 25,
    "slip_telephone":       (157, 120),
    "slip_invoice":         (157, 97),
    "slip_customer":        (157, 75),
    "slip_account":         (157, 50),
}

# 3-level hierarchy: subscription_ref → product_label → charges
CHARGES_TABLE = {
    "page1_y_start":            472,
    "page1_y_min":              330,
    "otherpage_y_start":        780,
    "otherpage_y_min":          80,

    "line_h":                   11,
    "font_size":                9,

    "subscription_ref_x":       43.2,
    "product_label_x":          50.4,
    "product_label_y_gap":      15,
    "desc_x":                   57.6,
    "desc_max_x":               500,
    "amount_x":                 553,
    "subtotal_indent":          65,
}

FONTS = {
    "header":            {"size": 9,   "bold": False},
    "customer_name":     {"size": 9.5, "bold": True},
    "customer_addr":     {"size": 9,   "bold": True},
    "badge":             {"size": 11,  "bold": True},
    "summary_box":       {"size": 10,  "bold": False},
    "summary_total":     {"size": 10,  "bold": True},
    "subscription_ref":  {"size": 10,  "bold": True},
    "product_label":     {"size": 9,   "bold": True},
    "charge_line":       {"size": 9,   "bold": False},
    "subtotal":          {"size": 9,   "bold": True},
    "top_subtotal":      {"size": 9,   "bold": True},
    "taxes":             {"size": 9,   "bold": False},
    "total":             {"size": 10,  "bold": True},
    "payments":          {"size": 8,   "bold": False},
    "slip":              {"size": 8,   "bold": False},
    "gen_id":            {"size": 8,   "bold": False},
}