from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.schemas import InvoiceOut

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
) -> InvoiceOut:
    out = crud.get_invoice(db, invoice_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
    return out
