from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.errors import NotFound
from app.api.schemas import InvoiceTemplateEditRequest, InvoiceTemplateOut
from app.auth.dependencies import require_admin
from app.auth.schemas import UserOut
from app.db.models import InvoiceTemplate

router = APIRouter(prefix="/invoice-templates", tags=["invoice-templates"])


def _apply_edit(template: InvoiceTemplate, body: InvoiceTemplateEditRequest) -> None:
    if body.name is not None:
        template.name = body.name
    if body.description is not None:
        template.description = body.description
    if body.header_message is not None:
        template.header_message = body.header_message
    if body.footer_message is not None:
        template.footer_message = body.footer_message
    if body.promotion_message is not None:
        template.promotion_message = body.promotion_message
    if body.theme_name is not None:
        template.theme_name = body.theme_name
    if body.theme_color is not None:
        template.theme_color = body.theme_color
    template.updated_at = datetime.now(timezone.utc)


def _get_template_or_404(template_id: int, db: Session) -> InvoiceTemplate:
    template = db.get(InvoiceTemplate, template_id)
    if template is None:
        raise NotFound(f"Invoice template {template_id} not found")
    return template


@router.get(
    "",
    response_model=list[InvoiceTemplateOut],
    summary="List invoice templates",
)
def list_templates(
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> list[InvoiceTemplate]:
    return db.scalars(
        select(InvoiceTemplate)
        .order_by(InvoiceTemplate.is_system_template.desc(), InvoiceTemplate.id)
    ).all()


@router.get(
    "/{template_id}",
    response_model=InvoiceTemplateOut,
    summary="Get invoice template",
)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> InvoiceTemplate:
    return _get_template_or_404(template_id, db)


@router.get(
    "/{template_id}/preview",
    response_model=InvoiceTemplateOut,
    summary="Preview invoice template metadata",
)
def preview_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> InvoiceTemplate:
    return _get_template_or_404(template_id, db)


@router.post(
    "/{template_id}/activate",
    response_model=InvoiceTemplateOut,
    summary="Set active invoice template",
)
def activate_template(
    template_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> InvoiceTemplate:
    template = _get_template_or_404(template_id, db)
    db.query(InvoiceTemplate).update({InvoiceTemplate.is_active: False})
    template.is_active = True
    template.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(template)
    return template


@router.post(
    "/{template_id}/save-copy",
    response_model=InvoiceTemplateOut,
    status_code=201,
    summary="Save template changes as a custom copy",
)
def save_template_copy(
    template_id: int,
    body: InvoiceTemplateEditRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> InvoiceTemplate:
    base = _get_template_or_404(template_id, db)
    existing_copies = db.scalar(
        select(func.count(InvoiceTemplate.id))
        .where(InvoiceTemplate.base_template_id == base.id)
    ) or 0
    next_copy_no = existing_copies + 1
    template_code = f"{base.template_code}_CUSTOM_{next_copy_no:03d}"
    while db.scalar(select(InvoiceTemplate.id).where(InvoiceTemplate.template_code == template_code)) is not None:
        next_copy_no += 1
        template_code = f"{base.template_code}_CUSTOM_{next_copy_no:03d}"

    copy = InvoiceTemplate(
        name=body.name or f"{base.name} Copy {next_copy_no}",
        description=body.description if body.description is not None else base.description,
        template_code=template_code,
        is_active=False,
        is_system_template=False,
        base_template_id=base.id,
        header_message=body.header_message if body.header_message is not None else base.header_message,
        footer_message=body.footer_message if body.footer_message is not None else base.footer_message,
        promotion_message=body.promotion_message if body.promotion_message is not None else base.promotion_message,
        theme_name=body.theme_name if body.theme_name is not None else base.theme_name,
        theme_color=body.theme_color if body.theme_color is not None else base.theme_color,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return copy


@router.put(
    "/{template_id}/save-original",
    response_model=InvoiceTemplateOut,
    summary="Save template changes to the selected original",
)
def save_template_original(
    template_id: int,
    body: InvoiceTemplateEditRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
) -> InvoiceTemplate:
    if not body.confirm_save_original:
        raise HTTPException(
            status_code=400,
            detail="confirm_save_original must be true to modify the selected original template.",
        )
    template = _get_template_or_404(template_id, db)
    _apply_edit(template, body)
    db.commit()
    db.refresh(template)
    return template
