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
    if cycle_label == "Test_GMFs":
        if log_callback:
            log_callback("Skipping output batch creation for test GMF preview run")
        return []

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
    
    current_batch_num = 1
    pdf_index = 0
    
    while pdf_index < len(pdfs):
        batch_dir = os.path.join(base, f"Batch_{current_batch_num}")
        os.makedirs(batch_dir, exist_ok=True)
        
        existing_files = [f for f in os.listdir(batch_dir) if f.lower().endswith(".pdf")]
        existing_count = len(existing_files)
        
        space_left = BATCH_FOLDER_SIZE - existing_count
        
        if space_left <= 0:
            current_batch_num += 1
            continue
            
        moved_in_this_batch = 0
        while moved_in_this_batch < space_left and pdf_index < len(pdfs):
            pdf_path = pdfs[pdf_index]
            dest = os.path.join(batch_dir, os.path.basename(pdf_path))
            
            # Copy to VM local output directory duplicate
            try:
                local_vm_batch_dir = os.path.join("./output", today, cycle_label, f"Batch_{current_batch_num}")
                os.makedirs(local_vm_batch_dir, exist_ok=True)
                shutil.copy2(pdf_path, os.path.join(local_vm_batch_dir, os.path.basename(pdf_path)))
            except Exception as copy_err:
                if log_callback:
                    log_callback(f"  Warning: failed to duplicate copy to VM local folder: {copy_err}")
                    
            shutil.move(pdf_path, dest)
            moved_in_this_batch += 1
            pdf_index += 1
            
        if log_callback:
            log_callback(
                f"  Batch {current_batch_num}: "
                f"added {moved_in_this_batch} invoices → {batch_dir}"
            )
            
        if batch_dir not in batch_folders:
            batch_folders.append(batch_dir)
            
        current_batch_num += 1

    # Removed temp dir cleanup to allow concurrent worker writing

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
