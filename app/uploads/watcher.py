"""
GMF Folder Watcher — monitors the Google Drive SLT_GMF_Uploads folder.

Watches for ANY new file (GMF files have no extension).
Auto-detects the billing cycle from which sub-folder the file is in.
Auto-detects the invoice template using SmartAI_Bill's identifier.
Creates a GmfUpload record and a NotificationEvent record in the database.
"""
import logging
import os
import threading
import sys
import time
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.db.models import GmfUpload, GmfUploadStatus, NotificationEvent, NotificationEventType
from app.core.config import settings

logger = logging.getLogger(__name__)

# Add SmartAI_Bill to sys.path so we can use the template identifier
_smartai_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../Models/SmartAI_Bill")
)
if _smartai_path not in sys.path:
    sys.path.insert(0, _smartai_path)

WATCH_DIR = settings.gmf_drive_path

# Valid folder names that correspond to billing cycles
CYCLE_FOLDERS = {
    "Cycle_1": 1,
    "Cycle_2": 2,
    "Cycle_3": 3,
    "Cycle_4": 4,
}
TEST_FOLDER = "Test_GMFs"
VALID_FOLDERS = set(CYCLE_FOLDERS.keys()) | {TEST_FOLDER}

# Files to skip (system/temp files)
SKIP_PREFIXES = (".", "~", "__")
SKIP_SUFFIXES = (".tmp", ".part", ".partial", ".crdownload")

# Lock to prevent concurrent DB writes
_process_lock = threading.Lock()


def _detect_template(file_path: str) -> str | None:
    """Run SmartAI_Bill's template identifier on the file. Returns template_id or None."""
    try:
        from core.template_identifier import identify_template
        result = identify_template(file_path)
        return result.template_id if result.is_supported else f"unsupported:{result.template_id}"
    except Exception as e:
        logger.warning(f"Template identification failed for {file_path}: {e}")
        return None


def _get_cycle(folder_name: str) -> int | None:
    """Return cycle number (1-4) from folder name, or None for Test_GMFs."""
    return CYCLE_FOLDERS.get(folder_name)


def _should_skip(filename: str) -> bool:
    """Return True if this file should be ignored."""
    name = os.path.basename(filename)
    if any(name.startswith(p) for p in SKIP_PREFIXES):
        return True
    if any(name.endswith(s) for s in SKIP_SUFFIXES):
        return True
    return False


