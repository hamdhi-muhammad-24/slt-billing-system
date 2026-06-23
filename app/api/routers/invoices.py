import io

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import crud
from app.api.deps import get_db
from app.api.errors import NotFound
from app.api.schemas import InvoiceOut
from app.auth.dependencies import require_invoice_owner, require_pdf_access
from app.auth.pdf_tokens import mint_pdf_token
from app.auth.schemas import PdfTokenOut, UserOut
from app.billing import engine as billing_engine
from app.core.config import settings
from app.pdf.renderer import render_bill

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get(
    "/{invoice_id}/pdf",
    response_class=Response,
    summary="Download invoice PDF",
    description=(
        "Renders and returns the invoice as a PDF file attachment. "
        "Uses the Phase 0 ReportLab generator; bytes are produced in memory — "
        "nothing is written to disk per request."
    ),
)
def get_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_pdf_access),
) -> Response:
    coords = crud.get_bill_coords_for_invoice(db, invoice_id)
    if coords is None:
        raise NotFound(f"Invoice {invoice_id} not found")

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


@router.get(
    "/{invoice_id}/pdf-token",
    response_model=PdfTokenOut,
    summary="Get signed PDF download token",
    description=(
        "Issues a short-lived signed token for the given invoice's PDF. "
        f"Token expires in {settings.pdf_token_expire_seconds} seconds. "
        "Pass it as ?token=<value> on the PDF endpoint."
    ),
)
def get_pdf_token(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_invoice_owner),
) -> PdfTokenOut:
    if crud.get_bill_coords_for_invoice(db, invoice_id) is None:
        raise NotFound(f"Invoice {invoice_id} not found")
    return PdfTokenOut(
        token=mint_pdf_token(invoice_id),
        expires_in=settings.pdf_token_expire_seconds,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceOut,
    summary="Get invoice",
    description=(
        "Returns a frozen invoice snapshot including all line items "
        "and the service accounts linked to those items."
    ),
)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_invoice_owner),
) -> InvoiceOut:
    out = crud.get_invoice(db, invoice_id)
    if out is None:
        raise NotFound(f"Invoice {invoice_id} not found")
    return out
