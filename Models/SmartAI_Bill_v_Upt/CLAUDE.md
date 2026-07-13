# CLAUDE.md - vat_enterprise Bill Renderer

## 0. Mission (read first, do not skip)

Take a **GMF bill file** (SLT/SLTMobitel bill export, pipe-delimited), extract the
values, and **stamp them onto `vat_enterprise/layout.pdf`** so the final PDF matches the
golden reference **pixel-for-pixel in structure and alignment**.

- **Input (GMF):** Test on BOTH bills:
  1. `520326_1-1-02-1-LKR-101-1-BILL-NONRED_1.7` (VAT-registered, 2-page, account 000201075X)
  2. The GMF for account `0033944500` (VAT-registered, 3-page, Kangaroo Cabs)
- **Template (do NOT redraw):** `vat_enterprise/layout.pdf` (2-page A4, 595 x 842 pt)
- **Golden outputs (match these):** `000201075X_VAT_ENTERPRISE.pdf` and
  `0033944500_VAT_ENTERPRISE.pdf`

The template contains static chrome you keep (header band, SLTMobitel logos, the five
trilingual summary bubbles, empty field boxes, the address box, the "DETAILS OF CHARGES"
header through `(Rs.)`, the payment slip with LANKAQR). You stamp dynamic values on top.
Do not redraw logos, boxes, or bubbles.

**CRITICAL - the template is NOT purely static.** `layout.pdf` has several labels **baked
at fixed y-positions in the middle of page 1** that DO NOT MOVE when your content grows:
"Total Charges for the Period" (y≈591, top-origin), "Details of Payments Received"
(y≈617), "Detailed Usage Charges..." (y≈655), and the Date/Dialled/Duration/Charge table
header (y≈677). Your charge block starts at y≈385 and grows downward. As soon as it is
tall enough it **overlaps these baked labels** - which is the current bug (two text layers
in the same y-range). This gets worse the longer the bill; it is NOT a scaling-factor
issue, so do not chase a scale factor.

**Chosen fix (Route 1 - mask and redraw):** mask out the baked mid-page band and redraw
those labels dynamically at the correct y after the charges. See section 5A. Keep the one
template file; do not create a second template.

---

## 1. Hard rules (non-negotiable)

1. **Never edit anything outside `vat_enterprise/` without asking me first.** This
   includes `core/`, the caller/entry point, and any shared module. If a fix seems to
   require an outside edit (e.g. `core.bill_common`), STOP, explain what and why, and wait
   for my answer. Prefer making the module self-contained inside `vat_enterprise/`.
2. **Do NOT run `git commit`, `git add`, or `git push`.** Not once. Leave the working
   tree dirty for me to review.
3. **Present a plan and wait for my approval before any large change** (new files,
   refactors, deleting functions). Small in-place bug fixes on the list in section 4 can
   proceed directly.
4. **When done, write a build note** at `vat_enterprise/BUILD_NOTE.md` (see section 8).
   Do not commit it.

---

## 2. Current state (what exists, what's broken)

- `vat_enterprise/parser.py` - parses the GMF into a `data` dict. **Has bugs (section 4).**
- `vat_enterprise/renderer.py` - **misnamed.** It is a duplicate of `parser.py` plus a
  dangerous `remove_zeros()` wrapper. It does NOT render. There is currently **no PDF
  drawing code** in the package.
- `vat_enterprise/config.py` - holds `COORDS`, `ADDRESS_BOX`, `CHARGES_TBL`, `PAGE_W/H`.
  **It is orphaned** - nothing in the package imports it. `PAGE_W/H` (595.5 x 842.25)
  matches the template, so the coordinate map is calibrated to `layout.pdf`.
- `vat_enterprise/layout.pdf` - the 2-page template background. Page 1 = full chrome.
  Page 2 = continuation chrome ("Invoice No." + "N of M").
- **Missing:** the overlay/draw engine, and `PhoneNumberFromNoSubRefBlock`
  (imported from `core.bill_common`).

