from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.errors import NotFound
from app.api.schemas import AccountOut, InvoiceOut, Page, PaymentOut, ServiceAccountOut, UsageSummaryOut
from app.auth.dependencies import require_account_owner
from app.auth.schemas import UserOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get(
    "/{account_id}",
    response_model=AccountOut,
    summary="Get account",
    description="Returns a single billing account by ID.",
)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_account_owner),
) -> AccountOut:
    out = crud.get_account(db, account_id)
    if out is None:
        raise NotFound(f"Account {account_id} not found")
    return out


@router.get(
    "/{account_id}/service-accounts",
    response_model=list[ServiceAccountOut],
    summary="Service accounts",
    description=(
        "Returns the voice, broadband, and PeoTV sub-accounts "
        "attached to a billing account."
    ),
)
def list_service_accounts(
    account_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_account_owner),
) -> list[ServiceAccountOut]:
    if crud.get_account(db, account_id) is None:
        raise NotFound(f"Account {account_id} not found")
    return crud.list_service_accounts(db, account_id)


@router.get(
    "/{account_id}/invoices",
    response_model=Page[InvoiceOut],
    summary="List invoices for account",
    description=(
        "Paginated invoices for a billing account, newest first. "
        "Line items are omitted in the list; fetch the individual invoice for full detail."
    ),
)
def list_invoices_for_account(
    account_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_account_owner),
) -> Page[InvoiceOut]:
    if crud.get_account(db, account_id) is None:
        raise NotFound(f"Account {account_id} not found")
    items, total = crud.list_invoices_for_account(db, account_id, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/{account_id}/payments",
    response_model=list[PaymentOut],
    summary="Payments for account",
    description="Returns all payment records for a billing account, newest first.",
)
def list_payments_for_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_account_owner),
) -> list[PaymentOut]:
    if crud.get_account(db, account_id) is None:
        raise NotFound(f"Account {account_id} not found")
    return crud.list_payments_for_account(db, account_id)


@router.get(
    "/{account_id}/usage",
    response_model=list[UsageSummaryOut],
    summary="Usage summary for account",
    description="Returns monthly usage summaries for every service on the account.",
)
def list_usage_for_account(
    account_id: int,
    period: str | None = Query(None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_account_owner),
) -> list[UsageSummaryOut]:
    if crud.get_account(db, account_id) is None:
        raise NotFound(f"Account {account_id} not found")
    return crud.list_usage_for_account(db, account_id, period=period)


@router.get(
    "/{account_id}/usage/history",
    response_model=list[UsageSummaryOut],
    summary="Usage history for account",
    description="Returns recent monthly usage summaries, newest first.",
)
def list_usage_history_for_account(
    account_id: int,
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_account_owner),
) -> list[UsageSummaryOut]:
    if crud.get_account(db, account_id) is None:
        raise NotFound(f"Account {account_id} not found")
    return crud.list_usage_for_account(db, account_id, months=months)