class GmfFolderHandler(FileSystemEventHandler):
    """Handles file creation events inside the GMF watch directory."""

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)
        filename = filepath.name
        folder_name = filepath.parent.name

        # Skip temp/system files
        if _should_skip(filename):
            return

        # Only process files inside valid sub-folders
        if folder_name not in VALID_FOLDERS:
            logger.debug(f"Skipping file in unrecognised folder '{folder_name}': {filename}")
            return

        logger.info(f"Detected new file: {filepath} (folder: {folder_name}). Offloading to thread...")

        # Spawn a thread to prevent blocking the watchdog observer for other files
        t = threading.Thread(target=self._process_file, args=(filepath, filename, folder_name))
        t.start()

    def on_moved(self, event):
        if event.is_directory:
            return

        filepath = Path(event.dest_path)
        filename = filepath.name
        folder_name = filepath.parent.name

        # Skip temp/system files
        if _should_skip(filename):
            return

        # Only process files inside valid sub-folders
        if folder_name not in VALID_FOLDERS:
            return

        logger.info(f"Detected newly synced file: {filepath} (folder: {folder_name}). Offloading to thread...")

        t = threading.Thread(target=self._process_file, args=(filepath, filename, folder_name))
        t.start()

    def _process_file(self, filepath: Path, filename: str, folder_name: str):
        # Wait briefly to ensure the file has finished copying
        time.sleep(0.1)

        if not filepath.exists():
            logger.warning(f"File disappeared before processing: {filepath}")
            return

        # Auto-detect billing cycle
        cycle_number = _get_cycle(folder_name)
        is_test = folder_name == TEST_FOLDER

        # Auto-detect invoice template
        template_detected = _detect_template(str(filepath))
        logger.info(f"Template identified: {template_detected}")

        with _process_lock:
            with SessionLocal() as db:
                try:
                    # Avoid duplicate records
                    existing = db.query(GmfUpload).filter(
                        GmfUpload.file_path == str(filepath)
                    ).first()
                    if existing:
                        if existing.status in (GmfUploadStatus.COMPLETED, GmfUploadStatus.FAILED):
                            existing.status = GmfUploadStatus.PENDING_APPROVAL
                            existing.error_message = None
                            existing.rejection_reason = None
                            existing.billing_run_id = None
                            
                            # Create notification event
                            if is_test:
                                notif = NotificationEvent(
                                    event_type=NotificationEventType.TEST_GMF_RECEIVED,
                                    title="Test GMF Re-uploaded",
                                    message=(
                                        f"Test GMF file '{filename}' has been re-uploaded and is ready "
                                        f"for preview. Template detected: {template_detected or 'Unknown'}."
                                    ),
                                    upload_id=existing.id,
                                )
                            else:
                                notif = NotificationEvent(
                                    event_type=NotificationEventType.GMF_DETECTED,
                                    title=f"GMF Re-uploaded — Cycle {cycle_number}",
                                    message=(
                                        f"GMF file '{filename}' has been re-uploaded in Cycle {cycle_number}. "
                                        f"Template: {template_detected or 'Unknown'}. "
                                        f"Awaiting approval to generate invoices."
                                    ),
                                    upload_id=existing.id,
                                )
                            db.add(notif)
                            db.commit()
                            logger.info(f"Re-registered GMF (reset status to PENDING_APPROVAL): {filename}")
                        else:
                            logger.info(f"Already registered (currently in status {existing.status.value}): {filename}")
                        return

                    # Create GMF upload record
                    upload = GmfUpload(
                        filename=filename,
                        file_path=str(filepath),
                        folder_type=folder_name,
                        cycle_number=cycle_number,
                        template_detected=template_detected,
                        status=GmfUploadStatus.PENDING_APPROVAL,
                    )
                    db.add(upload)
                    db.flush()  # get upload.id

                    # Create notification event
                    if is_test:
                        notif = NotificationEvent(
                            event_type=NotificationEventType.TEST_GMF_RECEIVED,
                            title="Test GMF Received",
                            message=(
                                f"Test GMF file '{filename}' has been received and is ready "
                                f"for preview. Template detected: {template_detected or 'Unknown'}."
                            ),
                            upload_id=upload.id,
                        )
                    else:
                        notif = NotificationEvent(
                            event_type=NotificationEventType.GMF_DETECTED,
                            title=f"GMF Detected — Cycle {cycle_number}",
                            message=(
                                f"New GMF file '{filename}' detected in Cycle {cycle_number}. "
                                f"Template: {template_detected or 'Unknown'}. "
                                f"Awaiting approval to generate invoices."
                            ),
                            upload_id=upload.id,
                        )
                    db.add(notif)
                    db.commit()

                    logger.info(
                        f"Registered GMF: {filename} | cycle={cycle_number} | "
                        f"template={template_detected}"
                    )
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error saving GMF upload to DB: {e}", exc_info=True)


def _scan_existing_files(watch_path: Path):
    """Scan for files that already exist in the watch directory and register any
    that are not yet in the database.  This covers files uploaded while the
    watcher was not running (or events that Google Drive's virtual filesystem
    failed to deliver)."""
    handler = GmfFolderHandler()
    for subfolder in watch_path.iterdir():
        if not subfolder.is_dir():
            continue
        folder_name = subfolder.name
        if folder_name not in VALID_FOLDERS:
            continue
        for file in subfolder.iterdir():
            if file.is_file() and not _should_skip(file.name):
                logger.info(f"Startup scan — processing existing file: {file}")
                handler._process_file(file, file.name, folder_name)


def start_watcher():
    """Start monitoring the GMF upload folder."""
    watch_path = WATCH_DIR

    if not watch_path.exists():
        logger.warning(f"Watch directory does not exist, creating: {watch_path}")
        watch_path.mkdir(parents=True, exist_ok=True)

    # First, pick up any files that were uploaded while the watcher was stopped
    logger.info("Running startup scan for existing files...")
    _scan_existing_files(watch_path)
    logger.info("Startup scan complete.")

    handler = GmfFolderHandler()
    observer = Observer()
    observer.schedule(handler, str(watch_path), recursive=True)
    observer.start()

    logger.info(f"Watching for GMF files in: {watch_path}")
    logger.info(f"Valid folders: {sorted(VALID_FOLDERS)}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    start_watcher()