**First task before touching anything: run a discovery pass.** Report back:
- Does an overlay/draw function exist anywhere reachable? (`grep -rn "show_pdf_page\|drawString\|reportlab\|fitz\|canvas"`)
- Where does `core.bill_common` live and can it be imported? If it cannot, tell me before
  proceeding - do not stub it silently.

---

## 3. Architecture to build (Approach A - overlay, keep the template)

Pipeline:

```
GMF file ──parse──► data dict ──overlay──► layout.pdf background ──► final PDF
```

Use **PyMuPDF (fitz)**. For each output page:
1. Create a new page and paint the correct template page as the background via
   `page.show_pdf_page(rect, template_doc, template_page_index)`.
   - Page 1 body -> template page 0. Overflow pages -> template page 1 (continuation).
2. Stamp **fixed-position fields** (header, summary bubbles, payment slip) using absolute
   coordinates from `config.COORDS`. Wire `config.py` in - it is the single source of
   truth for positions. Do not hardcode coordinates in the drawer.
3. **Mask the baked mid-page band** (section 5A) so the template's fixed labels can't
   collide with your content.
4. Render **variable-length sections with a y-cursor and page breaks** (sections 5A + 5),
   redrawing the mid-page labels at their computed y.
5. After all pages are laid out, stamp the real page numbers: **"N of M"** where M is the
   final page count. The template has **baked** page markers - "1 of 2" (y≈84, top) and
   "N2:n 2" (y≈726) on page 1, plus "2 of 2" on the continuation page. **Mask these baked
   markers** (redaction or white box) before stamping the real "N of M", or you get the
   doubling seen in the last output ("2 of 2 of 2").

### 3.1 Coordinate origin - ONE convention, no exceptions (current failure point)

**This is the bug in the latest output.** fitz draws with a **top-left origin**;
`config.COORDS` values are **bottom-left origin**. The mid-page code is top-origin and
correct, but the `config.COORDS`-driven stamps are being drawn **without conversion**, so
they are vertically mirrored - e.g. `slt_vat_reg = (360, 749.5)` landed at y≈748 (bottom
of page, on the payment slip) instead of y≈92 (top, next to its label).

**Rule:** define ONE helper and route EVERY vertical coordinate through it. No raw config
y-value may ever reach a fitz draw call.

```python
def yt(y_pdf):          # bottom-origin (config) -> fitz top-origin
    return PAGE_H - y_pdf
```

- Every fixed-field stamp: `page.insert_text((x, yt(y_pdf)), ...)`.
- The mid-page y-cursor: pick ONE convention for the whole drawer and stick to it. If the
  cursor is top-origin, convert the config band bounds once with `yt()` and compare in
  top-origin. Do not mix.
- **Symptom to recognize:** any field appearing near the *opposite* edge from where it
  belongs (VAT number at the bottom, footer at the top) = a missing/ double `yt()`. Audit
  every draw call for exactly one conversion.

Do not "nudge" individual coordinates to fix this - that hides the inconsistency and
breaks on the next field. Fix the convention once, then calibrate x-offsets against the
golden PDF.

---

## 4. Parser fixes (verified against the real GMF - do these)

All line indices below are **0-based `line.split("|")` positions**, verified against the
actual bill file.

1. **Taxes are all dropped (off-by-one).** In the `TAXCODE` branch, the amount is read
   from `tax_parts[14]`, which is always `0.00`. The real amount is at **index 13**.
   Example line:
   `TAXCODE 193|VAT-18%|3|With-Prorate|3838.69|...|690.96|0.00|...` -> 690.96 is index 13.
   Fix the index. Also reconsider the `if amount > 0` filter - a legit 0.00 tax line
   should still be decided intentionally, not dropped by accident.
   Result must show: CESS 68.13, Recovery in lieu of SSCL 95.82, Telecommunication
   Levy-15% 335.22, VAT-18% 690.96.

