"""
Output batch manager for SLT Bill Generator.

Replaces ZIP creation with organised folder-based output:
  G:/My Drive/SLT_GMF_Uploads/Output/<YYYY-MM-DD>/<Cycle_N>/Batch_1/
                                                              Batch_2/
                                                              ...

Each batch folder contains up to BATCH_FOLDER_SIZE individual PDF files.
This allows the admin UI to list and preview individual invoices without unzipping.
"""
import os
import shutil
from datetime import datetime
from config import BATCH_FOLDER_SIZE, OUTPUT_BASE_DIR


def create_output_batches(temp_pdf_dir, cycle_label="Cycle_1", log_callback=None):
    """
    Move generated PDFs from temp_pdf_dir into organised date/cycle/batch folders.

    Returns a list of batch folder paths that were created.
    """
    if not os.path.exists(temp_pdf_dir):
        if log_callback:
            log_callback("No PDFs to organise — temp dir does not exist")
        return []

    # Collect all PDFs
    pdfs = sorted([
        os.path.join(temp_pdf_dir, f)
        for f in os.listdir(temp_pdf_dir)
        if f.lower().endswith(".pdf")
    ])

    if not pdfs:
        if log_callback:
            log_callback("No PDFs found to organise")
        return []

    today = datetime.now().strftime("%Y-%m-%d")
    base = os.path.join(OUTPUT_BASE_DIR, today, cycle_label)
    os.makedirs(base, exist_ok=True)

    if log_callback:
        log_callback(
            f"\nOrganising {len(pdfs)} PDFs → {base} "
            f"(batches of {BATCH_FOLDER_SIZE})"
        )

    batch_folders = []
    total_batches = (len(pdfs) + BATCH_FOLDER_SIZE - 1) // BATCH_FOLDER_SIZE

    for batch_num in range(1, total_batches + 1):
        start = (batch_num - 1) * BATCH_FOLDER_SIZE
        end = start + BATCH_FOLDER_SIZE
        batch_pdfs = pdfs[start:end]

        batch_dir = os.path.join(base, f"Batch_{batch_num}")
        os.makedirs(batch_dir, exist_ok=True)

        for pdf_path in batch_pdfs:
            dest = os.path.join(batch_dir, os.path.basename(pdf_path))
            shutil.move(pdf_path, dest)

        if log_callback:
            log_callback(
                f"  Batch {batch_num}/{total_batches}: "
                f"{len(batch_pdfs)} invoices → {batch_dir}"
            )

        batch_folders.append(batch_dir)

    # Clean up temp dir
    try:
        shutil.rmtree(temp_pdf_dir)
    except OSError:
        pass

    if log_callback:
        log_callback(f"Created {len(batch_folders)} batch folder(s) in {base}")

    return batch_folders


def get_output_root(date_str=None, cycle_label=None):
    """Return the output root path (optionally scoped by date and cycle)."""
    parts = [OUTPUT_BASE_DIR]
    if date_str:
        parts.append(date_str)
    if cycle_label:
        parts.append(cycle_label)
    return os.path.join(*parts)


def list_output_dates():
    """Return sorted list of dates that have output, newest first."""
    if not os.path.exists(OUTPUT_BASE_DIR):
        return []
    return sorted(
        [d for d in os.listdir(OUTPUT_BASE_DIR)
         if os.path.isdir(os.path.join(OUTPUT_BASE_DIR, d))],
        reverse=True,
    )


def list_cycles_for_date(date_str):
    """Return list of cycle folders for a given date."""
    date_path = os.path.join(OUTPUT_BASE_DIR, date_str)
    if not os.path.exists(date_path):
        return []
    return sorted([
        d for d in os.listdir(date_path)
        if os.path.isdir(os.path.join(date_path, d))
    ])


def list_batches_for_cycle(date_str, cycle_label):
    """Return list of batch folders for a given date/cycle."""
    cycle_path = os.path.join(OUTPUT_BASE_DIR, date_str, cycle_label)
    if not os.path.exists(cycle_path):
        return []
    return sorted([
        d for d in os.listdir(cycle_path)
        if os.path.isdir(os.path.join(cycle_path, d))
    ])


def list_pdfs_in_batch(date_str, cycle_label, batch_name):
    """Return list of PDF filenames in a specific batch folder."""
    batch_path = os.path.join(OUTPUT_BASE_DIR, date_str, cycle_label, batch_name)
    if not os.path.exists(batch_path):
        return []
    return sorted([
        f for f in os.listdir(batch_path)
        if f.lower().endswith(".pdf")
    ])


def get_pdf_path(date_str, cycle_label, batch_name, filename):
    """Return absolute path to a specific PDF file."""
    return os.path.join(OUTPUT_BASE_DIR, date_str, cycle_label, batch_name, filename)
