from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import User
from app.db.models import Account, Customer


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_customer_id_for_user(db: Session, user_id: int) -> int | None:
    """Return the customers.id whose user_id matches, or None for admins."""
    return db.scalar(select(Customer.id).where(Customer.user_id == user_id))


def get_customer_id_by_account_number(db: Session, account_number: str) -> int | None:
    """Used by the auth seed to find a customer via their unique account number."""
    return db.scalar(
        select(Account.customer_id).where(Account.account_number == account_number)
    )