2. **Date range over-appended + product-name junk.** `SLTPRODLABELDET` currently appends
   `[Rental] (start-end)` **whenever** start/end exist, and leaks the raw prefix from
   part[2]. Example:
   `SLTPRODLABELDET  950.00|AB_Megaline|z Sales End_Biz SLT Phone|37|38|P|01/09/2025|30/09/2025|SAPROD|0|`
   currently becomes `"Megaline z Sales End_Biz SLT Phone [Rental] (01/09/2025-30/09/2025)"`.
   The golden output is just **`"Megaline Biz SLT Phone [Rental]"`** with **no** date range.
   Rules (from Rule Set page 18):
   - Show the date range **only if it differs from the bill period.** Full-period items
     (01/09 - 30/09) get no range. Only genuinely prorated items (e.g. PeoTV split into
     01-27 / 28-29 / 30-30) show their sub-range.
   - Clean the product name: strip the `XX_` prefix from **both** part[1] and part[2],
     avoid duplicating `[Rental]`.

3. **`remove_zeros()` deletes real content.** It recursively strips any value `== 0`,
   which removes legit zero-amount line items (the golden output shows
   **"Triple VAS Bundle Charge Free [Rental]"**, a 0.00 `SLTPRODLABELDET`) and can delete
   top-level keys the drawer expects -> `KeyError`. **Remove this function** and handle
   display filtering explicitly at render time instead.

4. **Discounts must render inline, not in a separate list.** `SLTPRODLABELDISCDET`
   currently goes to `data["discounts"]`. The golden output shows the discount inline
   inside the phone group: `"Discount Domestic Calls-FixedLine  -400.00"` under
   `0522267554`. Keep discounts attached to their group so they render in place.

Do not "fix" anything not on this list without flagging it first.

---

## 5A. Mid-page dynamic zone - THE FIX for the overlap bug

This is the root cause of the current text-on-text collision. Implement it before section 5.

**Concept:** page 1 has three zones. Top and bottom come from the template unchanged. The
**middle owns everything from below `(Rs.)` down to just above the legal disclaimer**, and
your code fully controls it - including the four labels that are currently baked into the
template.

**Zone boundaries on page 1 (top-origin y, PAGE_H = 842). Calibrate against the golden
PDF; these are measured starting points, not final):**
- Keep template above: header + summary bubbles + "DETAILS OF CHARGES" + `(Rs.)`.
  The `(Rs.)` line ends at y≈379.
- **Dynamic band = y 385 (top) down to y 715 (bottom).** Below 715 sits the legal
  disclaimer ("This electric form of the bill...") and then the payment slip - both stay
  from the template.
- In bottom-origin (the `config.COORDS` convention): band top ≈ 457, band floor ≈ 127.

**Step 1 - mask the baked labels.** After painting the template background but before
drawing content, cover the baked mid-page text so it cannot show through. Two options,
pick the robust one:
  - Preferred: use fitz **redaction** on the template's own text in that y-band
    (`page.add_redact_annot(rect); page.apply_redactions()`) so "Total Charges for the
    Period", "Details of Payments Received", "Detailed Usage Charges...", and the baked
    "Date &Time / Dialled No. / Duration / Charge" header are removed cleanly. Do this on
    the template doc/page you copy from, or on the output page after `show_pdf_page`.
  - Fallback: paint an opaque **white rectangle** over the band `(x0=45, y0=385,
    x1=560, y1=715)`. The band is pure white in the template, so this leaves no artifact.
    Watch the thin separator rules baked around those labels - if a rule line survives at
    a fixed y, mask it too, because you will redraw the lines dynamically.

**Step 2 - redraw the labels dynamically, in order, after the charges end:**
1. Charge groups + taxes (section 5) - draw top-down, get the final `y`.
2. `"Total Charges for the Period"` + the total amount, on the next line after taxes,
   with its separator rule - at the **computed** y, never a fixed one.
3. `"Details of Payments Received"` + payment rows.
4. `"Detailed Usage Charges for P_Domestic Voice Usage"` + `"SLT-Mobile"` + the
   `Date &Time | Dialled No. | Duration | Charge` header, then the `EVENT_11` rows.

