import time
import os
import shutil
import logging
import multiprocessing
import sys
from pathlib import Path
from datetime import datetime

# Add Models/SmartAI_Bill to sys.path
_smartai_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../Models/SmartAI_Bill"))
if _smartai_path not in sys.path:
    sys.path.insert(0, _smartai_path)

from app.db.base import SessionLocal
from app.db.models import GmfUpload, GmfUploadStatus
from app.core.config import settings
from processing.output_manager import create_output_batches
from config import OUTPUT_PDF_NAMES, OUTPUT_PDF_NAME_DEFAULT

logger = logging.getLogger("worker_queue")
logger.setLevel(logging.INFO)

COMPLETED_TEMP = Path("./queue/completed_temp")

def _worker_process(worker_id):
    """
    Parallel worker process that generates PDFs from GMFs in the incoming queue.
    """
    # Imports must be inside the process to avoid multiprocessing pickling issues
    from core.template_identifier import identify_template
    from templates.registry import get_renderer, get_parser
    
    logger.info(f"Worker {worker_id} started")
    COMPLETED_TEMP.mkdir(parents=True, exist_ok=True)
    
    while True:
        try:
            # Throttle 5 per sec = 0.2s sleep per iteration minimum
            start_time = time.time()
            
            incoming_dir = settings.queue_incoming_dir
            if not incoming_dir.exists():
                time.sleep(1)
                continue
                
            files = [f for f in incoming_dir.iterdir() if f.is_file() and not f.name.startswith(".") and not f.name.endswith(".processing")]
            
            if not files:
                time.sleep(1)
                continue
                
            # Pick a file
            file_path = files[0]
            working_path = incoming_dir / (file_path.name + ".processing")
            
            # Atomic rename to claim the file
            try:
                os.rename(file_path, working_path)
            except OSError:
                # Another worker grabbed it
                time.sleep(0.1)
                continue

            filename = file_path.name
            logger.info(f"Worker {worker_id} processing {filename}")
            
            # DB lookup to get cycle and template ID
            with SessionLocal() as db:
                upload = db.query(GmfUpload).filter(GmfUpload.filename == filename).first()
                if not upload:
                    logger.warning(f"No DB record for {filename}, deleting orphan file")
                    os.remove(working_path)
                    continue
                cycle_label = upload.folder_type
                template_id = upload.template_detected
                
            if not template_id:
                logger.error(f"Cannot process {filename}: template unknown")
                os.remove(working_path)
                with SessionLocal() as db:
                    upload = db.query(GmfUpload).filter(GmfUpload.filename == filename).first()
                    if upload:
                        upload.status = GmfUploadStatus.FAILED
                        upload.error_message = "Template unknown"
                        
                        if upload.billing_run_id:
                            from app.db.models import BillingRun, BillingRunFailure, RunStatus
                            run = db.query(BillingRun).filter(BillingRun.id == upload.billing_run_id).first()
                            if run:
                                run.failed += 1
                                db.add(BillingRunFailure(billing_run_id=run.id, account_number=filename, error_message="Template unknown"))
                                if run.succeeded + run.failed >= run.total_accounts:
                                    run.status = RunStatus.SUCCESS if run.failed == 0 else RunStatus.PARTIAL
                                    run.finished_at = datetime.now()
                        db.commit()
                continue
                
            # Render PDF
            parser_func = get_parser(template_id)
            RendererClass = get_renderer(template_id)
            
            if not parser_func or not RendererClass:
                logger.error(f"Cannot process {filename}: parser/renderer not found for {template_id}")
                os.remove(working_path)
                with SessionLocal() as db:
                    upload = db.query(GmfUpload).filter(GmfUpload.filename == filename).first()
                    if upload:
                        upload.status = GmfUploadStatus.FAILED
                        upload.error_message = f"Parser/Renderer not found for {template_id}"
                        
                        if upload.billing_run_id:
                            from app.db.models import BillingRun, BillingRunFailure, RunStatus
                            run = db.query(BillingRun).filter(BillingRun.id == upload.billing_run_id).first()
                            if run:
                                run.failed += 1
                                db.add(BillingRunFailure(billing_run_id=run.id, account_number=filename, error_message=f"Parser/Renderer not found for {template_id}"))
                                if run.succeeded + run.failed >= run.total_accounts:
                                    run.status = RunStatus.SUCCESS if run.failed == 0 else RunStatus.PARTIAL
                                    run.finished_at = datetime.now()
                        db.commit()
                continue
            
            data = parser_func(str(working_path))
            renderer = RendererClass()
            renderer.render(data)
            
            account_number = str(data.get("account_number", "unknown")).replace(" ", "")
            name_pattern = OUTPUT_PDF_NAMES.get(str(template_id), OUTPUT_PDF_NAME_DEFAULT)
            output_name = name_pattern.format(account_number=account_number, template_id=template_id)
            
            cycle_temp = COMPLETED_TEMP / cycle_label
            cycle_temp.mkdir(parents=True, exist_ok=True)
            output_pdf_path = cycle_temp / output_name
            
            renderer.save(str(output_pdf_path))
            
            # Update DB
            with SessionLocal() as db:
                upload = db.query(GmfUpload).filter(GmfUpload.filename == filename).first()
                if upload:
                    upload.status = GmfUploadStatus.COMPLETED
                    upload.processed_at = datetime.now()
                    
                    if upload.billing_run_id:
                        from app.db.models import BillingRun, RunStatus
                        run = db.query(BillingRun).filter(BillingRun.id == upload.billing_run_id).first()
                        if run:
                            run.succeeded += 1
                            if run.succeeded + run.failed >= run.total_accounts:
                                run.status = RunStatus.SUCCESS if run.failed == 0 else RunStatus.PARTIAL
                                run.finished_at = datetime.now()
                    db.commit()
            
            # Cleanup source GMF
            os.remove(working_path)
            logger.info(f"Worker {worker_id} successfully generated {output_name}")
            
            # Throttle
            elapsed = time.time() - start_time
            if elapsed < 0.2:
                time.sleep(0.2 - elapsed)
                
        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
            if 'filename' in locals() and 'working_path' in locals() and working_path.exists():
                try:
                    failed_dest = Path("./queue/failed")
                    failed_dest.mkdir(parents=True, exist_ok=True)
                    clean_filename = filename.replace(".processing", "")
                    dest_file_path = failed_dest / clean_filename
                    
                    # Atomic rename/move to failed queue
                    shutil.move(str(working_path), str(dest_file_path))
                    
                    with SessionLocal() as db:
                        upload = db.query(GmfUpload).filter(GmfUpload.filename == clean_filename).first()
                        if upload:
                            upload.status = GmfUploadStatus.FAILED
                            upload.error_message = str(e)
                            upload.file_path = str(dest_file_path)
                            
                            if upload.billing_run_id:
                                from app.db.models import BillingRun, BillingRunFailure, RunStatus
                                run = db.query(BillingRun).filter(BillingRun.id == upload.billing_run_id).first()
                                if run:
                                    run.failed += 1
                                    db.add(BillingRunFailure(
                                        billing_run_id=run.id,
                                        account_number=clean_filename,
                                        error_message=str(e)
                                    ))
                                    if run.succeeded + run.failed >= run.total_accounts:
                                        run.status = RunStatus.SUCCESS if run.failed == 0 else RunStatus.PARTIAL
                                        run.finished_at = datetime.now()
                        db.commit()
                except Exception as inner_err:
                    logger.error(f"Failed to record failure details: {inner_err}")
            time.sleep(1)


