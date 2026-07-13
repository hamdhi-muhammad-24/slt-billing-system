import os
import multiprocessing

#PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INBOUND_DIR   = os.path.join(BASE_DIR, "data", "inbound")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
FAILED_DIR    = os.path.join(BASE_DIR, "data", "failed")
OUTPUT_ZIP_DIR = os.path.join(BASE_DIR, "output", "zips")
LOGS_DIR      = os.path.join(BASE_DIR, "logs")

DEFAULT_WORKERS = max(1, multiprocessing.cpu_count() - 1)

#ZIP BATCHING
ZIP_BATCH_SIZE = 1500

#NAMING
OUTPUT_PDF_NAMES = {
    "nonvat_home":                  "{account_number}_NONVAT_HOME.pdf",
    "nonvat_enterprise":            "{account_number}_NONVAT_ENTERPRISE.pdf",
    "vat_enterprise":               "{account_number}_VAT_ENTERPRISE.pdf",
    "product_label_grouping":       "{account_number}_ProductLevel.pdf",
    "subscription_ref_grouping":    "{account_number}_SubscriptionLevel.pdf",
    "summary_statement":            "SUMMARY.pdf",
    "invoice_of_summary":           "{account_number}_InvoiceOfSummary.pdf",
}

# Fallback if template not in the map
OUTPUT_PDF_NAME_DEFAULT = "SLT20eBill-{account_number}.pdf"
OUTPUT_ZIP_NAME = "SLT_BILLS_{template}_{batch_num:04d}_{timestamp}.zip"

#FILE HANDLING
MOVE_AFTER_PROCESS = True

#PERFORMANCE TARGET
TARGET_BILLS_PER_HOUR = 40000