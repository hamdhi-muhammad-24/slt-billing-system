import re
import os

def parse_usd_open_item(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    data = {
        "account_number": "",
        "invoice_number": "",
        "billing_date": "",
        "bill_period": "",
        "invoice_amount": "",
        "payment_due_date": "",
        
        "customer_segment": "",  # NEW: Added for the top header

        "address_line1": "",
        "address_line2": "",
        "address_line3": "",
        "address_line4": "",
        "address_line5": "",
        "address_line6": "",
        "address_line7": "",
        "address_line8": "",
        "address_line9": "",
        "address_line10": "",
        "address_line11": "",

        "contact_line1": "",
        "contact_line2": "",

        "total_charges": 0.00,
        "charges": []
    }

    def extract_field(pattern, text):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""

    # ==============================
    # HEADER DETAILS
    # ==============================
    data["account_number"] = extract_field(r"ACCOUNTNO\s+([^|]+)", content)
    data["invoice_number"] = extract_field(r"BILLREF\s+([^|]+)", content)
    data["billing_date"] = extract_field(r"INVOICEACTUALDATE\s+([^|]+)", content)
    data["payment_due_date"] = extract_field(r"PAYMENTDUEDATE\s+([^|]+)", content)
    
    # NEW: Extract Customer Segment
    data["customer_segment"] = extract_field(r"ACC_CUSTOMER_SEGMENT\s+([^|]+)", content)

    start_date = extract_field(r"INVOICESTART\s+([^|]+)", content)
    end_date = extract_field(r"INVOICEEND\s+([^|]+)", content)

    if start_date and end_date:
        data["bill_period"] = f"{start_date} - {end_date}"

    # ==============================
    # ADDRESS
    # ==============================
    address_fields = [
        "ADDRESSNAME",
        "POSITION",
        "DEPARTMENT",
        "BUSINESSNAME",
        "ADDRESS1",
        "ADDRESS2",
        "ADDRESS3",
        "ADDRESS4",
        "ADDRESS5",
        "ZIPCODE",
        "COUNTRY"
    ]

    for index, field in enumerate(address_fields, start=1):
        data[f"address_line{index}"] = extract_field(rf"\b{field}\s+([^|]+)", content)

    # ==============================
    # INVOICE AMOUNT
    # ==============================
    invoice_total = extract_field(r"\bINVTOTALROUNDED\s+([^|]+)", content)
    data["invoice_amount"] = invoice_total

    try:
        data["total_charges"] = float(invoice_total.replace(",", ""))
    except ValueError:
        data["total_charges"] = 0.00

    # ==============================
    # PRODUCT DETAILS
    # ==============================
    REMOVE_LABELS = {
        "E1101261",
        "E1101883"
    }

    for line in content.splitlines():
        upper = line.upper()

        # ======================================
        # LEVEL 1 - SLTPRODUCTLABEL
        # ======================================
        if "SLTPRODUCTLABEL" in upper:
            match = re.search(r"SLTPRODUCTLABEL\s+([^|]+)", line, re.IGNORECASE)
            if match:
                product_code = match.group(1).strip()

                if product_code not in REMOVE_LABELS:
                    data["charges"].append({
                        "description": product_code,
                        "amount": None,
                        "level": 1
                    })

        # ======================================
        # LEVEL 2 - SLTPRODLABELDET
        # ======================================
        elif upper.startswith("SLTPRODLABELDET"):
            clean_line = re.sub(r"^SLTPRODLABELDET\s*", "", line, flags=re.IGNORECASE)
            parts = [p.strip() for p in clean_line.split("|")]

            if len(parts) >= 8:
                # Parse amount as a number, not a string
                raw_amount = parts[0].strip()
                try:
                    charge_amount = float(raw_amount.replace(",", ""))
                except ValueError:
                    charge_amount = None

                detail_text = parts[2]
                start = parts[6]
                end = parts[7]

                bandwidth_match = re.search(r"(\d+\s?Gbps)", detail_text, re.IGNORECASE)

                if bandwidth_match:
                    bandwidth = bandwidth_match.group(1)
                    description = f"Capacity Bearer {bandwidth} [Rental] ({start}-{end})"

                    data["charges"].append({
                        "description": description,
                        "amount": charge_amount,
                        "level": 2
                    })

    return data