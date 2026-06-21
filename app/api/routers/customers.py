from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.schemas import AccountOut, CustomerOut, Page

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=Page[CustomerOut])
def list_customers(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[CustomerOut]:
    items, total = crud.list_customers(db, limit=limit, offset=offset)
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
) -> CustomerOut:
    out = crud.get_customer(db, customer_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return out


@router.get("/{customer_id}/accounts", response_model=list[AccountOut])
def list_accounts_for_customer(
    customer_id: int,
    db: Session = Depends(get_db),
) -> list[AccountOut]:
    if crud.get_customer(db, customer_id) is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return crud.list_accounts_for_customer(db, customer_id)