If the running `y` would cross the band floor (715 on page 1), break to a new page per
section 5 BEFORE drawing the next block, and re-emit the table header on the new page.

**Note on `config.CHARGES_TBL`:** `y_min` is currently 250 (bottom-origin), which stops
far too early and is part of why layout is cramped. The real floor is ≈127 bottom-origin
(the 715 top-origin line). Update it, and drive the band from config, not magic numbers.

---

## 5. Variable-length rendering (flow + page breaks)

Three sections grow and must flow with page breaks:

- **Charges block** - grouped under `SLTPRODUCTLABEL` headers (phone/service numbers:
  `0522267554`, `HT2267554`). Group header printed once, then its rental / usage /
  discount lines indented beneath.
- **Taxes & Levies** - printed after the last charge group, before "Total Charges".
- **Detailed usage table** - `EVENT_11` rows (Date&Time | Dialled No. | Duration | Charge),
  60+ rows here, flowing onto page 2 (and page 3+ if needed). Note the event tag in this
  file is **`EVENT_11`**, with an `EVENTS` summary line and `EVENTHEADING_11` header.

Flow logic:
1. Maintain a `y` cursor starting at the band top (`CHARGES_TBL["y_start"]` ≈ 457
   bottom-origin / 385 top-origin).
2. Before each row, if the cursor reaches the band floor (≈127 bottom-origin / 715
   top-origin, per 5A), **start a new page**: paint the continuation template background
   (template page 1), mask its baked labels the same way (5A), reset `y` to the top of
   that page's content frame, re-emit the table header, and continue.
3. Track total pages; stamp "N of M" on every page at the end.
4. Collision with "Total Charges", the payment slip, and the baked labels is now
   structurally prevented by 5A (mask) + the band floor - not by hoping the content fits.

---

## 5B. y-cursor MUST advance after every draw (current overlap bug)

**This is the active bug in the latest output.** Visible on page 3 of
`0033944500_VAT_ENTERPRISE.pdf`: three separate sections - "Cancel Payment /
Physical payment-12/09/2025 -2,800.00", "Detailed Usage Charges for Domestic Voice
Usage 0112026200", and "Total Usage Charges for Domestic Voice Usage 122,598.600" - are
all rendered at the **same y-position** (~y 63, top-origin), producing garbled overlapping
text.

The page break fires correctly (content moves from page 2 to page 3), but after the
cursor resets to the new page's top-of-content y, **each subsequent section draws at that
same reset y instead of advancing past the previous section.**

**Rule - every draw function must return the new y, and the caller must use it:**

```python
def draw_section(page, y, content, ...):
    for line in content:
        if y > BAND_FLOOR:          # check BEFORE drawing
            page = new_page(...)
            y = CONTENT_TOP
        page.insert_text((x, y), line, ...)
        y += line_height
    return page, y                  # BOTH - page may have changed

# Caller - chain page AND y through every section:
page, y = draw_total_charges(page, y, total)
page, y = draw_payments(page, y, payments)
page, y = draw_cancel_payments(page, y, cancel_payments)   # if present
page, y = draw_usage_header(page, y, phone_number)
page, y = draw_usage_rows(page, y, events)
page, y = draw_usage_total(page, y, usage_total)
```

**Each section gets `y` from the previous section's return value.** No section may use
a hardcoded y, a class-level reset y, or the page-break reset y without first checking
whether another section already drew below it. This is the single fix that prevents the
overlap.

**Test case:** the `0033944500` bill (3 pages). After fixing, page 3 must show:
- "Cancel Payment" section clearly above
- "Detailed Usage Charges for Domestic Voice Usage 0112026200" clearly below it
- "Total Usage Charges for Domestic Voice Usage  122,598.600" clearly below that
- NO overlapping text anywhere

---

## 5C. Vertical line - must start at Total Charges, span all usage pages

**Current bug:** the vertical line (x≈308, 0.5pt, black) that forms the right edge of the
usage detail table currently appears on the EVENT page only. On `000201075X` it starts on
page 2 at y=66.9 but is missing from page 1 entirely. On `0033944500` it does not appear
on any page.

