"""Invoice of Summary Renderer (Sheet 18, BILLSTYLE=18)."""
import os
from datetime import datetime
from core.pdf_renderer import BaseRenderer
from templates.invoice_of_summary.config import (
    COORDS, CHARGES_TABLE, USAGE_TABLE_2COL, FONTS,
)

TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PDF = os.path.join(TEMPLATE_DIR, "layout.pdf")


class InvoiceOfSummaryRenderer(BaseRenderer):

    def __init__(self):
        super().__init__(TEMPLATE_PDF)
        self._y = CHARGES_TABLE["otherpage_y_start"]
        self._on_page1 = True

    def render(self, data):
        # Fixed-position elements (page 1)
        self._draw_header(data)
        self._draw_vat_lines(data)
        self._draw_customer(data)
        self._draw_badge(data)
        self._draw_generation_id(data)
        self._draw_summary_boxes(data)
        self._draw_page1_footer(data)

        # Independent sections (page 1, fixed positions)
        self._draw_summary_of_invoice_fixed(data)
        self._draw_total_charges_fixed(data)
        self._draw_charges_in_detail_fixed(data)

        # Flowing sections (continue from charges, may overflow to page 2+)
        self._draw_discounts_and_taxes_flowing(data)
        self._draw_payments_flowing(data)
        self._draw_usage_sections(data)
        self._stamp_all_page_indicators(data)


    def _draw_header(self, data):
        f = FONTS["header"]
        self.text(*COORDS["telephone_number"], data["telephone_number"], size=f["size"])
        self.text(*COORDS["account_number"], data["account_number"], size=f["size"])
        self.text(*COORDS["invoice_number"], data["invoice_number"], size=f["size"])
        self.text(*COORDS["billing_date"], data["billing_date"], size=f["size"])
        period = f"{data['billing_period_start']} - {data['billing_period_end']}"
        self.text(*COORDS["billing_period"], period, size=f["size"])

    def _draw_vat_lines(self, data):
        f = FONTS["header"]
        if data.get("slt_vat_reg"):
            self.text(*COORDS["slt_vat_reg_label"],
                       f"SLT VAT Registration Number: {data['slt_vat_reg']}",
                       size=f["size"])
        if data.get("customer_vat_reg"):
            self.text(*COORDS["customer_vat_reg_label"],
                       f"Customer VAT Registration Number: {data['customer_vat_reg']}",
                       size=f["size"])

    def _draw_customer(self, data):
        f = FONTS["customer_name"]
        top_line = data.get("department") or data.get("customer_name", "")
        self.text(COORDS["customer_name"][0], COORDS["customer_name"][1],
                   top_line, size=f["size"], bold=True)
        if data.get("business_name"):
            self.text(COORDS["customer_name"][0], COORDS["customer_business_y"],
                       data["business_name"], size=f["size"], bold=True)
        fa = FONTS["customer_addr"]
        addr = data["address_lines"] + ([data["zip_code"]] if data["zip_code"] else [])
        self.multiline_block(
            COORDS["customer_addr_x"], COORDS["customer_addr_start"],
            addr, line_height=COORDS["customer_addr_line_h"],
            size=fa["size"], bold=fa["bold"]
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
        self.text(*COORDS["slip_customer"], data["customer_name"], size=f["size"])
        self.text(*COORDS["slip_account"], data["account_number"], size=f["size"])


    def _draw_summary_of_invoice_fixed(self, data):
        """Summary of Invoice data at FIXED position. No indent on items."""
        page1_canvas = self.canvases[0][1]

        x = COORDS["summary_x"]
        amt_x = COORDS["summary_amount_x"]
        y = COORDS["summary_y_start"]
        line_h = COORDS["summary_line_h"]
        f = FONTS["taxes"]

        page1_canvas.setFont("Helvetica", f["size"])
        page1_canvas.drawString(x, y, "Subtotal Rental and Other Charges")
        page1_canvas.drawRightString(amt_x, y, f"{data['rental_subtotal']:,.2f}")
        y -= line_h

        page1_canvas.drawString(x, y, "Subtotal Usage charges")
        page1_canvas.drawRightString(amt_x, y, f"{data['usage_subtotal']:,.2f}")
        y -= line_h

        if data["discounts"]:
            page1_canvas.setFont("Helvetica-Bold", f["size"])
            page1_canvas.drawString(x, y, "Discounts")
            y -= line_h
            page1_canvas.setFont("Helvetica", f["size"])
            for d in data["discounts"]:
                page1_canvas.drawString(x, y, d["description"])  # ← NO indent (was x + 20)
                page1_canvas.drawRightString(amt_x, y, f"{d['amount']:,.2f}")
                y -= line_h

        if data["taxes"]:
            page1_canvas.setFont("Helvetica-Bold", f["size"])
            page1_canvas.drawString(x, y, "Taxes & Levies")
            y -= line_h
            page1_canvas.setFont("Helvetica", f["size"])
            for t in data["taxes"]:
                page1_canvas.drawString(x, y, t["name"])  # ← NO indent (was x + 20)
                page1_canvas.drawRightString(amt_x, y, f"{t['amount']:,.2f}")
                y -= line_h


    def _draw_total_charges_fixed(self, data):
        """Total Charges at FIXED position on page 1 (in Summary of Invoice section)."""
        page1_canvas = self.canvases[0][1]
        f = FONTS["total"]

        x = COORDS["total_charges_label_x"]
        y = COORDS["total_charges_label_y"]
        amt_x = COORDS["total_charges_amount_x"]

        page1_canvas.setFont("Helvetica-Bold", f["size"])
        page1_canvas.drawString(x, y, "Total Charges for the Period")
        page1_canvas.drawRightString(amt_x, y, f"{data['total_charges']:,.2f}")


    def _draw_charges_in_detail_fixed(self, data):
        """Charges in Detail data starts at FIXED position.
        Template has the 'Charges in Detail' label.
        May overflow to page 2 — then becomes flowing."""
        if not data["charge_groups"]:
            return

        self._y = COORDS["charges_detail_y_start"]
        self._on_page1 = True

        for group in data["charge_groups"]:
            if group["ref"]:
                self._write_line(group["ref"], bold=True,
                                  x=CHARGES_TABLE["group_ref_x"])
            for product in group["products"]:
                self._write_line(product["label"], bold=True,
                                  x=CHARGES_TABLE["product_label_x"])
                for charge in product["charges"]:
                    self._write_line(charge["description"],
                                      amount=charge["amount"],
                                      x=CHARGES_TABLE["desc_x"])


    def _ensure_space(self, needed=None):
        needed = needed if needed is not None else CHARGES_TABLE["line_h"]
        y_min = (CHARGES_TABLE["page1_y_min"] if self._on_page1
                 else CHARGES_TABLE["otherpage_y_min"])
        if self._y - needed < y_min:
            self.new_page()
            self._on_page1 = False
            self._y = CHARGES_TABLE["otherpage_y_start"]

    def _write_line(self, text, amount=None, bold=False, x=None,
                     indent=0, size=None):
        self._ensure_space()
        f_size = size if size is not None else CHARGES_TABLE["font_size"]
        x_pos = (x if x is not None else CHARGES_TABLE["desc_x"]) + indent
        self.text(x_pos, self._y, text, size=f_size, bold=bold)
        if amount is not None:
            self.number(CHARGES_TABLE["amount_x"], self._y, amount,
                         size=f_size, bold=bold, align="right")
        self._y -= CHARGES_TABLE["line_h"]

    def _write_header_line(self, text):
        self._write_line(text, bold=True, x=CHARGES_TABLE["group_ref_x"])


    def _draw_discounts_and_taxes_flowing(self, data):
        """Discounts + Taxes + Total Charges — NO indent, box width 558."""
        grx = CHARGES_TABLE["group_ref_x"]

        if data["discounts"]:
            self._write_line("Discounts", bold=True, x=grx)
            for d in data["discounts"]:
                self._write_line(d["description"], amount=d["amount"], x=grx)

        if data["taxes"]:
            self._write_line("Taxes & Levies", bold=True, x=grx)
            for t in data["taxes"]:
                self._write_line(t["name"], amount=t["amount"], x=grx)

        # Total Charges for the Period WITH box (width=558)
        self._y -= CHARGES_TABLE["line_h"] * 0.3
        self._ensure_space(CHARGES_TABLE["line_h"] * 1.5)

        box_x = 32.5
        box_y = self._y - 3
        box_width = 528
        box_height = CHARGES_TABLE["line_h"] + 2
        try:
            self.canvas.rect(box_x, box_y, box_width, box_height)
        except AttributeError:
            pass

        f = FONTS["total"]
        self._write_line("Total Charges for the Period",
                         amount=data["total_charges"], bold=True,
                         size=f["size"], x=grx)
        self._y -= CHARGES_TABLE["line_h"] * 0.5

    def _draw_payments_flowing(self, data):
        """Payments — no indent (at group_ref_x), amount at x=290."""
        grx = CHARGES_TABLE["group_ref_x"]
        f_size = FONTS["payments"]["size"]

        # Header
        self._write_line("Details of Payments Received", bold=True, x=grx)

        # Payment lines — at group_ref_x, amount at 290
        for p in data["payments"]:
            line = (f"{p.get('pay_type', '')}-{p.get('date', '')}"
                    f"-{p.get('location', '')}").rstrip('-')
            self._ensure_space()
            self.text(grx, self._y, line, size=f_size)
            self.number(290, self._y, p["amount"], size=f_size, align="right")
            self._y -= CHARGES_TABLE["line_h"]

        # Total Payments Received — at group_ref_x, amount at 290
        self._ensure_space()
        self.text(grx, self._y, "Total Payments Received", size=f_size, bold=True)
        self.number(290, self._y, data["total_payments"],
                    size=f_size, bold=True, align="right")
        self._y -= CHARGES_TABLE["line_h"] * 1.5


    def _draw_usage_sections(self, data):
        for section in data.get("usage_sections", []):
            self._draw_one_usage_section(section)

    def _draw_one_usage_section(self, section):
        """Only draw sections with actual CDR rows.
        Totals within left column width, amount at left_amount_x."""
        subsections = section.get("subsections", [])
        subs_with_rows = [s for s in subsections if s.get("rows")]

        if not subs_with_rows:
            return

        u = USAGE_TABLE_2COL
        grx = u["left_col_x"][0]
        amt_x = u["left_amount_x"]

        for subsection in subs_with_rows:
            self._draw_usage_subsection(subsection)
            self._ensure_space()
            self.text(grx, self._y,
                      f"Total for {subsection.get('label', '')}",
                      size=u["font_size"], bold=True)
            self.number(amt_x, self._y,
                        subsection.get("subtotal", 0), decimals=3,
                        size=u["font_size"], bold=True, align="right")
            self._y -= u["line_h"]

        label = section.get("label", "")
        self._ensure_space()
        self.text(grx, self._y,
                  f"Total Usage Charges for {label}",
                  size=u["font_size"], bold=True)
        self.number(amt_x, self._y,
                    section.get("grand_total", 0), decimals=3,
                    size=u["font_size"], bold=True, align="right")
        self._y -= u["line_h"] * 1.5

    def _draw_usage_subsection(self, subsection):
        """CDR rows only. No labels (template has them).
        LEFT column: box + headers. RIGHT column: no box, no headers."""
        rows = subsection.get("rows", [])
        if not rows:
            return
        u = USAGE_TABLE_2COL

        self._ensure_space(u["line_h"] * 3)
        self._draw_usage_headers()

        i = 0
        while i < len(rows):
            self._ensure_space(u["line_h"])
            self._draw_usage_row(rows[i], side="left")
            if i + 1 < len(rows):
                self._draw_usage_row(rows[i + 1], side="right")
            self._y -= u["line_h"]
            i += 2

    def _draw_usage_headers(self):
        """LEFT column only: box + headers. Right column: nothing."""
        u = USAGE_TABLE_2COL
        headers = ["Date &Time", "Dialled No.", "Duration", "Charge"]

        # LEFT column box only
        left_start = u["left_col_x"][0]
        try:
            self.canvas.rect(
                left_start - 3, self._y - 3,
                u["left_box_right"] - left_start + 3,
                u["line_h"] + 2
            )
        except AttributeError:
            pass

        # LEFT column header text only
        for i, h in enumerate(headers):
            if i == len(headers) - 1:
                self.text(u["left_amount_x"], self._y, h,
                           size=u["font_header"], bold=True, align="right")
            else:
                self.text(u["left_col_x"][i], self._y, h,
                           size=u["font_header"], bold=True)

        # NO right column headers or box

        self._y -= u["line_h"]

    def _draw_usage_row(self, row, side):
        """Draw one CDR row on left or right column."""
        u = USAGE_TABLE_2COL
        col_x = (u["left_col_x"] if side == "left"
                 else u["right_col_x"])
        amount_x = (u["left_amount_x"] if side == "left"
                    else u["right_amount_x"])

        date = row[0] if len(row) > 0 else ""
        time = row[1] if len(row) > 1 else ""
        dialled = row[2] if len(row) > 2 else ""
        duration = row[3] if len(row) > 3 else ""
        charge = row[4] if len(row) > 4 else "0"

        self.text(col_x[0], self._y, f"{date} {time}".strip(),
                   size=u["font_size"])
        self.text(col_x[1], self._y, dialled, size=u["font_size"])
        self.text(col_x[2], self._y, duration, size=u["font_size"])
        self.number(amount_x, self._y, _safe_float(charge),
                     size=u["font_size"], align="right")


    def _stamp_all_page_indicators(self, data):
        """Draw 'X of Y' on all pages + Invoice No. on pages 2+."""
        total_pages = self.page_count()
        for page_idx in range(total_pages):
            canvas = self.canvases[page_idx][1]
            if page_idx == 0:
                canvas.setFont("Helvetica", 9)
                canvas.drawRightString(555, 750, f"1 of {total_pages}")
            else:
                canvas.setFont("Helvetica-Bold", 10)
                canvas.drawString(45, 795,
                                   f'Invoice No.{data["invoice_number"]}')
                canvas.setFont("Helvetica", 9)
                canvas.drawRightString(555, 795,
                                        f"{page_idx + 1} of {total_pages}")


def _safe_float(v):
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return 0