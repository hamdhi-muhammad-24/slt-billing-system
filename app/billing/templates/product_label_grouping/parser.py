import os


def parse_product_label_grouping(file_path: str) -> dict:
    """
    Product Label Grouping (Sheet 22, BILLSTYLE=19).
    """
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
        "badge": "HOME",
        "customer_type": "",
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
    }

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        current_product = None

        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('DOCEND'):
                break

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

            # ---- Requires actual value ----
            if len(tokens) < 2:
                continue

            # Header
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

            # Customer
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

            # Product label (start of a new group)
            elif key == 'SLTPRODUCTLABEL':
                current_product = {
                    "label": value,
                    "charges": [],
                    "recurring_subtotal": 0,
                    "oneoff_subtotal": 0,
                }
                data['product_labels'].append(current_product)
                # NOTE: don't auto-set telephone from product label
                # (this template's product labels are not phone numbers)

            # Product label detail: <amount>|<code>_<shortcode>|<code2>_<suffix>|...|<flag>|<start>|<end>|...
            elif key == 'SLTPRODLABELDET':
                raw = rest.split('|')
                all_parts = [value] + raw
                if current_product and len(all_parts) > 7:
                    prefix = all_parts[1].split('_')[-1].strip()
                    suffix = all_parts[2].split('_')[-1].strip()
                    description = f"{prefix} {suffix}".strip()
                    flag = all_parts[5].strip().upper() if len(all_parts) > 5 else ''
                    start = all_parts[6].strip() if len(all_parts) > 6 else ''
                    end = all_parts[7].strip() if len(all_parts) > 7 else ''

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
                    elif flag == 'I':
                        description += " [Initiation]"
                        count = all_parts[9].strip() if len(all_parts) > 9 else ''
                        unit = all_parts[10].strip() if len(all_parts) > 10 else ''
                        count_unit = f"{count} {unit}".strip() if unit else count
                        if count_unit:
                            description += f" [{count_unit}]"
                        if start:
                            description += f" ({start}-{end})"

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

            # SUBTOTALS (specific to this template - BPR12)
            elif key == 'SLTPRODLABEL_RECURR_SUBTOTAL':
                if current_product:
                    current_product['recurring_subtotal'] = _to_float(value)

            elif key == 'SLTPRODLABEL_ONEOFF_SUBTOTAL':
                if current_product:
                    current_product['oneoff_subtotal'] = _to_float(value)

            # Taxes — sum into one total (same rule as nonvat_home)
            elif key == 'SLTTAXCODE':
                raw = [p.strip() for p in rest.split('|') if p.strip()]
                all_parts = [value] + raw
                if len(all_parts) >= 4:
                    data['taxes_total'] += _to_float(all_parts[3])

            # Adjustments
            elif key == 'ADJ':
                raw = rest.split('|')
                all_parts = [value] + raw
                if len(all_parts) > 15:
                    short_desc = all_parts[2].strip().split('_')[-1].strip()
                    reason = all_parts[15].strip()[:52]
                    desc = f"{short_desc} - {reason}" if reason else short_desc
                    data['adjustments'].append({
                        'description': desc,
                        'amount': _to_float(all_parts[3]),
                    })

            # Payments — idx0=date, idx3=amount, idx13=payment type
            elif key == 'ACCBALPAYDET':
                raw_parts = [value] + rest.split('|')
                amount = _to_float(raw_parts[3]) if len(raw_parts) > 3 else 0
                pay_type = raw_parts[13].strip() if len(raw_parts) > 13 and raw_parts[13].strip() else 'Payment'
                data['payments'].append({
                    'date': value,
                    'pay_type': pay_type,
                    'location': '',
                    'amount': amount
                })

            elif key == 'SLT_PAYMENT_LOCATION':
                if data['payments']:
                    data['payments'][-1]['location'] = value

            elif key == 'ACC_CUSTOMER_SEGMENT':
                data['customer_segment'] = value

    # Set badge from customer type
    from core.customer_type_mapper import get_badge
    data['badge'] = get_badge(data['customer_type'])

    # Try to extract telephone from account number or first meaningful product label
    if not data['telephone_number']:
        for label in data['product_labels']:
            lbl = label['label']
            # Only use if it looks like a plain phone number (10-11 digits)
            if lbl.isdigit() and 10 <= len(lbl) <= 11 and not lbl.startswith('94'):
                data['telephone_number'] = lbl
                break

    return data


def _to_float(value):
    if value is None or value == "":
        return 0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0