def _archiver_process():
    """
    Periodically checks the COMPLETED_TEMP dir and moves PDFs to the final structured archive.
    """
    logger.info("Archiver process started")
    while True:
        try:
            if COMPLETED_TEMP.exists():
                for cycle_dir in COMPLETED_TEMP.iterdir():
                    if cycle_dir.is_dir() and any(f.name.endswith(".pdf") for f in cycle_dir.iterdir()):
                        # We have PDFs for this cycle, batch them into the final output dir
                        create_output_batches(str(cycle_dir), cycle_label=cycle_dir.name)
            time.sleep(2)
        except Exception as e:
            logger.error(f"Archiver error: {e}", exc_info=True)
            time.sleep(5)


def start_workers(num_workers=10):
    """
    Starts the parallel worker pool and archiver daemon.
    """
    processes = []
    
    # Start Archiver
    archiver = multiprocessing.Process(target=_archiver_process, daemon=True)
    archiver.start()
    processes.append(archiver)
    
    # Start Workers
    for i in range(num_workers):
        p = multiprocessing.Process(target=_worker_process, args=(i,), daemon=True)
        p.start()
        processes.append(p)
        
    return processes


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Starting background worker queue daemon...")
    procs = start_workers()
    try:
        for p in procs:
            p.join()
    except KeyboardInterrupt:
        logger.info("Stopping workers...")
