"""NonVAT Enterprise Renderer (Sheet 19)."""
import os
from datetime import datetime
from core.pdf_renderer import BaseRenderer
from templates.nonvat_enterprise.config import COORDS, CHARGES_TABLE, FONTS

TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PDF = os.path.join(TEMPLATE_DIR, "layout.pdf")


class NonVATEnterpriseRenderer(BaseRenderer):
    """Renders NonVAT Enterprise invoice_of_summary."""

    def __init__(self):
        super().__init__(TEMPLATE_PDF)

    def render(self, data):
        self._draw_header(data)
        self._draw_customer(data)
        self._draw_badge()
        self._draw_generation_id(data)
        self._draw_summary_boxes(data)
        self._draw_page1_footer(data)

        y = self._draw_charges(data["product_labels"])
        y = self._draw_adjustments(data, y)
        y = self._draw_taxes_only(data, y)
        self._draw_total_charges_fixed(data)
        self._draw_payments_fixed(data)

        self._draw_usage_full_from_page2(data)
        total_pages = self.page_count()
        self._draw_page_indicators(data, total_pages)

    # ==================== HEADER/CUSTOMER/BADGE ====================

    def _draw_header(self, data):
        f = FONTS["header"]
        self.text(*COORDS["telephone_number"], data["telephone_number"], size=f["size"])
        self.text(*COORDS["account_number"], data["account_number"], size=f["size"])
        self.text(*COORDS["invoice_number"], data["invoice_number"], size=f["size"])
        self.text(*COORDS["billing_date"], data["billing_date"], size=f["size"])
        period = f"{data['billing_period_start']} - {data['billing_period_end']}"
        self.text(*COORDS["billing_period"], period, size=f["size"])

    def _draw_customer(self, data):
        f = FONTS["customer_name"]
        if data.get("business_name"):
            self.text(*COORDS["customer_business"], data["business_name"],
                       size=f["size"], bold=f["bold"])

        f = FONTS["customer_addr"]
        addr = data["address_lines"] + ([data["zip_code"]] if data["zip_code"] else [])
        self.multiline_block(
            COORDS["customer_addr_x"],
            COORDS["customer_addr_start"],
            addr,
            line_height=COORDS["customer_addr_line_h"],
            size=f["size"], bold=f["bold"]
        )

    def _draw_badge(self):
        f = FONTS["badge"]
        self.text(*COORDS["badge_text"], "ENTERPRISE", size=f["size"], bold=f["bold"])

    def _draw_generation_id(self, data):
        f = FONTS["gen_id"]
        due = data.get("payment_due_date", "")
        try:
            dd, mm, yyyy = due.split("/")
            due_mmddyy = f"{mm}{dd}{yyyy[-2:]}"
        except ValueError:
            due_mmddyy = ""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f'{data["source_filename"]}_{timestamp}{due_mmddyy}'
        self.text(*COORDS["gen_id_line"], line, size=f["size"])
        if data.get("customer_segment"):
            self.text(*COORDS["gen_id_line2"], data["customer_segment"], size=f["size"])

    def _draw_summary_boxes(self, data):
        f = FONTS["summary_box"]
        self.number(*COORDS["balance_bf"], data["balance_bf"], size=f["size"], align="center")
        self.number(*COORDS["payments_received"], data["payments_received"], size=f["size"], align="center")
        self.number(*COORDS["charges_period"], data["charges_period"], size=f["size"], align="center")

        f = FONTS["summary_total"]
        self.number(*COORDS["total_payable"], data["total_payable"],
                     size=f["size"], bold=True, align="center")
        self.text(*COORDS["payment_due_date"], data["payment_due_date"],
                   size=f["size"], bold=True, align="center")

    def _draw_page1_footer(self, data):
        # Static payonline QR
        self.draw_static_payonline_qr(
            *COORDS["payonline_qr"],
            size=COORDS["payonline_qr_size"]
        )

        # Payment QR — account_number + total_charges
        self.draw_qr(
            *COORDS["qr_code"],
            account_number=data["account_number"],
            total_charges=data["total_charges"],
            size=COORDS["qr_size"]
        )

        # Address barcode (just account number)
        self.draw_barcode(
            *COORDS["barcode"],
            data["account_number"],
            width=COORDS["barcode_width"],
            height=COORDS["barcode_height"]
        )

        # Payment slip barcode (invoice number + total charges)
        self.draw_slip_barcode(
            *COORDS["slip_barcode"],
            bill_ref=data["invoice_number"],
            total_charges=data["total_charges"],
            width=COORDS["slip_barcode_width"],
            height=COORDS["slip_barcode_height"]
        )
        f = FONTS["slip"]
        self.text(*COORDS["slip_telephone"], data["telephone_number"], size=f["size"])
        self.text(*COORDS["slip_invoice"], data["invoice_number"], size=f["size"])
        self.text(*COORDS["slip_customer"], data["business_name"], size=f["size"])
        self.text(*COORDS["slip_account"], data["account_number"], size=f["size"])


    def _draw_charges(self, product_labels):
        y = CHARGES_TABLE["page1_y_start"]
        if not product_labels:
            return y

        f = FONTS["product_label"]
        fc = FONTS["charge_line"]
        y_min = CHARGES_TABLE["page1_y_min"]
        line_h = CHARGES_TABLE["line_h"]
        label_gap = CHARGES_TABLE["product_label_y_gap"]

        for product in product_labels:
            space_needed = label_gap + len(product["charges"]) * line_h
            if y - space_needed < y_min:
                self.new_page()
                y = CHARGES_TABLE["otherpage_y_start"]
                y_min = CHARGES_TABLE["otherpage_y_min"]

            self.text(CHARGES_TABLE["product_label_x"], y,
                       product["label"], size=f["size"], bold=f["bold"])
            y -= label_gap

            for charge in product["charges"]:
                if y < y_min:
                    self.new_page()
                    y = CHARGES_TABLE["otherpage_y_start"]
                    y_min = CHARGES_TABLE["otherpage_y_min"]

                self.text(CHARGES_TABLE["desc_x"], y,
                           charge["description"], size=fc["size"])
                if charge["amount"]:
                    self.number(CHARGES_TABLE["amount_x"], y,
                                 charge["amount"], size=fc["size"], align="right")
                y -= line_h

        return y

    def _draw_adjustments(self, data, y):
        adjustments = data.get("adjustments", [])
        if not adjustments:
            return y

        f = FONTS["taxes"]
        line_h = CHARGES_TABLE["line_h"]
        self.text(CHARGES_TABLE["product_label_x"], y, "Adjustments",
                   size=f["size"], bold=True)
        y -= line_h
        for adj in adjustments:
            self.text(CHARGES_TABLE["desc_x"], y, adj["description"], size=f["size"])
            self.number(CHARGES_TABLE["amount_x"], y, adj["amount"],
                         size=f["size"], align="right")
            y -= line_h
        return y

    def _draw_taxes_only(self, data, y):
        """Taxes & Levies FLOWING with charges (Total Charges is now independent)."""
        line_h = CHARGES_TABLE["line_h"]
        f = FONTS["taxes"]
        self.text(CHARGES_TABLE["product_label_x"], y, "Taxes & Levies",
                   size=f["size"], bold=True)
        y -= line_h
        self.text(CHARGES_TABLE["desc_x"], y, "Taxes & Levies", size=f["size"])
        self.number(CHARGES_TABLE["amount_x"], y, data["taxes_total"],
                     size=f["size"], align="right")
        return y - line_h

    def _draw_total_charges_fixed(self, data):
        """1. Total Charges for the Period - INDEPENDENT fixed position."""
        page1_canvas = self.canvases[0][1]
        f = FONTS["total"]

        x = COORDS["total_charges_label_x"]
        y = COORDS["total_charges_label_y"]
        amt_x = COORDS["total_charges_amount_x"]

        page1_canvas.setFont("Helvetica-Bold", f["size"])
        page1_canvas.drawString(x, y, "Total Charges for the Period")
        page1_canvas.drawRightString(amt_x, y, f"{data['total_charges']:,.2f}")

    def _draw_payments_fixed(self, data):
        """2. Details of Payments Received - FIXED position.
        Amount column position is configurable via COORDS['payments_amount_x']."""
        page1_canvas = self.canvases[0][1]

        f = FONTS["payments"]
        header_x = COORDS["payments_header_x"]
        header_y = COORDS["payments_header_y"]
        row_x = COORDS["payments_row_x"]
        row_y = COORDS["payments_row_start_y"]
        amt_x = COORDS["payments_amount_x"]     # ← configurable
        line_h = COORDS["payments_line_h"]

        page1_canvas.setFont("Helvetica-Bold", f["size"])
        page1_canvas.drawString(header_x, header_y, "Details of Payments Received")

        page1_canvas.setFont("Helvetica", f["size"])
        y = row_y
        for p in data.get("payments", []):
            line = f"{p.get('pay_type', 'Payment')}-{p.get('date', '')}-{p.get('location', '')}".rstrip('-')
            page1_canvas.drawString(row_x, y, line)
            page1_canvas.drawRightString(amt_x, y, f"{p['amount']:,.2f}")
            y -= line_h

        page1_canvas.setFont("Helvetica-Bold", f["size"])
        page1_canvas.drawString(row_x, y, COORDS["payments_total_label"])
        page1_canvas.drawRightString(amt_x, y, f"{data['total_payments']:,.2f}")


    def _draw_usage_full_from_page2(self, data):
        sections = [s for s in data.get("usage_sections", []) if s["subsections"]]
        if not sections:
            return

        # Start on a fresh new page
        self.new_page()
        y_state = {"y": 750}
        y_min = 60
        line_h = 9

        # Narrow box positioning
        col_x = [50, 130, 190]
        amount_x = 300
        box_right = 305
        total_label_x = 45

        # Font sizes
        font_row = 7
        font_header = 7
        font_subtotal = 7
        font_grand_total = 8
        font_section_header = 9

        def get_last_numeric_value(row):
            for val in reversed(row):
                if val is None:
                    continue
                val_str = str(val).replace(",", "").strip()
                if not val_str:
                    continue
                try:
                    return float(val_str)
                except (ValueError, TypeError):
                    continue
            return 0.0

        def sum_rows_reliable(rows):
            return sum(get_last_numeric_value(row) for row in rows if row)

        def draw_table(sub, rows, print_header_line, show_section_header,
                       section_label, section_phone):
            if y_state["y"] < y_min:
                self.new_page()
                y_state["y"] = 780

            if show_section_header:
                header = f'Detailed Usage Charges for {section_label}'
                if section_phone:
                    header += f' {section_phone}'
                self.text(45, y_state["y"], header, size=font_section_header, bold=True)
                y_state["y"] -= line_h * 1.4

            if print_header_line and sub["label"]:
                self.text(45, y_state["y"], sub["label"], size=font_row, bold=True)
                y_state["y"] -= line_h * 1.2

            headers = sub["headers"]
            combine = len(headers) >= 2 and headers[0] == 'Date' and headers[1] == 'Time'
            disp_headers = ['Date &Time'] + headers[2:] if combine else headers

            if print_header_line:
                box_y = y_state["y"] - 2
                box_h = line_h + 2
                try:
                    self.canvas.rect(col_x[0] - 3, box_y,
                                     box_right - (col_x[0] - 3), box_h)
                except AttributeError:
                    pass

                for i, h in enumerate(disp_headers[:len(col_x) + 1]):
                    x = col_x[i] if i < len(col_x) else amount_x
                    self.text(x, y_state["y"], h, size=font_header, bold=True,
                              align="right" if i == len(disp_headers) - 1 else "left")
                y_state["y"] -= line_h

            for row in rows:
                if y_state["y"] < y_min:
                    self.new_page()
                    y_state["y"] = 780

                disp = [f"{row[0]}  {row[1]}"] + row[2:] if combine else list(row)
                charge_val = get_last_numeric_value(row)

                for i in range(min(len(disp) - 1, len(col_x))):
                    x = col_x[i]
                    self.text(x, y_state["y"], str(disp[i]), size=font_row)

                self.number(amount_x, y_state["y"], charge_val, decimals=3,
                            size=font_row, align="right")

                y_state["y"] -= line_h

            return sum_rows_reliable(rows)

        for section in sections:
            for sub_idx, sub in enumerate(section["subsections"]):
                sub_total = sum_rows_reliable(sub["rows"])
                draw_table(sub, sub["rows"],
                           print_header_line=True,
                           show_section_header=(sub_idx == 0),
                           section_label=section["label"],
                           section_phone=section["phone"])
                self.text(total_label_x, y_state["y"], f'Total for {sub["label"]}',
                          size=font_subtotal, bold=True)
                self.number(amount_x, y_state["y"], sub_total, decimals=3,
                            size=font_subtotal, bold=True, align="right")
                y_state["y"] -= line_h * 1.3

            section_grand_total = section.get("grand_total", 0)
            if not section_grand_total:
                section_grand_total = sum(sum_rows_reliable(s["rows"])
                                           for s in section["subsections"])

            self.text(total_label_x, y_state["y"],
                      f'Total Usage Charges for {section["label"]}',
                      size=font_grand_total, bold=True)
            self.number(amount_x, y_state["y"], section_grand_total, decimals=3,
                        size=font_grand_total, bold=True, align="right")
            y_state["y"] -= line_h * 2


    def _draw_page_indicators(self, data, total_pages):
        f = FONTS["page_indicator"]
        inv_f = FONTS["invoice_no_p2"]

        for page_idx in range(len(self.canvases)):
            canvas = self.canvases[page_idx][1]

            if page_idx == 0:
                x, y = COORDS["page_indicator_p1"]
            else:
                x, y = COORDS["page_indicator_p2"]

            text = f"{page_idx + 1} of {total_pages}"
            canvas.setFont("Helvetica", f["size"])
            canvas.drawRightString(x, y, text)

            if page_idx > 0:
                x, y = COORDS["page_invoice_no_p2"]
                canvas.setFont("Helvetica-Bold", inv_f["size"])
                canvas.drawString(x, y, f'Invoice No.{data["invoice_number"]}')