# PDF.md — E-Bill Layout (ReportLab)

Spec for the PDF generator (ROADMAP Steps 5–7). Target = the new **"INVOICE"** layout
(sample 1 + the PNG). Renders from a `Bill` object (see BILLING.md). Page = **A4**
(595 × 842 pt). Margins ≈ 36 pt.

> Build strategy: use the **canvas** (absolute positioning) for fixed regions (header,
> summary boxes, payment slip) and **platypus** Tables/Flowables for the variable charges and
> usage sections so they paginate. Start Step 5 with hard-coded Sample-1 values; wire to the
> `Bill` object in Step 6; add overflow in Step 7.

---

## 1. Colors (approximate — sample exact values from the real logo/asset)

```
HEADER_BLUE   = #14529E   # top band + payment-slip field labels
LABEL_BLUE    = #2E6DB4   # "TELEPHONE NUMBER", field captions
TEAL_FILL     = #16A7C2   # filled summary boxes (Total payable, Due date)
TEAL_BORDER   = #16A7C2
GREEN_BORDER  = #4CAF50   # customer address box border
BOX_BORDER    = #BFC9D4   # light grey field boxes
TEXT          = #1A1A1A
MUTED         = #6B7280
```

---

## 2. Fonts (MUST register, or Sinhala/Tamil = tofu boxes)

Place TTFs in `app/pdf/assets/fonts/`. Register at module load:

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("Noto",        "assets/fonts/NotoSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Noto-Bold",   "assets/fonts/NotoSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("NotoSinhala", "assets/fonts/NotoSansSinhala-Regular.ttf"))
pdfmetrics.registerFont(TTFont("NotoTamil",   "assets/fonts/NotoSansTamil-Regular.ttf"))
```

Latin → `Noto`/`Noto-Bold`. Sinhala summary labels → `NotoSinhala`. Tamil (notice/slip) →
`NotoTamil`. Each summary box caption is bilingual (Sinhala line + English line) — draw the
two lines in their respective fonts.

---

## 3. Page regions (top → bottom)

### A. Header band  (full width, ~70 pt tall, HEADER_BLUE)
- Left: **"INVOICE"** large white bold; beside it "Sri Lanka Telecom PLC / Lotus Road,
  P.O Box 503, Colombo 01." (small white).
- Right: **SLT MOBITEL logo** (`assets/logo.png`) + "The Connection".

### B. Identity block  (two columns under header)
**Left column** — caption (LABEL_BLUE) + value in a light box (BOX_BORDER):
- TELEPHONE NUMBER (value inline, no box)
- Account Number · Invoice Number · Billing Date · Billing Period (each boxed)

**Right column**:
- "`1 of N`" top-right.
- Customer box (GREEN_BORDER): "Rev. Mr/Mrs." + name + address lines.
- **Barcode** (Code128, see §5) under the customer box.
- Service-label banner (e.g. "HOME") in a blue/teal bar.
- **QR code** + MYSLT app icon + "www.slt.lk/payonline".
- Reference line (small muted): e.g. `407493_1-1-02-1-LKR-105-5-BIL_1.5...` + service tag.

### C. SUMMARY OF INVOICE  (section title + a row of 5 rounded boxes)
Boxes left→right with operators between them:
`Balance B/F`  −  `Payments received`  +  `Charges for the period`  =  **`Total payable`**  **`Payment due date`**
- First three: white fill, BOX/TEAL border. Last two: **TEAL_FILL** background, white text.
- Each box: bilingual caption (small) on top, value (bold, larger) below. Amounts 2dp.
- Map: `summary.balance_bf`, `summary.payments_received`, `summary.charges_for_period`,
  `summary.total_payable`, `bill.due_date`.

### D. DETAILS OF CHARGES FOR THE PERIOD  (platypus — variable height)
- Title rule; right-aligned `(Rs.)` header.
- **For each `ServiceGroup`:** print the `service_number` as a bold heading row, then each
  `BillLine` indented: description (left) + amount (right, 2dp). Split-period rentals show
  their date range in the description. Negative discounts print with a leading `-`.
- **Taxes & Levies:** heading + each `tax_line` amount.
- Horizontal rule, then **Total Charges for the Period** (bold) + `charges_total + taxes_total`
  right-aligned.

### E. Details of Payments Received  (small block)
"Details of Payments Received" + one row per payment (`description  date  amount`) +
"Total Payments Received" + sum.

### F. Usage detail (optional v1, from PNG)  → `usage_records`
"Detailed Usage Charges for Additional Channels" table: columns
`Date & Time | Service Type | Description | Charge`, then a total row. Platypus table.

### G. Legal line
Small italic: "This electronic form of the bill has the same legal recognition, effect,
validity or enforceability as the original form of the bill, in terms of the Electronic
Transactions Act No.19 of 2006."

### H. Notice box (sample 1 — optional)
Red-bordered box, trilingual arrears notice. Skip in v1 unless needed.

### I. Tear-off payment slip  (dashed separator across full width)
Bottom section, mirrors header fields. Field labels in HEADER_BLUE boxes:
- Left grid: Telephone No. · Invoice No. · Customer Name · Account No. · Credit Card No.
  (empty boxes) · Card Expiry Date (DD MM YYYY boxes).
- Right grid: "Payment Slip" tag · barcode · checkboxes Cash / Cheques / Credit Card ·
  Name of Bank · Cheque Number · Amount · Customer's Signature · Date · LANKAQR mark · QR ·
  SLT MOBITEL logo.

---

## 4. Layout skeleton

```python
def render_bill(bill: Bill, out_path: str):
    c = canvas.Canvas(out_path, pagesize=A4)
    draw_header(c)                 # A
    draw_identity(c, bill)         # B  (incl. barcode + QR)
    draw_summary(c, bill.summary, bill.due_date)   # C
    y = draw_charges(c, bill)      # D  (returns current y; may add pages)
    y = draw_payments(c, bill, y)  # E
    draw_legal(c)                  # G
    draw_payment_slip(c, bill)     # I  (anchored to page bottom)
    c.showPage(); c.save()
```
For Step 7, route D/E/F through platypus Frames so overflow flows to page 2+, repeating a
slim header and updating "Page X of N".

---

## 5. Barcode & QR

```python
# Code128 barcode (invoice number) -> PNG/drawing
from barcode import Code128
from barcode.writer import ImageWriter
Code128(bill.invoice_number, writer=ImageWriter()).write(buf)

# QR -> pay URL + invoice ref
import qrcode
qrcode.make(f"https://www.slt.lk/payonline?inv={bill.invoice_number}")
```
v1: placeholder content is fine (ROADMAP decision). Wire real spec later.

---

## 6. Formatting rules

- Amounts: 2dp with thousands separators, right-aligned (e.g. `1,154.84`, `-38.71`).
- Dates: `DD/MM/YYYY` (matches the bills).
- Never recompute totals in the renderer — print the values the engine put on `Bill`.
- Output file: `output/{account_number}_{period}.pdf` (sanitise spaces).

---

## 7. Acceptance (Steps 5–7)

- Step 5: hard-coded Sample-1 PDF visually matches the sample; Sinhala labels render (no tofu);
  barcode + QR present.
- Step 6: `generate-one` produces the same PDF from the `Bill` object end-to-end.
- Step 7: a long bill paginates with correct "Page X of N" and repeated header.
