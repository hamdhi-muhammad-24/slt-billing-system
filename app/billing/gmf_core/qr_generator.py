"""LankaQR generator — matches SLT's actual QR format."""
import qrcode
from io import BytesIO

_STATIC_PAYONLINE_QR_CACHE = None


def generate_static_payonline_qr(size=200):
    """Static payonline QR (cached)."""
    global _STATIC_PAYONLINE_QR_CACHE
    if _STATIC_PAYONLINE_QR_CACHE is None:
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=2,
        )
        qr.add_data("https://slt.lk/en/payonline")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size))

        buf = BytesIO()
        img.save(buf, format="PNG")
        _STATIC_PAYONLINE_QR_CACHE = buf.getvalue()

    return BytesIO(_STATIC_PAYONLINE_QR_CACHE)


def calculate_crc(data: str) -> str:
    """CRC-16/CCITT-FALSE for EMVCo QR."""
    crc = 0xFFFF
    for ch in data:
        crc ^= (ord(ch) << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
    return f"{crc:04X}"


def build_slt_qr_payload(
        account_number: str,
        total_charges: float,
        merchant_id: str = "00281601000000050001490001145829",
        merchant_category_code: str = "4900",
        currency_code: str = "144",
        country_code: str = "LK",
        merchant_name: str = "SRI LANKA TELECOM PLC",
        merchant_city: str = "COLOMBO 01",
        additional_ref: str = "40025829",
) -> str:
    def field(tag, value):
        return f"{tag}{len(value):02d}{value}"

    parts = []

    # 00: Payload Format Indicator (always "01")
    parts.append(field("00", "01"))

    # 01: Point of Initiation Method
    # 11 = static (same QR always for this invoice)
    # 12 = dynamic (changes each time)
    parts.append(field("01", "11"))

    # 26: Merchant Account Info — RAW merchant ID (no sub-tags)
    # Sample: 263200281601000000050001490001145829 5204
    parts.append(field("26", merchant_id))

    # 52: Merchant Category Code (4900 = Utilities)
    parts.append(field("52", merchant_category_code))

    # 53: Currency Code (144 = LKR as used by SLT)
    parts.append(field("53", currency_code))

    # 54: Transaction Amount (total charges for period, NOT total payable)
    if total_charges is not None and total_charges > 0:
        parts.append(field("54", f"{total_charges:.2f}"))

    # 58: Country Code
    parts.append(field("58", country_code))

    # 59: Merchant Name
    parts.append(field("59", merchant_name))

    # 60: Merchant City
    parts.append(field("60", merchant_city))

    # 62: Additional Data
    # Sub-tag 05 = account number (bill reference, 10 chars)
    # Sub-tag 07 = additional reference (8 chars)
    clean_account = account_number.replace(" ", "")
    additional_data = field("05", clean_account)
    if additional_ref:
        additional_data += field("07", additional_ref)
    parts.append(field("62", additional_data))

    # 63: CRC (calculated over everything + "6304")
    payload_no_crc = "".join(parts) + "6304"
    crc = calculate_crc(payload_no_crc)
    parts.append(field("63", crc))

    return "".join(parts)


def generate_qr_image(payload: str, size: int = 200):
    """Generate QR code image from payload."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_slt_qr(
        account_number: str,
        total_charges: float,
        size: int = 200,
        additional_ref: str = "40025829",
):
    payload = build_slt_qr_payload(
        account_number=account_number,
        total_charges=total_charges,
        additional_ref=additional_ref,
    )
    return generate_qr_image(payload, size=size), payload