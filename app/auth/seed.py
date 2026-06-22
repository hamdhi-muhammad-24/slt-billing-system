"""
Auth seed — idempotent.

Creates:
  1 ADMIN  : admin@slt.lk
  3 CUSTOMER users, each linked to an existing seeded customer via
  customers.user_id (the FK direction already present in the schema).

Run:  python -m app.auth.seed
"""

from __future__ import annotations

import sys

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.logging import configure_logging, get_logger
from app.db.base import SessionLocal
from app.db.models import Customer, UserRole
from app.auth.models import User
from app.auth import repository as auth_repo
from app.auth.security import hash_password

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Dev credentials — synthetic, printed at seed time, never stored plaintext
# ---------------------------------------------------------------------------

_ADMIN_EMAIL    = "admin@slt.lk"
_ADMIN_PASSWORD = "Admin@SLT2024!"

# (email, dev_password, account_number_to_link)
_CUSTOMER_USERS: list[tuple[str, str, str]] = [
    ("pavithim@slt-customer.lk", "Cust@2024!Pavi", "004 152 4075"),
    ("ruwan@slt-customer.lk",    "Cust@2024!Ruwa", "002 341 8901"),
    ("kumari@slt-customer.lk",   "Cust@2024!Kuma", "003 517 2243"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upsert_user(
    db: Session,
    email: str,
    password: str,
    role: UserRole,
) -> User:
    """Return existing user or create a new one. Never re-hashes if present."""
    existing = auth_repo.get_user_by_email(db, email)
    if existing:
        log.debug("skip user  %s (already exists)", email)
        return existing
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.flush()
    log.info("create user  %s  role=%s", email, role.value)
    return user


def _link_customer(db: Session, user_id: int, account_number: str) -> None:
    """Set customers.user_id for the customer who owns *account_number*."""
    customer_id = auth_repo.get_customer_id_by_account_number(db, account_number)
    if customer_id is None:
        log.warning("account %s not found — run app.db.seed first", account_number)
        return
    # Check already linked
    existing_uid = db.scalar(
        select(Customer.user_id).where(Customer.id == customer_id)
    )
    if existing_uid == user_id:
        log.debug("skip link  customer %d already linked to user %d", customer_id, user_id)
        return
    db.execute(
        update(Customer)
        .where(Customer.id == customer_id)
        .values(user_id=user_id)
    )
    log.info("link  customer %d -> user %d  (account %s)", customer_id, user_id, account_number)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    configure_logging()
    log.info("seeding auth users …")

    with SessionLocal() as db:
        try:
            # Admin
            _upsert_user(db, _ADMIN_EMAIL, _ADMIN_PASSWORD, UserRole.ADMIN)

            # Customer users
            for email, password, account_number in _CUSTOMER_USERS:
                user = _upsert_user(db, email, password, UserRole.CUSTOMER)
                _link_customer(db, user.id, account_number)

            db.commit()
        except Exception:
            db.rollback()
            log.exception("auth seed failed — rolled back")
            sys.exit(1)

    # Print dev credentials — intentional, dev-only
    print("\n── Dev credentials (synthetic, never use in production) ──")
    print(f"  ADMIN     {_ADMIN_EMAIL:<30}  password: {_ADMIN_PASSWORD}")
    for email, password, acct in _CUSTOMER_USERS:
        print(f"  CUSTOMER  {email:<30}  password: {password}  (account {acct})")
    print()
    log.info("auth seed done")


if __name__ == "__main__":
    main()
