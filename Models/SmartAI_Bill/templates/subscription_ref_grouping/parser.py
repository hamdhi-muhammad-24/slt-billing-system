import os

def parse_subscription_ref_grouping(file_path: str) -> dict:
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
        # Nested structure
        "subscription_refs": [],  # [{ref, detail_name, products: [{label, charges}], recurring_subtotal, oneoff_subtotal}]
        # Top-level subtotals (specific to Sheet 23)
        "rental_subtotal": 0,     # $SLT_RENTAL_SUBTOTAL
        "usage_subtotal": 0,      # $SLTEVENTSSUBTOTAL
        "taxes": [],
        "total_charges": 0,
        "payments": [],
        "total_payments": 0,
        "source_filename": os.path.basename(file_path),
        "customer_segment": "",
        "slt_vat_reg": "",
        "customer_vat_reg": "",
    }

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        current_sub_ref = None
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
            rest = parts[1].strip() if len(parts) > 1 else ''
            tokens = key_val.split(None, 1)

            if len(tokens) < 2:
                continue

            key = tokens[0].upper()
            value = tokens[1].strip()

            # Standard fields
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
                    data['address_lines'].append(value)
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

            elif key == 'SLTSUBSCRIPTIONREF':
                current_sub_ref = {
                    "ref": value,
                    "detail_name": "",
                    "products": [],
                    "recurring_subtotal": 0,
                    "oneoff_subtotal": 0,
                }
                data['subscription_refs'].append(current_sub_ref)

            elif key == 'SLTSUBSDETAIL':
                all_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                if current_sub_ref is not None and len(all_parts) >= 2:
                    current_sub_ref['detail_name'] = all_parts[1]

            elif key == 'SLTPRODUCTLABEL':
                current_product = {
                    "label": value,
                    "charges": [],
                }
                if current_sub_ref is not None:
                    current_sub_ref['products'].append(current_product)
                else:
                    default_ref = {
                        "ref": "",
                        "detail_name": "",
                        "products": [current_product],
                        "recurring_subtotal": 0,
                        "oneoff_subtotal": 0,
                    }
                    data['subscription_refs'].append(default_ref)
                    current_sub_ref = default_ref

                if not data['telephone_number'] and value.isdigit() and len(value) >= 10:
                    data['telephone_number'] = value

            elif key == 'SLTPRODLABELDET':
                all_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                if current_product and len(all_parts) >= 6:
                    prefix = all_parts[1].split('_')[-1].strip()
                    suffix = all_parts[2].strip()
                    description = f"{prefix} {suffix}".strip()
                    flag = all_parts[5].strip().upper()
                    if flag == 'P':
                        description += " [Rental]"
                    elif flag == 'O':
                        description += " [One Time]"
                    current_product['charges'].append({
                        'description': description,
                        'amount': _to_float(all_parts[0]),
                    })

            elif key == 'SLTPRODLABELUSAGEDET':
                all_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                if current_product and len(all_parts) >= 2:
                    current_product['charges'].append({
                        'description': all_parts[0],
                        'amount': _to_float(all_parts[1]),
                    })

            elif key == 'SLTPRODLABELDISCDET':
                all_parts = [value] + [p.strip() for p in rest.split('|') if p.strip()]
                if current_product and len(all_parts) >= 2:
                    current_product['charges'].append({
                        'description': all_parts[0],
                        'amount': _to_float(all_parts[1]),
                    })

            elif key == 'SLTSUBSLVL_RECURR_SUBTOTAL':
                if current_sub_ref:
                    current_sub_ref['recurring_subtotal'] = _to_float(value)

            elif key == 'SLTSUBSLVL_ONEOFF_SUBTOTAL':
                if current_sub_ref:
                    current_sub_ref['oneoff_subtotal'] = _to_float(value)

            elif key == 'SLT_RENTAL_SUBTOTAL':
                data['rental_subtotal'] = _to_float(value)

            elif key == 'SLTEVENTSSUBTOTAL':
                data['usage_subtotal'] = _to_float(value)

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
                pending_payment = {'date': value, 'pay_type': pay_type, 'location': '', 'amount': amount}
                data['payments'].append(pending_payment)

            elif key == 'SLT_PAYMENT_LOCATION':
                if data['payments']:
                    data['payments'][-1]['location'] = value

            elif key == 'ACC_CUSTOMER_SEGMENT':
                data['customer_segment'] = value

            elif key == 'INVOICINGCOVATREG':
                data['slt_vat_reg'] = value
            elif key == 'CUSTOMERVATREF':
                data['customer_vat_reg'] = value

    # Set badge from customer type
    from core.customer_type_mapper import get_badge
    data['badge'] = get_badge(data['customer_type'])

    return data


def _to_float(value):
    if value is None or value == "":
        return 0
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return 0