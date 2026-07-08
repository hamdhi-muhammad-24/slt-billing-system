"""Subscription Ref Grouping Renderer (Sheet 23)."""
import os
from core.pdf_renderer import BaseRenderer
from templates.subscription_ref_grouping.config import COORDS, CHARGES_TABLE, FONTS
from datetime import datetime

TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PDF = os.path.join(TEMPLATE_DIR, "layout.pdf")


class SubscriptionRefGroupingRenderer(BaseRenderer):
    """
    Renders bill with 3-level hierarchy:
    Subscription Ref → Product Label → Charges
    Plus subtotals at both levels + top-level rental/usage summaries.
    """

    def __init__(self):
        super().__init__(TEMPLATE_PDF)

    def render(self, data):
        self._draw_header(data)
        self._draw_customer(data)
        self._draw_vat_registration(data)
        self._draw_badge(data)
        self._draw_generation_id(data)
        self._draw_summary_boxes(data)
        self._draw_page1_footer(data)
        self._draw_hierarchy(data["subscription_refs"])
        self._draw_taxes_and_total(data)
        self._draw_payments(data)

    def _draw_header(self, data):
        f = FONTS["header"]
        self.text(*COORDS["account_number"], data["account_number"], size=f["size"])
        self.text(*COORDS["invoice_number"], data["invoice_number"], size=f["size"])
        self.text(*COORDS["billing_date"], data["billing_date"], size=f["size"])
        period = f"{data['billing_period_start']} - {data['billing_period_end']}"
        self.text(*COORDS["billing_period"], period, size=f["size"])

    def _draw_customer(self, data):
        f = FONTS["customer_name"]
        self.text(*COORDS["customer_name"], data["customer_name"],
                   size=f["size"], bold=f["bold"])
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

    def _draw_vat_registration(self, data):
        if data.get("slt_vat_reg"):
            self.text(*COORDS["slt_vat_reg_label"],
                      f"SLT VAT Registration Number: {data['slt_vat_reg']}", size=8)
        if data.get("customer_vat_reg"):
            self.text(*COORDS["customer_vat_reg_label"],
                      f"Customer VAT Registration Number: {data['customer_vat_reg']}", size=8)

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
        if data["customer_name"]:
            self.text(*COORDS["slip_customer"], data["customer_name"], size=f["size"])
        else:
            self.text(*COORDS["slip_customer"], data["business_name"], size=f["size"])
        self.text(*COORDS["slip_account"], data["account_number"], size=f["size"])

    def _draw_hierarchy(self, subscription_refs):
        """Draw 3-level hierarchy: sub_ref → product → charges.
        """
        if not subscription_refs:
            return

        f_sub = FONTS["subscription_ref"]
        f_prod = FONTS["product_label"]
        f_charge = FONTS["charge_line"]
        f_sub_total = FONTS["subtotal"]

        y = CHARGES_TABLE["page1_y_start"]
        y_min = CHARGES_TABLE["page1_y_min"]
        line_h = CHARGES_TABLE["line_h"]
        label_gap = CHARGES_TABLE["product_label_y_gap"]

        for sub_ref in subscription_refs:
            # Space estimate mirrors the draw loop exactly:
            # label_gap once (if the ref line is shown), then line_h for
            # every product label, every charge, and every subtotal line.
            space_needed = label_gap if sub_ref["ref"] else 0
            for prod in sub_ref["products"]:
                space_needed += line_h            # product label line
                space_needed += len(prod["charges"]) * line_h
            if sub_ref["recurring_subtotal"]:
                space_needed += line_h
            if sub_ref["oneoff_subtotal"]:
                space_needed += line_h

            if y - space_needed < y_min:
                self.new_page()
                y = CHARGES_TABLE["otherpage_y_start"]
                y_min = CHARGES_TABLE["otherpage_y_min"]

            if sub_ref["ref"]:
                self.text(CHARGES_TABLE["subscription_ref_x"], y,
                          sub_ref["ref"], size=f_sub["size"], bold=f_sub["bold"])
                y -= label_gap

            for product in sub_ref["products"]:
                if y < y_min:
                    self.new_page()
                    y = CHARGES_TABLE["otherpage_y_start"]
                    y_min = CHARGES_TABLE["otherpage_y_min"]

                self.text(CHARGES_TABLE["product_label_x"], y,
                          product["label"], size=f_prod["size"], bold=f_prod["bold"])
                y -= line_h

                for charge in product["charges"]:
                    if y < y_min:
                        self.new_page()
                        y = CHARGES_TABLE["otherpage_y_start"]
                        y_min = CHARGES_TABLE["otherpage_y_min"]

                    self.text(CHARGES_TABLE["desc_x"], y,
                              charge["description"], size=f_charge["size"])
                    if charge["amount"]:
                        self.number(CHARGES_TABLE["amount_x"], y,
                                    charge["amount"], size=f_charge["size"], align="right")
                    y -= line_h

            if sub_ref["recurring_subtotal"]:
                label = f'{sub_ref.get("detail_name", "").strip()} Recurring Subtotal'.strip()
                self.text(CHARGES_TABLE["desc_x"], y, label,
                          size=f_sub_total["size"], bold=f_sub_total["bold"])
                self.number(CHARGES_TABLE["amount_x"], y, sub_ref["recurring_subtotal"],
                            size=f_sub_total["size"], bold=f_sub_total["bold"], align="right")
                y -= line_h

            if sub_ref["oneoff_subtotal"]:
                label = f'{sub_ref.get("detail_name", "").strip()} One-off Subtotal'.strip()
                self.text(CHARGES_TABLE["desc_x"], y, label,
                          size=f_sub_total["size"], bold=f_sub_total["bold"])
                self.number(CHARGES_TABLE["amount_x"], y, sub_ref["oneoff_subtotal"],
                            size=f_sub_total["size"], bold=f_sub_total["bold"], align="right")
                y -= line_h

    def _draw_taxes_and_total(self, data):
        f = FONTS["taxes"]
        self.text(*COORDS["taxes_label"], "Taxes & Levies", size=f["size"], bold=True)

        y = COORDS["taxes_label"][1] - COORDS["taxes_line_h"]
        for tax in data["taxes"]:
            self.text(COORDS["taxes_label"][0], y, tax["name"], size=f["size"])
            self.number(COORDS["taxes_amount"][0], y, tax["amount"],
                        size=f["size"], align="right")
            y -= COORDS["taxes_line_h"]

        y -= 6  # breathing room before the total row
        f = FONTS["total"]
        self.text(COORDS["total_charges_label"][0], y, "Total Charges for the Period",
                  size=f["size"], bold=True)
        self.number(COORDS["total_charges_amount"][0], y, data["total_charges"],
                    size=f["size"], bold=True, align="right")

    def _draw_payments(self, data):
        f = FONTS["payments"]
        y = COORDS["payments_start"][1]
        amount_x = COORDS["payments_amount_x"]

        self.text(COORDS["payments_start"][0], y, "Details of Payments Received",
                   size=f["size"], bold=True)
        y -= COORDS["payments_line_h"]

        for p in data["payments"]:
            line = f"{p.get('pay_type', 'Payment')}-{p.get('date', '')}-{p.get('location', '')}".rstrip('-')
            self.text(COORDS["payments_start"][0], y, line, size=f["size"])
            self.number(amount_x, y, p["amount"], size=f["size"], align="right")
            y -= COORDS["payments_line_h"]

        self.text(COORDS["payments_start"][0], y, "Total Payments Received",
                   size=f["size"], bold=True)
        self.number(amount_x, y, data["total_payments"], size=f["size"], bold=True, align="right")