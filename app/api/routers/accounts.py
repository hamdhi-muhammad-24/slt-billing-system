from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.schemas import AccountOut, InvoiceOut, Page, PaymentOut, ServiceAccountOut

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("/{account_id}", response_model=AccountOut)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
) -> AccountOut:
    out = crud.get_account(db, account_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return out


@router.get("/{account_id}/service-accounts", response_model=list[ServiceAccountOut])
def list_service_accounts(
    account_id: int,
    db: Session = Depends(get_db),
) -> list[ServiceAccountOut]:
    if crud.get_account(db, account_id) is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return crud.list_service_accounts(db, account_id)


@router.get("/{account_id}/invoices", response_model=Page[InvoiceOut])
def list_invoices_for_account(
    account_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[InvoiceOut]:
    if crud.get_account(db, account_id) is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    items, total = crud.list_invoices_for_account(db, account_id, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{account_id}/payments", response_model=list[PaymentOut])
def list_payments_for_account(
    account_id: int,
    db: Session = Depends(get_db),
) -> list[PaymentOut]:
    if crud.get_account(db, account_id) is None:
        raise HTTPException(status_code=404, detail=f"Account {account_id} not found")
    return crud.list_payments_for_account(db, account_id)
