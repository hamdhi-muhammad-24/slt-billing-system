from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth import repository as auth_repo
from app.auth.pdf_tokens import verify_pdf_token
from app.auth.schemas import UserOut
from app.auth.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
_404 = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserOut:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        raise _401

    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise _401

    user = auth_repo.get_user_by_id(db, int(user_id_str))
    if user is None or not user.is_active:
        raise _401

    return UserOut(
        id=user.id,
        email=user.email,
        role=payload["role"],
        customer_id=payload.get("customer_id"),
    )


def require_admin(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_account_owner(
    account_id: int,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if current_user.role == "ADMIN":
        return current_user
    owner_customer_id = auth_repo.get_customer_id_for_account(db, account_id)
    if owner_customer_id is None or current_user.customer_id != owner_customer_id:
        raise _404
    return current_user


def require_invoice_owner(
    invoice_id: int,
    current_user: UserOut = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    if current_user.role == "ADMIN":
        return current_user
    owner_customer_id = auth_repo.get_customer_id_for_invoice(db, invoice_id)
    if owner_customer_id is None or current_user.customer_id != owner_customer_id:
        raise _404
    return current_user


def require_pdf_access(
    invoice_id: int,
    pdf_token: str | None = Query(None, alias="token"),
    bearer: str | None = Depends(_oauth2_optional),
    db: Session = Depends(get_db),
) -> None:
    """Allow access via a valid signed PDF token OR an authorized Bearer JWT."""
    # Path 1: signed short-lived PDF token
    if pdf_token is not None:
        try:
            claims = verify_pdf_token(pdf_token)
        except Exception:
            pass  # invalid/expired — fall through to bearer check
        else:
            if claims.get("invoice_id") != invoice_id:
                raise _404
            return

    # Path 2: Bearer JWT with ownership check
    if bearer is None:
        raise _401
    try:
        payload = decode_access_token(bearer)
    except InvalidTokenError:
        raise _401
    user_id_str: str | None = payload.get("sub")
    if not user_id_str:
        raise _401
    user = auth_repo.get_user_by_id(db, int(user_id_str))
    if user is None or not user.is_active:
        raise _401
    if payload.get("role") == "ADMIN":
        return
    customer_id: int | None = payload.get("customer_id")
    owner_customer_id = auth_repo.get_customer_id_for_invoice(db, invoice_id)
    if owner_customer_id is None or customer_id != owner_customer_id:
        raise _404
