"""
SLT Bill Generator - Main CLI Entry Point
Just run: python run.py
"""
import os
import sys
import logging
import tempfile
import shutil
from datetime import datetime

from config import (
    INBOUND_DIR, PROCESSED_DIR, FAILED_DIR, OUTPUT_ZIP_DIR, LOGS_DIR,
    DEFAULT_WORKERS, ZIP_BATCH_SIZE,
)
from processing.batch_processor import process_batch
from processing.zip_manager import create_output_zip
from processing.stats_tracker import StatsTracker
from templates.registry import list_templates
from core.template_identifier import identify_template


def setup_logging():
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOGS_DIR, f"slt_bills_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger('slt_bills'), log_file


def ensure_folders():
    for folder in [INBOUND_DIR, PROCESSED_DIR, FAILED_DIR,
                   OUTPUT_ZIP_DIR, LOGS_DIR]:
        os.makedirs(folder, exist_ok=True)


def collect_gmf_files(folder):
    if not os.path.exists(folder):
        return []
    return sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f))
        and not f.startswith('.')
    ])


def prompt_template_selection():
    templates = list_templates(only_ready=True)

    print("\n" + "=" * 70)
    print("  SLT BILL GENERATOR - SELECT TEMPLATE")
    print("=" * 70)
    print(f"  0. ALL templates (auto-detect from each file)")
    print()

    for i, t in enumerate(templates, start=1):
        print(f"  {i}. {t['name']:<40} [OK]")
        print(f"     {t['description']}")
        print()

    print("=" * 70)

    while True:
        try:
            choice = input(f"\n  Enter your choice (0-{len(templates)}): ").strip()

            if not choice:
                continue

            choice_num = int(choice)

            if choice_num == 0:
                print("\n  Selected: ALL templates (auto-detect)\n")
                return "all"

            if 1 <= choice_num <= len(templates):
                selected = templates[choice_num - 1]
                print(f"\n  Selected: {selected['name']}\n")
                return selected["id"]

            print(f"  Invalid. Enter 0-{len(templates)}")

        except ValueError:
            print("  Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\n  Aborted.")
            sys.exit(0)


def filter_files_by_template(files, target_template_id, log):
    """Filter files matching a specific template."""
    if target_template_id == "all":
        return files

    log(f"Filtering files for template: {target_template_id}")

    matching = []
    non_matching = 0
    errors = 0

    for f in files:
        try:
            result = identify_template(f)
            if result.template_id == target_template_id:
                matching.append(f)
            else:
                non_matching += 1
        except Exception as e:
            log(f"  Failed to identify {os.path.basename(f)}: {e}")
            errors += 1

    log(f"  Matched: {len(matching)} | Skipped: {non_matching} | Errors: {errors}")
    return matching


def main():
    ensure_folders()
    logger, log_file = setup_logging()
    log = logger.info

    log(" " * 70)
    log("  SLT BILL GENERATOR")
    log(" " * 70)

    # Collect files
    files = collect_gmf_files(INBOUND_DIR)

    if not files:
        log(f"\n  No GMF files found in: {INBOUND_DIR}")
        log(f"  Place your GMF files there and re-run.\n")
        return 1

    log(f"  Inbound folder:  {INBOUND_DIR}")
    log(f"  Files found:     {len(files)}")
    log(f"  Workers:         {DEFAULT_WORKERS}")
    log(f"  ZIP batch size:  {ZIP_BATCH_SIZE}")
    log(f"  Log file:        {log_file}")
    log(" " * 70)

    # Get template selection
    selected_template = prompt_template_selection()

    # Filter files
    if selected_template != "all":
        files = filter_files_by_template(files, selected_template, log)
        if not files:
            log(f"\n  No files matching '{selected_template}' found.\n")
            return 1
        log(f"\n  Generating {len(files)} '{selected_template}' bills\n")
    else:
        log(f"\n  Generating ALL {len(files)} bills\n")

    # Create temp directory for PDFs
    temp_pdf_dir = tempfile.mkdtemp(prefix="slt_bills_")
    log(f"  Temp PDF dir: {temp_pdf_dir}\n")

    try:
        # Process files
        stats = StatsTracker()
        stats.start()

        def progress(completed, total):
            pct = int(completed / total * 100)
            if pct % 10 == 0 and completed % max(1, total // 10) == 0:
                log(f"    Progress: {completed}/{total} ({pct}%)")

        results = process_batch(
            files, temp_pdf_dir,
            workers=DEFAULT_WORKERS,
            log_callback=log,
            progress_callback=progress
        )

        for r in results:
            stats.add_result(r)

        stats.stop()
        stats.print_summary(log_callback=log)

        report_path = stats.save_report(LOGS_DIR)
        log(f"  Detailed report: {report_path}")

        # Create output ZIP
        log("\n" + "" * 70)
        log("  CREATING OUTPUT ZIP")
        log(" " * 70)

        zips = create_output_zip(
            temp_pdf_dir,
            template_name=selected_template,
            log_callback=log
        )

        log(f"\n  Total ZIPs created: {len(zips)}")
        log(f"  ZIP output folder: {OUTPUT_ZIP_DIR}")
        log("\n  Processing complete\n")

    finally:
        if os.path.exists(temp_pdf_dir):
            try:
                shutil.rmtree(temp_pdf_dir)
            except OSError:
                pass

    return 0


if __name__ == "__main__":
    sys.exit(main())