"""
Main billing router — all endpoints for the admin dashboard.
Calls SmartAI_Bill functions for PDF generation (never reimplements them).
"""
import os
import sys
import shutil
import tempfile
from typing import List, Optional
from pathlib import Path
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.auth.dependencies import require_admin
from app.auth.schemas import UserOut
from app.db.models import (
    GmfUpload, GmfUploadStatus,
    BillingRun, RunStatus, BillingRunFailure,
    BillingSchedule, BillingScheduleMode,
    NotificationEvent, NotificationEventType,
    InvoiceTemplate, TemplateApprovalStatus,
)
from app.db.base import SessionLocal
from app.core.config import settings
from app.billing_scheduler import reload_schedules

# ── SmartAI_Bill on sys.path ──────────────────────────────────────────────────
_smartai_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../Models/SmartAI_Bill")
)
if _smartai_path not in sys.path:
    sys.path.insert(0, _smartai_path)

from processing.batch_processor import process_single_file, process_batch
from processing.output_manager import (
    create_output_batches,
    list_output_dates,
    list_cycles_for_date,
    list_batches_for_cycle,
    list_pdfs_in_batch,
    get_pdf_path,
)
from templates.registry import TEMPLATE_REGISTRY

router = APIRouter(prefix="/billing", tags=["billing"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────────────────────

class GmfUploadOut(BaseModel):
    id: int
    filename: str
    file_path: str
    folder_type: str
    cycle_number: Optional[int]
    template_detected: Optional[str]
    status: str
    detected_at: datetime
    processed_at: Optional[datetime]
    error_message: Optional[str]
    rejection_reason: Optional[str]
    billing_run_id: Optional[int]

    class Config:
        from_attributes = True


class BillingRunOut(BaseModel):
    id: int
    batch_name: str
    cycle_number: Optional[int]
    status: str
    total_accounts: int
    succeeded: int
    failed: int
    started_at: datetime
    finished_at: Optional[datetime]
    output_path: Optional[str]
    failures: List[dict] = []

    class Config:
        from_attributes = True


class ScheduleOut(BaseModel):
    id: int
    name: str
    day_of_month: int
    run_time: str
    timezone: str
    schedule_mode: str
    is_active: bool
    approval_lead_days: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleCreate(BaseModel):
    name: str
    day_of_month: int
    run_time: str = "02:00"
    timezone: str = "Asia/Colombo"
    schedule_mode: str = "APPROVAL_REQUIRED"
    is_active: bool = True
    approval_lead_days: int = 1


class NotificationOut(BaseModel):
    id: int
    event_type: str
    title: str
    message: str
    upload_id: Optional[int]
    run_id: Optional[int]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RejectBody(BaseModel):
    reason: str = "Rejected by admin"


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard stats
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    """Aggregate stats for the Overview dashboard."""
    today = date.today()

    gmfs_today = db.query(func.count(GmfUpload.id)).filter(
        func.date(GmfUpload.detected_at) == today
    ).scalar() or 0

    gmfs_pending = db.query(func.count(GmfUpload.id)).filter(
        GmfUpload.status == GmfUploadStatus.PENDING_APPROVAL
    ).scalar() or 0

    # Count from billing run items for precise per-invoice numbers
    total_succeeded = db.query(func.sum(BillingRun.succeeded)).scalar() or 0
    total_failed = db.query(func.sum(BillingRun.failed)).scalar() or 0
    total_generated = total_succeeded + total_failed

    success_rate = round(total_succeeded / total_generated * 100, 2) if total_generated > 0 else 0

    active_runs = db.query(func.count(BillingRun.id)).filter(
        BillingRun.status == RunStatus.RUNNING
    ).scalar() or 0

    active_schedules = db.query(func.count(BillingSchedule.id)).filter(
        BillingSchedule.is_active == True
    ).scalar() or 0

    # Per-cycle summary
    cycles = {}
    for i in range(1, 5):
        folder = f"Cycle_{i}"
        uploads = db.query(GmfUpload).filter(GmfUpload.folder_type == folder).all()
        if uploads:
            statuses = [u.status.value for u in uploads]
            if all(s == "COMPLETED" for s in statuses):
                cycle_status = "completed"
            elif any(s == "GENERATING" for s in statuses):
                cycle_status = "generating"
            elif any(s == "APPROVED" for s in statuses):
                cycle_status = "approved"
            else:
                cycle_status = "pending"
        else:
            cycle_status = "no_gmf"

        cycles[folder] = {
            "received": len(uploads),
            "status": cycle_status,
        }

    unread_notifications = db.query(func.count(NotificationEvent.id)).filter(
        NotificationEvent.is_read == False
    ).scalar() or 0

    return {
        "gmfs_received_today": gmfs_today,
        "gmfs_pending_review": gmfs_pending,
        "total_invoices_generated": int(total_succeeded),
        "total_invoices_failed": int(total_failed),
        "success_rate": success_rate,
        "active_runs": active_runs,
        "active_schedules": active_schedules,
        "unread_notifications": unread_notifications,
        "cycles": cycles,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GMF Uploads
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/pending-batches")
def get_pending_batches(
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Group approved or pending GMF files into one batch per cycle (excluding Test GMFs)."""
    
    pending_uploads = db.query(GmfUpload).join(
        InvoiceTemplate,
        GmfUpload.template_detected == InvoiceTemplate.template_code
    ).filter(
        GmfUpload.status.in_([GmfUploadStatus.APPROVED, GmfUploadStatus.PENDING_APPROVAL]),
        GmfUpload.folder_type != "Test_GMFs",
        InvoiceTemplate.approval_status == TemplateApprovalStatus.APPROVED
    ).order_by(GmfUpload.detected_at.asc()).all()

    cycles = {}
    dates = {}
    for upload in pending_uploads:
        c = upload.cycle_number or 0
        if c not in cycles:
            cycles[c] = []
            dates[c] = upload.detected_at.strftime("%Y-%m-%d")
        cycles[c].append(upload.id)
        
    batches = []
    for c, upload_ids in cycles.items():
        batches.append({
            "cycle_number": c,
            "date": dates[c],
            "batch_index": 1,
            "file_count": len(upload_ids),
            "upload_ids": upload_ids
        })
            
    return batches

@router.get("/uploads", response_model=List[GmfUploadOut])
def get_uploads(
    status: Optional[str] = None,
    cycle: Optional[int] = None,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """List all detected GMF files with optional filters."""
    q = db.query(GmfUpload)
    if status:
        try:
            q = q.filter(GmfUpload.status == GmfUploadStatus[status])
        except KeyError:
            pass
    if cycle:
        q = q.filter(GmfUpload.cycle_number == cycle)
    return q.order_by(GmfUpload.detected_at.desc()).all()


# ─────────────────────────────────────────────────────────────────────────────
# Test Invoice Preview
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/preview/{upload_id}")
def preview_invoice(
    upload_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Generate a single test invoice PDF for admin review."""
    upload = db.query(GmfUpload).filter(GmfUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if not os.path.exists(upload.file_path):
        raise HTTPException(
            status_code=400,
            detail=f"GMF file not found on disk: {upload.file_path}"
        )

    # Save previews where React dev server can serve them
    preview_dir = Path(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../frontend/public/previews")
    ))
    preview_dir.mkdir(parents=True, exist_ok=True)

    args = (upload.file_path, str(preview_dir), 1, True)
    result = process_single_file(args)

    if not result.success:
        raise HTTPException(
            status_code=500,
            detail=f"Invoice engine failed: {result.error}"
        )

    # Update upload status and log notification
    upload.status = GmfUploadStatus.PENDING_APPROVAL
    notif = NotificationEvent(
        event_type=NotificationEventType.PREVIEW_GENERATED,
        title="Test Invoice Preview Ready",
        message=f"Preview for '{upload.filename}' generated successfully. Ready for approval.",
        upload_id=upload.id,
    )
    db.add(notif)
    db.commit()

    pdf_filename = os.path.basename(result.output_pdf)
    return {
        "message": "Preview generated successfully",
        "pdf_url": f"/previews/{pdf_filename}",
        "template_detected": result.template_id,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Approve / Reject
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/approve/{upload_id}")
def approve_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Approve a GMF file — enables batch generation."""
    upload = db.query(GmfUpload).filter(GmfUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload.status = GmfUploadStatus.APPROVED
    notif = NotificationEvent(
        event_type=NotificationEventType.APPROVED,
        title="GMF Approved",
        message=f"'{upload.filename}' approved. Ready for invoice generation.",
        upload_id=upload.id,
    )
    db.add(notif)
    db.commit()
    return {"message": "Approved successfully", "upload_id": upload_id}


@router.post("/reject/{upload_id}")
def reject_upload(
    upload_id: int,
    body: RejectBody,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Reject a GMF file — blocks generation."""
    upload = db.query(GmfUpload).filter(GmfUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload.status = GmfUploadStatus.FAILED
    upload.rejection_reason = body.reason
    notif = NotificationEvent(
        event_type=NotificationEventType.REJECTED,
        title="GMF Rejected",
        message=f"'{upload.filename}' rejected. Reason: {body.reason}",
        upload_id=upload.id,
    )
    db.add(notif)
    db.commit()
    return {"message": "Rejected", "upload_id": upload_id}


# ─────────────────────────────────────────────────────────────────────────────
# Batch Generation
# ─────────────────────────────────────────────────────────────────────────────

def _background_generate(upload_id: int, run_id: int):
    """Background task: calls friend's engine then organises output into folders."""

@router.post("/generate/{upload_id}")
def generate_batch(
    upload_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Queue a single GMF file for parallel generation."""
    upload = db.query(GmfUpload).filter(GmfUpload.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    if upload.status not in (GmfUploadStatus.APPROVED, GmfUploadStatus.PENDING_APPROVAL):
        raise HTTPException(
            status_code=400,
            detail=f"GMF is already generating/completed. Current status: {upload.status.value}"
        )

    if not os.path.exists(upload.file_path):
        raise HTTPException(status_code=400, detail=f"GMF file not found on disk: {upload.file_path}")

    # Move to incoming queue
    settings.queue_incoming_dir.mkdir(parents=True, exist_ok=True)
    filename = Path(upload.file_path).name
    new_path = settings.queue_incoming_dir / filename
    
    try:
        shutil.move(upload.file_path, str(new_path))
        upload.file_path = str(new_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to move file to queue: {e}")

    # Create BillingRun to track progress
    run = BillingRun(
        batch_name=f"Single GMF {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        status=RunStatus.RUNNING,
        total_accounts=1,
        succeeded=0,
        failed=0,
        started_at=datetime.now()
    )
    db.add(run)
    db.flush()

    upload.status = GmfUploadStatus.APPROVED
    upload.billing_run_id = run.id
    db.commit()

    return {"message": "File queued for generation"}


class GenerateBatchRequest(BaseModel):
    upload_ids: List[int]

@router.post("/generate-batch")
def generate_batch_endpoint(
    req: GenerateBatchRequest,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Queue multiple GMF files for parallel generation."""
    upload_ids = req.upload_ids
    if not upload_ids:
        raise HTTPException(status_code=400, detail="No uploads provided")

    uploads = db.query(GmfUpload).filter(GmfUpload.id.in_(upload_ids)).all()
    if not uploads:
        raise HTTPException(status_code=404, detail="Uploads not found")

    settings.queue_incoming_dir.mkdir(parents=True, exist_ok=True)
    
    # Create BillingRun to track progress
    run = BillingRun(
        batch_name=f"Batch {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        status=RunStatus.RUNNING,
        total_accounts=len(upload_ids),
        succeeded=0,
        failed=0,
        started_at=datetime.now()
    )
    db.add(run)
    db.flush()
    
    success_count = 0
    for upload in uploads:
        if upload.status not in (GmfUploadStatus.APPROVED, GmfUploadStatus.PENDING_APPROVAL):
            continue
        if not os.path.exists(upload.file_path):
            continue

        try:
            filename = Path(upload.file_path).name
            new_path = settings.queue_incoming_dir / filename
            if str(Path(upload.file_path)) != str(new_path):
                shutil.move(upload.file_path, str(new_path))
            upload.file_path = str(new_path)
            upload.status = GmfUploadStatus.APPROVED
            upload.billing_run_id = run.id
            success_count += 1
        except Exception:
            pass

    run.total_accounts = success_count
    db.commit()
    return {"message": f"{success_count} files queued for generation"}


def _background_retry_failed_batch(run_id: int):
    """Background task: retry only the failed files for a given billing run."""
    with SessionLocal() as db:
        run = db.query(BillingRun).filter(BillingRun.id == run_id).first()
        if not run or not run.failures:
            return

        failed_filenames = [f.account_number for f in run.failures]
        uploads = db.query(GmfUpload).filter(GmfUpload.filename.in_(failed_filenames)).all()
        
        if not uploads:
            return

        temp_pdf_dir = tempfile.mkdtemp(prefix="slt_batch_retry_")
        try:
            cycle_label = uploads[0].folder_type
            file_paths = [u.file_path for u in uploads]

            results = process_batch(file_paths, temp_pdf_dir)

            new_successes = sum(1 for r in results if r.success)
            
            # create outputs
            batch_folders = create_output_batches(temp_pdf_dir, cycle_label=cycle_label)
            if batch_folders:
                run.output_path = str(Path(batch_folders[0]).parent)

            run.succeeded += new_successes
            run.failed -= new_successes

            # Remove resolved failures
            for res in results:
                if res.success:
                    filename = Path(res.source_file).name
                    # Remove from DB
                    failure_record = db.query(BillingRunFailure).filter(
                        BillingRunFailure.billing_run_id == run.id,
                        BillingRunFailure.account_number == filename
                    ).first()
                    if failure_record:
                        db.delete(failure_record)
                    # update upload status
                    upload = db.query(GmfUpload).filter(GmfUpload.filename == filename).first()
                    if upload:
                        upload.status = GmfUploadStatus.COMPLETED
                else:
                    filename = Path(res.source_file).name
                    failure_record = db.query(BillingRunFailure).filter(
                        BillingRunFailure.billing_run_id == run.id,
                        BillingRunFailure.account_number == filename
                    ).first()
                    if failure_record:
                        failure_record.error_message = str(res.error) if res.error else "Unknown error"

            run.status = RunStatus.SUCCESS if run.failed == 0 else RunStatus.PARTIAL
            run.finished_at = datetime.now()

            db.commit()

        except Exception as e:
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now()
            db.commit()
        finally:
            if os.path.exists(temp_pdf_dir):
                shutil.rmtree(temp_pdf_dir, ignore_errors=True)


@router.post("/runs/{run_id}/retry")
def retry_failed_run(
    run_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin)
):
    """Retry all failed files in a specific run."""
    run = db.query(BillingRun).filter(BillingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    if run.failed == 0 or not run.failures:
        raise HTTPException(status_code=400, detail="No failures to retry")
        
    run.status = RunStatus.RUNNING
    db.commit()
    
    background_tasks.add_task(_background_retry_failed_batch, run.id)
    return {"message": "Retry started"}


# ─────────────────────────────────────────────────────────────────────────────
# Billing Runs (history + live status)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/runs", response_model=List[BillingRunOut])
def get_runs(db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    """List all billing run history."""
    return db.query(BillingRun).order_by(BillingRun.started_at.desc()).limit(100).all()


@router.get("/runs/{run_id}", response_model=BillingRunOut)
def get_run(run_id: int, db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    """Get a single billing run (used for live progress polling)."""
    run = db.query(BillingRun).filter(BillingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/results")
def get_run_results(run_id: int, db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    """Get successes and failures for a specific run, used for Generation Hub summary."""
    run = db.query(BillingRun).filter(BillingRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    failures_list = [{"account_number": f.account_number, "error_message": f.error_message} for f in run.failures]
    
    successes = []
    if run.output_path and os.path.exists(run.output_path):
        out_path = Path(run.output_path)
        date_str = out_path.parent.name
        cycle_label = out_path.name
        
        for batch_dir in out_path.iterdir():
            if batch_dir.is_dir() and batch_dir.name.startswith("Batch_"):
                for pdf_file in batch_dir.glob("*.pdf"):
                    successes.append({
                        "date": date_str,
                        "cycle": cycle_label,
                        "batch": batch_dir.name,
                        "filename": pdf_file.name,
                        "account_number": pdf_file.stem
                    })
                    
    return {
        "run_id": run.id,
        "successes": successes,
        "failures": failures_list
    }


# ─────────────────────────────────────────────────────────────────────────────
# Output Browser
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/output/dates")
def output_dates(_: UserOut = Depends(require_admin)):
    """List all dates that have generated output."""
    return {"dates": list_output_dates()}


@router.get("/output/{date_str}")
def output_cycles(date_str: str, _: UserOut = Depends(require_admin)):
    """List all cycles (Cycle_1, etc.) for a given date."""
    cycles = list_cycles_for_date(date_str)
    if not cycles:
        raise HTTPException(status_code=404, detail=f"No output found for date: {date_str}")
    return {"date": date_str, "cycles": cycles}


@router.get("/output/{date_str}/{cycle}")
def output_batches(date_str: str, cycle: str, _: UserOut = Depends(require_admin)):
    """List all batches for a given date and cycle."""
    batches = list_batches_for_cycle(date_str, cycle)
    if not batches:
        raise HTTPException(
            status_code=404,
            detail=f"No batches found for {date_str}/{cycle}"
        )
    # Add PDF count per batch
    result = []
    for b in batches:
        pdfs = list_pdfs_in_batch(date_str, cycle, b)
        result.append({"batch": b, "pdf_count": len(pdfs)})
    return {"date": date_str, "cycle": cycle, "batches": result}


@router.get("/output/{date_str}/{cycle}/{batch}")
def output_pdfs(
    date_str: str, cycle: str, batch: str,
    _: UserOut = Depends(require_admin)
):
    """List all PDF files in a specific batch."""
    pdfs = list_pdfs_in_batch(date_str, cycle, batch)
    return {"date": date_str, "cycle": cycle, "batch": batch, "files": pdfs}


@router.get("/output/{date_str}/{cycle}/{batch}/{filename}")
def serve_pdf(
    date_str: str, cycle: str, batch: str, filename: str,
    _: UserOut = Depends(require_admin)
):
    """Serve a single PDF file for inline viewing."""
    path = get_pdf_path(date_str, cycle, batch, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="PDF file not found")
    return FileResponse(path, media_type="application/pdf", filename=filename)


# ─────────────────────────────────────────────────────────────────────────────
# Invoice Templates
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/templates")
def get_templates(db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    """List all invoice templates, combining registry info with DB approval status."""
    templates = []
    
    # Pre-fetch all DB templates
    db_templates = {t.template_code: t for t in db.query(InvoiceTemplate).all()}
    
    for tid, info in TEMPLATE_REGISTRY.items():
        import importlib, pkgutil
        template_dir = os.path.join(_smartai_path, "templates", tid)
        layout_pdf = os.path.join(template_dir, "layout.pdf")
        has_layout = os.path.exists(layout_pdf)
        
        # Ensure DB record exists
        if tid not in db_templates:
            new_t = InvoiceTemplate(template_code=tid, name=info["name"], is_system_template=True)
            db.add(new_t)
            db.commit()
            db.refresh(new_t)
            db_templates[tid] = new_t
            
        db_record = db_templates[tid]

        templates.append({
            "id": tid,
            "name": info["name"],
            "description": info["description"],
            "ready": info.get("ready", False),
            "has_layout_preview": has_layout,
            "approval_status": db_record.approval_status.value if hasattr(db_record, "approval_status") else "PENDING",
        })
    return {"templates": templates}

class TemplateStatusUpdate(BaseModel):
    status: str

@router.patch("/templates/{template_id}/status")
def update_template_status(
    template_id: str,
    body: TemplateStatusUpdate,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin)
):
    """Approve or Reject an invoice template globally."""
    t = db.query(InvoiceTemplate).filter(InvoiceTemplate.template_code == template_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Template not found in DB")
        
    try:
        from app.db.models import TemplateApprovalStatus
        new_status = TemplateApprovalStatus[body.status]
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    t.approval_status = new_status
    
    # Cascade status update to pending uploads and physically move files
    import logging
    logger = logging.getLogger(__name__)
    
    if new_status == TemplateApprovalStatus.APPROVED:
        uploads = db.query(GmfUpload).filter(
            GmfUpload.template_detected == template_id,
            GmfUpload.status.in_([GmfUploadStatus.PENDING_APPROVAL, GmfUploadStatus.REJECTED])
        ).all()
        for upload in uploads:
            if upload.folder_type != "Test_GMFs":
                old_path = Path(upload.file_path)
                new_path = settings.queue_incoming_dir / upload.filename
                try:
                    settings.queue_incoming_dir.mkdir(parents=True, exist_ok=True)
                    if old_path.exists() and old_path != new_path:
                        shutil.move(str(old_path), str(new_path))
                        upload.file_path = str(new_path)
                except Exception as e:
                    logger.error(f"Failed to move file {upload.filename} to incoming queue: {e}")
            upload.status = GmfUploadStatus.APPROVED
            
    elif new_status == TemplateApprovalStatus.REJECTED:
        uploads = db.query(GmfUpload).filter(
            GmfUpload.template_detected == template_id,
            GmfUpload.status.in_([GmfUploadStatus.PENDING_APPROVAL, GmfUploadStatus.APPROVED])
        ).all()
        for upload in uploads:
            if upload.folder_type != "Test_GMFs":
                old_path = Path(upload.file_path)
                new_path = settings.queue_pending_dir / upload.filename
                try:
                    settings.queue_pending_dir.mkdir(parents=True, exist_ok=True)
                    if old_path.exists() and old_path != new_path:
                        shutil.move(str(old_path), str(new_path))
                        upload.file_path = str(new_path)
                except Exception as e:
                    logger.error(f"Failed to move file {upload.filename} to pending queue: {e}")
            upload.status = GmfUploadStatus.REJECTED
        
    db.commit()
    return {"message": "Status updated successfully", "status": new_status.value}



@router.get("/templates/{template_id}/preview")
def preview_template_layout(template_id: str, _: UserOut = Depends(require_admin)):
    """Serve the blank layout PDF for a template."""
    layout_path = os.path.join(_smartai_path, "templates", template_id, "layout.pdf")
    if not os.path.exists(layout_path):
        raise HTTPException(status_code=404, detail="Layout PDF not found for this template")
    return FileResponse(layout_path, media_type="application/pdf")


# ─────────────────────────────────────────────────────────────────────────────
# Notifications / Activity Log
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    """Get all system notification events."""
    q = db.query(NotificationEvent)
    if unread_only:
        q = q.filter(NotificationEvent.is_read == False)
    return q.order_by(NotificationEvent.created_at.desc()).limit(200).all()


@router.patch("/notifications/{notif_id}/read")
def mark_read(
    notif_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    notif = db.query(NotificationEvent).filter(NotificationEvent.id == notif_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}


@router.patch("/notifications/mark-all-read")
def mark_all_read(db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    db.query(NotificationEvent).filter(
        NotificationEvent.is_read == False
    ).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.delete("/notifications/clear-read")
def clear_read(db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    db.query(NotificationEvent).filter(NotificationEvent.is_read == True).delete()
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# Schedule Manager
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/schedules", response_model=List[ScheduleOut])
def get_schedules(db: Session = Depends(get_db), _: UserOut = Depends(require_admin)):
    return db.query(BillingSchedule).order_by(BillingSchedule.id).all()


@router.post("/schedules", response_model=ScheduleOut)
def create_schedule(
    body: ScheduleCreate,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    try:
        mode = BillingScheduleMode[body.schedule_mode]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid schedule_mode: {body.schedule_mode}")

    schedule = BillingSchedule(
        name=body.name,
        day_of_month=body.day_of_month,
        run_time=body.run_time,
        timezone=body.timezone,
        schedule_mode=mode,
        is_active=body.is_active,
        approval_lead_days=body.approval_lead_days,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    reload_schedules()
    return schedule


@router.put("/schedules/{schedule_id}", response_model=ScheduleOut)
def update_schedule(
    schedule_id: int,
    body: ScheduleCreate,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    schedule = db.query(BillingSchedule).filter(BillingSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    try:
        mode = BillingScheduleMode[body.schedule_mode]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid schedule_mode: {body.schedule_mode}")

    schedule.name = body.name
    schedule.day_of_month = body.day_of_month
    schedule.run_time = body.run_time
    schedule.timezone = body.timezone
    schedule.schedule_mode = mode
    schedule.is_active = body.is_active
    schedule.approval_lead_days = body.approval_lead_days
    db.commit()
    db.refresh(schedule)
    reload_schedules()
    return schedule


@router.patch("/schedules/{schedule_id}/toggle")
def toggle_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    schedule = db.query(BillingSchedule).filter(BillingSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    schedule.is_active = not schedule.is_active
    db.commit()
    reload_schedules()
    return {"id": schedule_id, "is_active": schedule.is_active}


@router.delete("/schedules/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    _: UserOut = Depends(require_admin),
):
    schedule = db.query(BillingSchedule).filter(BillingSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    db.delete(schedule)
    db.commit()
    reload_schedules()
    return {"ok": True}