**What the golden reference shows:** the vertical line divides the post-Total-Charges
section. On the LEFT: "Details of Payments Received" + payment rows + "Total Payments
Received". On the RIGHT (or same zone on usage pages): the CDR table
(Date & Time | Dialled No. | Duration | Charge). The vertical line connects these zones
across pages.

**Rule - the vertical line starts wherever "Total Charges for the Period" is drawn and
continues through every subsequent page until the last content row:**

```
Page where Total Charges lands:
  - Draw horizontal rules above/below "Total Charges for the Period"
  - Draw vertical line at x = VERT_LINE_X (≈308), starting from y = bottom rule of
    "Total Charges" down to the content floor of that page
  
Every continuation page that has post-Total-Charges content (payments, cancel payments,
usage header, usage rows):
  - Draw vertical line at x = VERT_LINE_X from CONTENT_TOP to the last content row's y
    (or to BAND_FLOOR if content fills the page)

Last page:
  - Vertical line ends at the y of the last content row (e.g. "Total Usage Charges"),
    not at BAND_FLOOR
```

**Implementation notes:**
- Add `VERT_LINE_X` to `config.py` (≈308 pt, top-origin). Calibrate against golden.
- Track vertical line state with two variables: `vert_line_start_y` per page (set when
  Total Charges bottom rule is drawn, or CONTENT_TOP on continuation pages) and
  `vert_line_end_y` per page (updated as each post-Total-Charges section is drawn).
  After all content on a page is done, draw the line from start to end. This avoids
  drawing the line before you know the final extent.
- Set a flag `past_total_charges = True` after drawing "Total Charges for the Period".
  Every page created while this flag is True gets a vertical line.
