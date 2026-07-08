"""Product Label Grouping Renderer (Sheet 22)."""
import os
from datetime import datetime
from core.pdf_renderer import BaseRenderer
from templates.product_label_grouping.config import COORDS, CHARGES_TABLE, FONTS

TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PDF = os.path.join(TEMPLATE_DIR, "layout.pdf")


class ProductLabelGroupingRenderer(BaseRenderer):
    """Renders bill with charges grouped by product label + subtotals."""

    def __init__(self):
        super().__init__(TEMPLATE_PDF)

    def render(self, data):
        self._draw_header(data)
        self._draw_customer(data)
        self._draw_badge(data)
        self._draw_generation_id(data)
        self._draw_summary_boxes(data)
        self._draw_page1_footer(data)

        # === FLOWING: Charges + Adjustments + Taxes (Total Charges independent) ===
        y = self._draw_charges_with_subtotals(data["product_labels"])
        y = self._draw_adjustments(data, y)
        y = self._draw_taxes_only(data, y)

        # === INDEPENDENT SECTIONS ===
        self._draw_total_charges_fixed(data)
        self._draw_payments_fixed(data)

        # Page indicators (LAST so we know total pages)
        total_pages = self.page_count()
        self._draw_page_indicators(data, total_pages)

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
        self.text(*COORDS["customer_name"], data["customer_name"],
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

    def _draw_badge(self, data):
        f = FONTS["badge"]
        self.text(*COORDS["badge_text"], data["badge"], size=f["size"], bold=f["bold"])

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
        # Use business_name if available, else customer_name
        slip_customer_name = data.get("business_name") or data["customer_name"]
        self.text(*COORDS["slip_customer"], slip_customer_name, size=f["size"])
        self.text(*COORDS["slip_account"], data["account_number"], size=f["size"])

    def _draw_charges_with_subtotals(self, product_labels):
        """Draw charges with recurring/one-off subtotals per product (BPR12).
        Returns final Y so flowing sections can continue."""
        y = CHARGES_TABLE["page1_y_start"]
        if not product_labels:
            return y

        f = FONTS["product_label"]
        fc = FONTS["charge_line"]
        fs = FONTS["subtotal"]
        y_min = CHARGES_TABLE["page1_y_min"]
        line_h = CHARGES_TABLE["line_h"]
        label_gap = CHARGES_TABLE["product_label_y_gap"]

        for product in product_labels:
            # Calculate space needed
            subtotal_lines = 0
            if product["recurring_subtotal"]:
                subtotal_lines += 1
            if product["oneoff_subtotal"]:
                subtotal_lines += 1
            space_needed = (label_gap + len(product["charges"]) * line_h
                            + subtotal_lines * line_h)

            if y - space_needed < y_min:
                self.new_page()
                y = CHARGES_TABLE["otherpage_y_start"]
                y_min = CHARGES_TABLE["otherpage_y_min"]

            # Product label
            self.text(CHARGES_TABLE["product_label_x"], y,
                       product["label"], size=f["size"], bold=f["bold"])
            y -= label_gap

            # Charges
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

            # Recurring subtotal (skip if 0 — BPR12)
            if product["recurring_subtotal"]:
                self.text(CHARGES_TABLE["desc_x"] + CHARGES_TABLE["subtotal_indent"], y,
                           "Product Recurring Subtotal", size=fs["size"], bold=fs["bold"])
                self.number(CHARGES_TABLE["subtotal_x"], y,
                             product["recurring_subtotal"], size=fs["size"],
                             bold=fs["bold"], align="right")
                y -= line_h

            # One-off subtotal (skip if 0 — BPR12)
            if product["oneoff_subtotal"]:
                self.text(CHARGES_TABLE["desc_x"] + CHARGES_TABLE["subtotal_indent"], y,
                           "Product One-off Subtotal", size=fs["size"], bold=fs["bold"])
                self.number(CHARGES_TABLE["subtotal_x"], y,
                             product["oneoff_subtotal"], size=fs["size"],
                             bold=fs["bold"], align="right")
                y -= line_h

        return y

    def _draw_adjustments(self, data, y):
        """Continues from charges."""
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
        """Taxes & Levies flowing — Total Charges is independent."""
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
        """Total Charges for the Period — INDEPENDENT position."""
        page1_canvas = self.canvases[0][1]
        f = FONTS["total"]

        x = COORDS["total_charges_label_x"]
        y = COORDS["total_charges_label_y"]
        amt_x = COORDS["total_charges_amount_x"]

        page1_canvas.setFont("Helvetica-Bold", f["size"])
        page1_canvas.drawString(x, y, "Total Charges for the Period")
        page1_canvas.drawRightString(amt_x, y, f"{data['total_charges']:,.2f}")

    def _draw_payments_fixed(self, data):
        """Details of Payments Received — INDEPENDENT position."""
        page1_canvas = self.canvases[0][1]

        f = FONTS["payments"]
        header_x = COORDS["payments_header_x"]
        header_y = COORDS["payments_header_y"]
        row_x = COORDS["payments_row_x"]
        row_y = COORDS["payments_row_start_y"]
        amt_x = COORDS["payments_amount_x"]
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