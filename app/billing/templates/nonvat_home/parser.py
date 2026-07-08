import os
import re

_ITEM_TAG_RE = re.compile(r'^(BSTARTITEM|BENDITEM|EVSOURCE|EVENTSTEXT|EVENTHEADING|EVENT|TSTARTEVENT|TENDEVENT|SLTITEMGRANDTOTAL)_(\d+)$')
_ITEMGROUP_RE = re.compile(r'^ITEMGROUPNAME_1_(\d+)$')
_GROUPSUBTOTAL_RE = re.compile(r'^ITEMGROUPSUBTOTAL_(\d+)_(\d+)$')


def parse_nonvat_home(file_path: str) -> dict:
    data = {
        "telephone_number": "",
        "account_number": "",
        "invoice_number": "",
        "billing_date": "",
        "billing_period_start": "",
        "billing_period_end": "",
        "payment_due_date": "",
        "customer_name": "",
        "address_lines": [],
        "zip_code": "",
        "badge": "HOME",
        "balance_bf": 0,
        "payments_received": 0,
        "charges_period": 0,
        "total_payable": 0,
        "product_labels": [],
        "adjustments": [],
        "taxes_total": 0,
        "total_charges": 0,
        "payments": [],
        "total_payments": 0,
        "source_filename": os.path.basename(file_path),
        "customer_segment": "",
        "usage_sections": [],
    }

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        current_product = None
        usage_sections = {}
        current_item_id = None
        current_subsection = None
        pending_subsection_label = None
        last_closed_subsection = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('DOCEND'):
                if line.startswith('DOCEND'):
                    break
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
                    usage_sections[item_id] = {'phone': '', 'label': '', 'subsections': [], 'grand_total': 0}
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
                        last_closed_subsection = current_subsection  # NEW: arm for the next SUBTOTAL line
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
                if last_closed_subsection is not None:
                    sub_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                    if len(sub_parts) >= 3:
                        last_closed_subsection['subtotal'] = _to_float(sub_parts[2])
                    last_closed_subsection = None  # disarm so COMP/INT/EXT variants are ignored
                continue

            if len(tokens) < 2:
                continue

            # Header fields
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

            # Customer
            elif key == 'ADDRESSNAME':
                data['customer_name'] = value
            elif key in ('ADDRESS1', 'ADDRESS2', 'ADDRESS3', 'ADDRESS4', 'ADDRESS5'):
                if value:
                    data['address_lines'].append(value)
            elif key == 'ZIPCODE':
                data['zip_code'] = value

            # Summary
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

            elif key == 'SLTPRODUCTLABEL':
                current_product = {"label": value, "charges": []}
                data['product_labels'].append(current_product)
                if not data['telephone_number'] and value.isdigit() and len(value) >= 10:
                    data['telephone_number'] = value

            elif key == 'SLTPRODLABELDET':
                raw = rest.split('|')
                all_parts = [value] + raw
                if current_product and len(all_parts) > 7:
                    prefix = all_parts[1].split('_')[-1].strip()
                    suffix = all_parts[2].split('_')[-1].strip()
                    description = f"{prefix} {suffix}".strip()
                    flag = all_parts[5].strip().upper()
                    start = all_parts[6].strip()
                    end = all_parts[7].strip()
                    if flag == 'P':
                        description += " [Rental]"
                        if start and end and (start != data['billing_period_start']
                                               or end != data['billing_period_end']):
                            description += f" ({start}-{end})"
                    elif flag == 'O':
                        count = all_parts[9].strip() if len(all_parts) > 9 else ''
                        description += " [One Time]"
                        if count:
                            description += f" [{count}]"
                        if start:
                            description += f" ({start})"
                    current_product['charges'].append({
                        'description': description,
                        'amount': _to_float(all_parts[0]),
                    })

            elif key == 'SLTPRODLABELUSAGEDET':
                raw = [p.strip() for p in rest.split('|') if p.strip()]
                all_parts = [value] + raw
                if current_product and len(all_parts) >= 2:
                    current_product['charges'].append({
                        'description': all_parts[0],
                        'amount': _to_float(all_parts[1]),
                    })

            elif key == 'SLTPRODLABELDISCDET':
                raw = [p.strip() for p in rest.split('|') if p.strip()]
                all_parts = [value] + raw
                if current_product and len(all_parts) >= 2:
                    current_product['charges'].append({
                        'description': all_parts[0],
                        'amount': -_to_float(all_parts[1]),
                    })

            elif key == 'SLTTAXCODE':
                raw = [p.strip() for p in rest.split('|') if p.strip()]
                all_parts = [value] + raw
                if len(all_parts) >= 4:
                    data['taxes_total'] += _to_float(all_parts[3])

            elif key == 'ADJ':
                raw = rest.split('|')
                all_parts = [value] + raw
                if len(all_parts) > 15:
                    short_desc = all_parts[2].strip()
                    reason = all_parts[15].strip()[:52]
                    desc = f"{short_desc} - {reason}" if reason else short_desc
                    data['adjustments'].append({
                        'description': desc,
                        'amount': _to_float(all_parts[3]),
                    })

            # Payments received -- confirmed against raw GMF:
            #   idx0=date, idx3=amount, idx13=payment type/label
            elif key == 'ACCBALPAYDET':
                all_parts = [value] + [p.strip() for p in rest.split('|')]
                if len(all_parts) > 13:
                    data['payments'].append({
                        'date': all_parts[0],
                        'location': all_parts[13],
                        'amount': _to_float(all_parts[3]),
                    })
                elif len(all_parts) >= 4:
                    data['payments'].append({
                        'date': all_parts[0],
                        'location': '',
                        'amount': _to_float(all_parts[3]),
                    })

            elif key == 'ACC_CUSTOMER_SEGMENT':
                data['customer_segment'] = value

    data['usage_sections'] = list(usage_sections.values())
    return data


def _to_float(value):
    if value is None or value == "":
        return 0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0