"""SMS body template — must stay under 160 chars."""
from __future__ import annotations


def render_sms_body(invoice, account) -> str:
    period = invoice.period_start.strftime("%b %Y")
    amount = f"{invoice.total_payable:,.2f}"
    due    = invoice.due_date.strftime("%d %b %Y")
    body   = f"SLT: Your bill for {period} is Rs {amount}. Due: {due}. Acc: {account.account_number}."
    # Truncate defensively — period/amount expansion should never exceed 160 in practice
    return body[:160]
