"""Parser for Invoice of Summary (Sheet 18, BILLSTYLE=18)."""
import os
import re

_ITEM_TAG_RE = re.compile(r'^(BSTARTITEM|BENDITEM|EVSOURCE|EVENTSTEXT|EVENTHEADING|EVENT|TSTARTEVENT|TENDEVENT|SLTITEMGRANDTOTAL)_(\d+)$')
_ITEMGROUP_RE = re.compile(r'^ITEMGROUPNAME_1_(\d+)$')
_GROUPSUBTOTAL_RE = re.compile(r'^ITEMGROUPSUBTOTAL_(\d+)_(\d+)$')


def parse_invoice_of_summary(file_path: str) -> dict:
    data = {
        "telephone_number": "",
        "account_number": "",
        "invoice_number": "",
        "billing_date": "",
        "billing_period_start": "",
        "billing_period_end": "",
        "payment_due_date": "",
        "customer_name": "",
        "position": "",
        "department": "",
        "business_name": "",
        "address_lines": [],
        "zip_code": "",
        "badge": "ENTERPRISE",
        "customer_type": "",
        "balance_bf": 0,
        "payments_received": 0,
        "charges_period": 0,
        "total_payable": 0,
        "rental_subtotal": 0,
        "usage_subtotal": 0,
        "discounts": [],
        "taxes": [],
        "total_charges": 0,
        "charge_groups": [],
        "payments": [],
        "total_payments": 0,
        "source_filename": os.path.basename(file_path),
        "customer_segment": "",
        "slt_vat_reg": "",
        "customer_vat_reg": "",
        "usage_sections": [],
    }

    raw_address = {}

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        current_group = None
        current_product = None
        in_subscription_ref = False
        usage_sections = {}
        current_item_id = None
        current_subsection = None
        pending_subsection_label = None
        last_closed_subsection = None

        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('DOCEND'):
                break

            if line.startswith('BSTARTSLTSUBSCRIPTIONREF'):
                in_subscription_ref = True
                continue
            if line.startswith('BENDSLTSUBSCRIPTIONREF'):
                in_subscription_ref = False
                current_group = None
                continue
            if line.startswith('BSTARTSLTNOSUBSCRIPTIONREF'):
                in_subscription_ref = False
                current_group = None
                continue

            if '|' not in line:
                continue

            parts = line.split('|', 1)
            key_val = parts[0].strip()
            rest = parts[1] if len(parts) > 1 else ''
            tokens = key_val.split(None, 1)

            if not tokens:
                continue

            key = tokens[0].upper()
            value = tokens[1].strip() if len(tokens) > 1 else ''

            m = _ITEM_TAG_RE.match(key)
            if m:
                tag, item_id = m.group(1), m.group(2)
                if tag == 'BSTARTITEM':
                    current_item_id = item_id
                    usage_sections[item_id] = {
                        'phone': '', 'label': '', 'subsections': [],
                        'grand_total': 0, 'aggregated_totals': {},
                    }
                elif tag == 'BENDITEM':
                    current_item_id = None
                elif tag == 'EVSOURCE':
                    if item_id in usage_sections:
                        usage_sections[item_id]['phone'] = value
                elif tag == 'EVENTSTEXT':
                    if item_id in usage_sections:
                        usage_sections[item_id]['label'] = value
                elif tag == 'EVENTHEADING':
                    cols = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                    current_subsection = {'label': pending_subsection_label or '', 'headers': cols, 'rows': [], 'subtotal': 0}
                    pending_subsection_label = None
                elif tag == 'EVENT':
                    if current_subsection is not None:
                        row = [value] + [p.strip() for p in rest.split('|')]
                        current_subsection['rows'].append(row)
                elif tag == 'TENDEVENT':
                    if current_subsection is not None and item_id in usage_sections:
                        usage_sections[item_id]['subsections'].append(current_subsection)
                        last_closed_subsection = current_subsection
                    current_subsection = None
                elif tag == 'SLTITEMGRANDTOTAL':
                    gparts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                    if item_id in usage_sections and len(gparts) >= 2:
                        usage_sections[item_id]['grand_total'] = _to_float(gparts[1])
                continue

            gm = _ITEMGROUP_RE.match(key)
            if gm:
                pending_subsection_label = value
                continue

            sm = _GROUPSUBTOTAL_RE.match(key)
            if sm:
                tag_n = sm.group(1)
                if last_closed_subsection is not None:
                    # Existing CDR-style path (e.g. International): subtotal
                    # belongs to the subsection that just closed via TENDEVENT.
                    sub_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                    if len(sub_parts) >= 3:
                        last_closed_subsection['subtotal'] = _to_float(sub_parts[2])
                    last_closed_subsection = None
                elif tag_n == '1' and current_item_id is not None and pending_subsection_label:
                    # No-CDR aggregate pattern (Domestic Voice Usage's
                    # Off Net / On Net). "value" IS the amount itself here
                    # (e.g. "ITEMGROUPSUBTOTAL_1_5 256.00|..."). Sum every
                    # occurrence of this label across the whole billing
                    # period (it repeats once per day).
                    amt = _to_float(value)
                    totals = usage_sections[current_item_id]['aggregated_totals']
                    totals[pending_subsection_label] = totals.get(pending_subsection_label, 0) + amt
                    pending_subsection_label = None
                # tag_n == '2' is the combined daily total (Off Net + On Net
                # for that single day) -- intentionally ignored, it would
                # double-count against the per-label sums above.
                continue

            if len(tokens) < 2:
                continue

            if key == 'ACCOUNTNO':
                data['account_number'] = value
            elif key == 'BILLREF':
                data['invoice_number'] = value
            elif key == 'INVOICEACTUALDATE':
                data['billing_date'] = value
            elif key == 'INVOICESTART':
                data['billing_period_start'] = value
            elif key == 'INVOICEEND':
                data['billing_period_end'] = value
            elif key == 'PAYMENTDUEDATE':
                data['payment_due_date'] = value
            elif key == 'CUSTOMERTYPE':
                data['customer_type'] = value

            elif key == 'ADDRESSNAME':
                data['customer_name'] = value
            elif key == 'POSITION':
                data['position'] = value
            elif key == 'DEPARTMENT':
                data['department'] = value
            elif key == 'BUSINESSNAME':
                data['business_name'] = value
            elif key in ('ADDRESS1', 'ADDRESS2', 'ADDRESS3', 'ADDRESS4', 'ADDRESS5'):
                if value:
                    raw_address[key] = value
            elif key == 'ZIPCODE':
                data['zip_code'] = value

            elif key == 'BALFWD':
                data['balance_bf'] = _to_float(value)
            elif key == 'ACCBALPAYTOT':
                data['payments_received'] = _to_float(value)
                data['total_payments'] = _to_float(value)
            elif key == 'CHARGES':
                data['charges_period'] = _to_float(value)
                data['total_charges'] = _to_float(value)
            elif key == 'NEWBAL':
                data['total_payable'] = _to_float(value)

            elif key == 'SLT_RENTAL_SUBTOTAL':
                data['rental_subtotal'] = _to_float(value)
            elif key == 'SLTEVENTSSUBTOTAL':
                data['usage_subtotal'] = _to_float(value)

            elif key == 'SLTDISCDETAIL':
                all_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                if len(all_parts) >= 2:
                    amt = _to_float(all_parts[0])
                    if amt:
                        data['discounts'].append({
                            'description': all_parts[1],
                            'amount': -amt,
                        })

            elif key == 'SLTSUBSCRIPTIONREF':
                current_group = {"ref": value, "products": []}
                data['charge_groups'].append(current_group)

            elif key == 'SLTPRODUCTLABEL':
                current_product = {"label": value, "charges": []}
                if current_group is not None:
                    current_group['products'].append(current_product)
                else:
                    current_group_standalone = {"ref": "", "products": [current_product]}
                    data['charge_groups'].append(current_group_standalone)
                if not data['telephone_number'] and value.isdigit() and len(value) >= 10:
                    data['telephone_number'] = value

            elif key == 'SLTPRODLABELDET':
                raw = rest.split('|')
                all_parts = [value] + raw
                if current_product and len(all_parts) > 6:
                    prefix = all_parts[1].split('_')[-1].strip()
                    suffix = all_parts[2].split('_')[-1].strip()
                    description = f"{prefix} {suffix}".strip()
                    flag = all_parts[5].strip().upper() if len(all_parts) > 5 else ''
                    if flag == 'P':
                        description += " [Rental]"
                        extra = all_parts[9].strip() if len(all_parts) > 9 else ''
                        count = all_parts[8].strip() if len(all_parts) > 8 else ''
                        if count and extra:
                            description += f" [{count} {extra}]"
                    current_product['charges'].append({
                        'description': description,
                        'amount': _to_float(all_parts[0]),
                    })

            elif key == 'SLTPRODLABELUSAGEDET':
                raw = [p.strip() for p in rest.split('|') if p.strip()]
                all_parts = [value] + raw
                if current_product and len(all_parts) >= 2:
                    desc = all_parts[0].strip()
                    if desc.startswith('P_'):
                        desc = desc[2:]
                    current_product['charges'].append({
                        'description': desc,
                        'amount': _to_float(all_parts[1]),
                    })

            elif key == 'SLTPRODLABELDISCDET':
                raw = [p.strip() for p in rest.split('|') if p.strip()]
                all_parts = [value] + raw
                if current_product and len(all_parts) >= 2:
                    amt = _to_float(all_parts[1])
                    if amt:
                        current_product['charges'].append({
                            'description': all_parts[0].strip(),
                            'amount': -amt,
                        })

            elif key == 'SLTTAXCODE':
                all_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                if len(all_parts) >= 4:
                    data['taxes'].append({
                        'name': all_parts[0],
                        'amount': _to_float(all_parts[3]),
                    })

            elif key == 'ACCBALPAYDET':
                raw_parts = [value] + rest.split('|')
                amount = _to_float(raw_parts[3]) if len(raw_parts) > 3 else 0
                pay_type = raw_parts[13].strip() if len(raw_parts) > 13 and raw_parts[13].strip() else 'Payment'
                data['payments'].append({'date': value, 'pay_type': pay_type, 'location': '', 'amount': amount})
            elif key == 'SLT_PAYMENT_LOCATION':
                if data['payments']:
                    data['payments'][-1]['location'] = value

            elif key == 'ACC_CUSTOMER_SEGMENT':
                data['customer_segment'] = value
            elif key == 'INVOICINGCOVATREG':
                data['slt_vat_reg'] = value
            elif key == 'CUSTOMERVATREF':
                data['customer_vat_reg'] = value

    for k in ('ADDRESS5', 'ADDRESS2', 'ADDRESS3', 'ADDRESS4', 'ADDRESS1'):
        if k in raw_address:
            data['address_lines'].append(raw_address[k])

    from core.customer_type_mapper import get_badge
    data['badge'] = get_badge(data['customer_type'])

    for sec in usage_sections.values():
        agg = sec.pop('aggregated_totals', {})
        for label, amt in agg.items():
            sec['subsections'].append({'label': label, 'headers': [], 'rows': [], 'subtotal': amt})

    data['usage_sections'] = list(usage_sections.values())
    return data


def _to_float(value):
    if value is None or value == "":
        return 0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0