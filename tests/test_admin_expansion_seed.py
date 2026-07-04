from app.db import seed


def test_demo_seed_targets_100_customers() -> None:
    assert seed._TARGET_CUSTOMER_COUNT == 100
    assert len(seed._ACCOUNTS) + len(seed._CUSTOMER_PROFILES) == 100


def test_hamdhi_seed_profile_exists() -> None:
    profiles = [p for p in seed._CUSTOMER_PROFILES if p[4] == "hamdhimuhammad024@gmail.com"]
    assert len(profiles) == 1
    _, first, last, _, email, mobile, *_ = profiles[0]
    assert f"{first} {last}" == "Muhammad Hamdhi"
    assert email == "hamdhimuhammad024@gmail.com"
    assert mobile == "0774991051"


def test_invoice_template_seed_records_are_18_system_templates() -> None:
    assert len(seed._INVOICE_TEMPLATE_SEEDS) == 18
    assert seed._INVOICE_TEMPLATE_SEEDS[0]["template_code"] == "SLT_TEMPLATE_01"
    assert seed._INVOICE_TEMPLATE_SEEDS[-1]["template_code"] == "SLT_TEMPLATE_18"
