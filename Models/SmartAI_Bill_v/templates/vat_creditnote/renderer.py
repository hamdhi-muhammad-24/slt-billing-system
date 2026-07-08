import os

from core.pdf_renderer import BaseRenderer

from templates.vat_creditnote.config import (
    COORDS,
    ADDRESS_BOX,
    ADJUSTMENT_TBL,
    CHARGE_PERIOD_X,
    CHARGE_PERIOD_Y,
    FONTS
)


TEMPLATE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_PDF = os.path.join(
    TEMPLATE_DIR,
    "layout.pdf"
)


class VATCreditNoteRenderer(BaseRenderer):

    def __init__(self):
        super().__init__(TEMPLATE_PDF)


    def render(self, data):

        self._draw_header(data)

        # Main account number barcode
        self._draw_barcode(data)

        self._draw_address(data)

        self._draw_vat_lines(data)

        self._draw_extra_lines(data)

        self._draw_summary(data)

        self._draw_adjustments(data)

        self._draw_charge_period(data)



    def _draw_header(self, data):

        self.text(
            *COORDS["document_title"],
            "Tax Credit Note",
            size=FONTS["title"]["size"]
        )


        self.text(
            *COORDS["account_number"],
            data.get("account_number", ""),
            size=FONTS["header"]["size"]
        )


        self.text(
            *COORDS["invoice_number"],
            data.get("invoice_number", ""),
            size=FONTS["header"]["size"]
        )


        self.text(
            *COORDS["billing_date"],
            data.get("billing_date", ""),
            size=FONTS["header"]["size"]
        )


        self.text(
            *COORDS["bill_period"],
            data.get("bill_period", ""),
            size=FONTS["header"]["size"]
        )



    def _draw_barcode(self, data):

        account_number = data.get("account_number", "")

        if not account_number:
            return


        self.draw_barcode(
            *COORDS["barcode"],
            account_number,
            width=COORDS["barcode_width"],
            height=COORDS["barcode_height"]
        )



    def _draw_address(self, data):

        y = ADDRESS_BOX["y"]


        lines = [
            data.get("address_line1"),
            data.get("address_line2"),
            data.get("address_line3"),
            data.get("address_line4"),
            data.get("address_line5"),
            data.get("address_line6"),
            data.get("address_line7"),
            data.get("address_line8"),
            data.get("address_line9"),
            data.get("address_line10"),
        ]


        for line in lines:

            if line:

                self.text(
                    ADDRESS_BOX["x"],
                    y,
                    line,
                    size=ADDRESS_BOX["font_size"]
                )

                y -= ADDRESS_BOX["line_h"]



    def _draw_vat_lines(self, data):

        self.text(
            *COORDS["below_address_line1"],
            data.get("below_address_line1", ""),
            size=FONTS["footer"]["size"]
        )


        self.text(
            *COORDS["below_address_line2"],
            data.get("below_address_line2", ""),
            size=FONTS["footer"]["size"]
        )



    def _draw_extra_lines(self, data):

        self.text(
            *COORDS["header_extra_line1"],
            data.get("header_extra_line1", ""),
            size=FONTS["footer"]["size"]
        )


        self.text(
            *COORDS["header_extra_line2"],
            data.get("header_extra_line2", ""),
            size=FONTS["footer"]["size"]
        )



    def _draw_summary(self, data):

        summary = data.get("summary", {})


        self.number(
            *COORDS["balance_bf"],
            summary.get("balance_bf", 0),
            align="center"
        )


        self.number(
            *COORDS["payments_received"],
            summary.get("payments_received", 0),
            align="center"
        )


        self.number(
            *COORDS["arrears"],
            summary.get("arrears", 0),
            align="center"
        )


        self.number(
            *COORDS["adjustment_value"],
            summary.get("adjustment_value", 0),
            align="center"
        )


        self.number(
            *COORDS["total_payable"],
            summary.get("total_payable", 0),
            bold=True,
            align="center"
        )



    def _draw_adjustments(self, data):

        y = ADJUSTMENT_TBL["y_start"]


        items = data.get("adjustments", [])


        self.text(
            ADJUSTMENT_TBL["desc_x"],
            y,
            "ADJUSTMENTS",
            bold=True
        )


        y -= ADJUSTMENT_TBL["line_h"]



        for item in items:

            desc = item.get("description", "")

            amount = item.get("amount", 0)


            self.text(
                ADJUSTMENT_TBL["desc_x"] +
                ADJUSTMENT_TBL["indent"],
                y,
                desc,
                size=ADJUSTMENT_TBL["font_size"]
            )


            self.number(
                ADJUSTMENT_TBL["amount_x"],
                y,
                amount,
                size=ADJUSTMENT_TBL["font_size"],
                align="right"
            )


            y -= ADJUSTMENT_TBL["line_h"]




    def _draw_charge_period(self, data):

        self.number(
            CHARGE_PERIOD_X,
            CHARGE_PERIOD_Y,
            data.get("charge_for_period", 0),
            size=9,
            bold=True,
            align="right"
        )