- On page 1 of `000201075X`: Total Charges is at y≈599. The vertical line should start
  at y≈615 (below the bottom rule) and run down to y≈670 (below "Detailed Usage
  Charges..." header). Even if there are no CDR rows on page 1, the line still appears
  through the payments/usage-header zone.
- On page 2 of `000201075X`: the line runs from CONTENT_TOP to the last "Total Usage
  Charges" row. This part already works - just make sure it also draws on page 1.
- On `0033944500`: Total Charges lands on page 2 (y≈673). Vertical line starts there,
  continues through page 3. Currently missing entirely - fix by tying the line draw to
  the post-Total-Charges flow, not to a hardcoded "usage detail page" check.

---

## 6. Field map (fixed-position stamps -> COORDS keys)

Confirm each against the golden PDF; adjust `config.COORDS` if misaligned (this is
expected - calibrate, don't assume the current numbers are correct):

- `INVOICINGCOVATREG` -> `slt_vat_reg` | `CUSTOMERVATREF` -> `customer_vat_reg`
- telephone (from the no-sub-ref block) -> `telephone_number`
- `ACCOUNTNO` -> `account_number` | `BILLREF` -> `invoice_number`
- `INVOICEACTUALDATE` -> `billing_date` | period -> `bill_period`
- Summary bubbles: `BALFWD` -> balance_bf, `ACCBALPAYTOT` -> payments_received,
  `CHARGES` -> charges_period, `NEWBAL` -> total_payable,
  `PAYMENTDUEDATE` -> payment_due_date
- Address block -> `ADDRESS_BOX` (order already defined in parser)
- Payment slip: telephone, invoice, customer name, account no -> slip_* coords
- Barcodes / QR: leave the template's if already present; only stamp data-driven ones if
  the golden shows them and the template doesn't.

---

## 7. Verification loop (do this every iteration)

**Test on BOTH bills** - `000201075X` (2-page, small) AND `0033944500` (3-page, large).
A fix that works on one and breaks the other is not a fix.

1. Run the pipeline on both GMF files -> produce output PDFs.
2. Rasterize outputs and compare against golden references at the same DPI.
3. Compare page 1 field-by-field: header boxes filled, summary bubbles aligned,
   charge groups correct, all four taxes present, totals correct.
4. **Overlap check:** confirm NO text sits on top of other text on ANY page. Specifically:
   - `000201075X` page 1: "Total Charges", "Details of Payments Received", and "Detailed
     Usage Charges" must each appear on their own line, no overprinting.
   - `0033944500` page 3: "Cancel Payment" / "Physical payment-12/09/2025 -2,800.00",
     "Detailed Usage Charges for Domestic Voice Usage 0112026200", and "Total Usage
     Charges for Domestic Voice Usage 122,598.600" must be on SEPARATE lines with clear
     vertical spacing. If they overlap, the y-cursor advancement fix (5B) is broken.
     **Do this programmatically:** extract text blocks from page 3 and assert that each
     block's y0 is >= the previous block's y1. Overlapping y-ranges = fail.
5. **Vertical line check:** extract drawings from every page and verify:
   - `000201075X`: vertical line at x≈308 must exist on BOTH page 1 (starting after
     the "Total Charges" bottom rule, y≈615) AND page 2 (full height of usage table).
   - `0033944500`: vertical line must exist on page 2 (starting after "Total Charges"
     at y≈690) AND page 3 (through usage content). Currently missing on all pages.
   - **Assert programmatically:** for each page after Total Charges, check that at least
     one vertical line exists with x in range [305, 312].
6. Check numbers explicitly:
   - `000201075X`: Balance B/F 4,509.01, Payments 4,509.03, Charges 4,529.65,
     Total payable 4,529.63, Due 22/10/2025.
   - `0033944500`: Balance B/F 1,138,715.10, Payments 385,147.30, Charges 380,079.94,
     Total payable 1,133,647.74, Due 23/10/2025.
7. **Origin audit (programmatic).** Extract word coordinates and assert:
   - SLT VAT number (`294001727`) and customer VAT must have **y < 120** (top-origin).
   - Footer / page-number stamps near the bottom, not the top.
   - If any stamp is at the opposite edge from where it belongs = `yt()` flip bug.
8. Iterate on `config.COORDS` (x-offsets) until alignment is tight. Report a before/after
   screenshot pair when you think it's done.

Do not declare success on "it runs." Success = it matches the golden PDF.

---

## 7A. Mandatory post-fix validation (run this BEFORE declaring done)

After implementing fixes 5B and 5C, write and execute a Python validation script
(`vat_enterprise/validate_output.py`) that checks all three issues programmatically on
BOTH output PDFs. **Do not skip this. Do not eyeball it. Run the script and paste the
output.** If any assertion fails, fix the code and re-run until all pass.

```python
import fitz
import sys

def validate(pdf_path, expected_pages, bill_label):
    doc = fitz.open(pdf_path)
    errors = []
    
    assert doc.page_count == expected_pages, \
        f"[{bill_label}] Expected {expected_pages} pages, got {doc.page_count}"

    # ── CHECK 1: No text overlap on ANY page ──
    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        blocks = sorted(
            [(b[1], b[3], b[4].strip()) for b in page.get_text("blocks") if b[4].strip()],
            key=lambda x: x[0]  # sort by y0
        )
        for i in range(1, len(blocks)):
            prev_y0, prev_y1, prev_txt = blocks[i-1]
            curr_y0, curr_y1, curr_txt = blocks[i]
            overlap = prev_y1 - curr_y0
            if overlap > 2.0:  # allow 2pt tolerance
                errors.append(
                    f"[{bill_label}] PAGE {pg_idx+1} OVERLAP ({overlap:.1f}pt): "
                    f"'{prev_txt[:40]}' (y1={prev_y1:.1f}) overlaps "
                    f"'{curr_txt[:40]}' (y0={curr_y0:.1f})"
                )

    # ── CHECK 2: Vertical line exists on every post-Total-Charges page ──
    total_charges_page = None
    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        text = page.get_text()
        if "Total Charges for the Period" in text:
            total_charges_page = pg_idx
            break

    if total_charges_page is None:
        errors.append(f"[{bill_label}] 'Total Charges for the Period' not found on any page")
    else:
        for pg_idx in range(total_charges_page, doc.page_count):
            page = doc[pg_idx]
            vert_lines = []
            for dr in page.get_drawings():
                for item in dr["items"]:
                    if item[0] == "l":
                        p1, p2 = item[1], item[2]
                        if abs(p1.x - p2.x) < 1 and abs(p1.y - p2.y) > 30:
                            vert_lines.append((p1.x, p1.y, p2.y))
            has_vert = any(300 < x < 320 for x, _, _ in vert_lines)
            if not has_vert:
                errors.append(
                    f"[{bill_label}] PAGE {pg_idx+1}: No vertical line (x~308) found. "
                    f"Vert lines found: {vert_lines}"
                )

    # ── CHECK 3: Vertical line starts on the Total Charges page, not later ──
    if total_charges_page is not None:
        page = doc[total_charges_page]
        vert_on_tc_page = False
        for dr in page.get_drawings():
            for item in dr["items"]:
                if item[0] == "l":
                    p1, p2 = item[1], item[2]
                    if abs(p1.x - p2.x) < 1 and 300 < p1.x < 320:
                        vert_on_tc_page = True
        if not vert_on_tc_page:
            errors.append(
                f"[{bill_label}] Vertical line missing on Total Charges page "
                f"(page {total_charges_page+1}). Line must START here."
            )

    # ── CHECK 4: Page break - content doesn't spill past band floor ──
    BAND_FLOOR_TOP_ORIGIN = 715  # just above legal disclaimer
    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        for b in page.get_text("blocks"):
            y1, txt = b[3], b[4].strip()
            # Skip known bottom-of-page elements (legal text, payment slip, page numbers)
            if any(k in txt for k in ["electric form", "Telephone No", "Invoice No",
                                       "Payment Slip", "Credit Card", "Customer"]):
                continue
            if pg_idx == 0 and y1 > BAND_FLOOR_TOP_ORIGIN + 5:
                errors.append(
                    f"[{bill_label}] PAGE 1: Content below band floor at y1={y1:.1f}: "
                    f"'{txt[:50]}'"
                )

    # ── REPORT ──
    if errors:
        print(f"\n{'='*60}")
        print(f"FAIL - {bill_label}: {len(errors)} error(s)")
        print(f"{'='*60}")
        for e in errors:
            print(f"  ✗ {e}")
        return False
    else:
        print(f"  ✓ {bill_label}: ALL CHECKS PASSED")
        return True

# Run on both bills
ok1 = validate("path/to/000201075X_VAT_ENTERPRISE.pdf", 2, "000201075X")
ok2 = validate("path/to/0033944500_VAT_ENTERPRISE.pdf", 3, "0033944500")
if not (ok1 and ok2):
    print("\n⚠ FIXES INCOMPLETE - review errors above and re-run")
    sys.exit(1)
else:
    print("\n✓ All validations passed on both bills")
```

**Update the paths** to your actual output locations before running.

**If any check fails:** fix the code, regenerate both PDFs, re-run this script. Loop until
all pass. Do not proceed to the build note (section 8) with any failures outstanding.

---

## 8. Build note (write at the end, do not commit)

Create `vat_enterprise/BUILD_NOTE.md` containing:
- What changed, file by file (and why).
- The parser bugs fixed, with the old vs new index/behaviour.
- Whether the overlay engine was newly created or an existing one was fixed.
- The y-cursor advancement fix (5B): what was wrong and how it was fixed.
- The vertical line fix (5C): where it now starts/ends, which pages it spans.
- Any outside-folder dependency you hit (e.g. `core.bill_common`) and how you handled it.
- Verification results on BOTH test bills:
  - `000201075X` (2-page): fields, totals, vertical line on page 1 + 2.
  - `0033944500` (3-page): page breaks clean, no overlap on page 3, vertical line on
    pages 2 + 3, all totals correct.
- Open issues / TODOs and any coordinate values still needing calibration.

Then stop. Do not commit. Ping me for review.