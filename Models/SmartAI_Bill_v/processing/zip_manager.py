import os
import zipfile
import shutil
from datetime import datetime
from config import ZIP_BATCH_SIZE, OUTPUT_ZIP_DIR, OUTPUT_ZIP_NAME, PROCESSED_DIR


def create_output_zip(temp_pdf_dir, template_name="all", log_callback=None):
    """
    Create ONE ZIP file containing ALL generated PDFs.
    """
    if not os.path.exists(temp_pdf_dir):
        if log_callback:
            log_callback("No PDFs to zip")
        return []

    # Collect ALL PDFs from temp dir (flat)
    pdfs = sorted([
        os.path.join(temp_pdf_dir, f)
        for f in os.listdir(temp_pdf_dir)
        if f.endswith('.pdf')
    ])

    if not pdfs:
        if log_callback:
            log_callback("No PDFs found to zip")
        return []

    if log_callback:
        log_callback(f"\nZipping {len(pdfs)} PDFs in batches of {ZIP_BATCH_SIZE}")

    os.makedirs(OUTPUT_ZIP_DIR, exist_ok=True)
    zip_paths = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Split into batches of ZIP_BATCH_SIZE
    for batch_num, i in enumerate(range(0, len(pdfs), ZIP_BATCH_SIZE), start=1):
        batch = pdfs[i:i + ZIP_BATCH_SIZE]

        zip_name = OUTPUT_ZIP_NAME.format(
            template=template_name,
            batch_num=batch_num,
            timestamp=timestamp,
        )
        zip_path = os.path.join(OUTPUT_ZIP_DIR, zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED,
                             compresslevel=6) as zf:
            for pdf_path in batch:
                arcname = os.path.basename(pdf_path)
                zf.write(pdf_path, arcname=arcname)

        zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        if log_callback:
            log_callback(
                f"  OK: {zip_name} ({len(batch)} PDFs, {zip_size_mb:.1f} MB)"
            )

        zip_paths.append(zip_path)

    # Cleanup temp PDFs
    try:
        shutil.rmtree(temp_pdf_dir)
    except OSError:
        pass

    if log_callback:
        log_callback(f"Created {len(zip_paths)} ZIP file(s)")

    return zip_paths


