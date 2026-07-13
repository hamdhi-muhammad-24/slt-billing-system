"""Summary Statement (Sheet 7) - Coordinates."""

COORDS_HEADER = {
    "date_of_statement":  (165, 713),
    "customer_ref_no":    (165, 682),

    # Customer contact
    "customer_y_start":   725,
    "customer_x":         290,
    "customer_line_h":    11,

    # Barcode
    "barcode":            (375, 638),
    "barcode_width":      100,
    "barcode_height":     20,

    "page_num_x":         540,
    "page_num_y":         753,
}

TABLE_COLS = {
    "account_no_x":   60,
    "account_name_x": 155,
    "net_amount_x":   360,
    "tax_amount_x":   440,
    "gross_total_x":  520,
    "name_max_x":     330,
}

TABLE = {
    "page1_y_start":  560,
    "page1_y_min":    60,
    "middle_y_start": 750,
    "middle_y_min":   100,
    "line_h":         18,
    "font_size":      9,
}

TOTAL_ROW = {
    "label_x":        155,
    "net_amount_x":   360,
    "tax_amount_x":   440,
    "gross_total_x":  520,
    "font_size":      10,
    "gap_above":      30,
}

MIDDLE_PAGE = {
    "invoice_no_x":   45,
    "invoice_no_y":   790,
    "page_num_x":     540,
    "page_num_y":     790,
}

FONTS = {
    "header":     {"size": 10, "bold": False},
    "customer":   {"size": 8,  "bold": False},
    "table_row":  {"size": 8,  "bold": False},
    "total_row":  {"size": 8, "bold": True},
    "page_num":   {"size": 7,  "bold": False},
    "invoice_no": {"size": 7, "bold": True},
}