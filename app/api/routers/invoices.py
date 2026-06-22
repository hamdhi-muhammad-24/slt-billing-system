import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.schemas import InvoiceOut
from app.billing import engine as billing_engine
from app.pdf.renderer import render_bill

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/{invoice_id}/pdf", response_class=Response)
def get_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
) -> Response:
    coords = crud.get_bill_coords_for_invoice(db, invoice_id)
    if coords is None:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")

    account_number, period_start, period_end = coords
    bill = billing_engine.build_bill(db, account_number, period_start, period_end)

    buf = io.BytesIO()
    render_bill(bill, buf)  # ReportLab accepts a file-like object as the path argument

    return Response(
        content=buf.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="invoice-{invoice_id}.pdf"'
        },
    )


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
) -> InvoiceOut:
    out = crud.get_invoice(db, invoice_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found")
    return out
