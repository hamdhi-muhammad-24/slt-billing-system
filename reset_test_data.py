import sys
import os

# Ensure the app module can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.base import SessionLocal
from app.db.models import (
    NotificationEvent,
    BillingRunItem,
    BillingRunFailure,
    Invoice,
    GmfUpload,
    BillingRun,
)

def reset_test_data():
    print("WARNING: This script will delete all transaction history (GMF Uploads, Invoices, Billing Runs, Notifications).")
    print("It will NOT delete Users, Templates, or Billing Schedules.")
    confirm = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
    
    if confirm != "YES":
        print("Operation cancelled.")
        return

    print("Connecting to database...")
    with SessionLocal() as db:
        try:
            # Delete in order to avoid foreign key constraint violations
            deleted_notifs = db.query(NotificationEvent).delete()
            print(f"Deleted {deleted_notifs} NotificationEvents.")
            
            deleted_items = db.query(BillingRunItem).delete()
            print(f"Deleted {deleted_items} BillingRunItems.")
            
            deleted_failures = db.query(BillingRunFailure).delete()
            print(f"Deleted {deleted_failures} BillingRunFailures.")
            
            deleted_invoices = db.query(Invoice).delete()
            print(f"Deleted {deleted_invoices} Invoices.")
            
            # GmfUpload has a foreign key to BillingRun, so we delete it before BillingRun
            deleted_uploads = db.query(GmfUpload).delete()
            print(f"Deleted {deleted_uploads} GmfUploads.")
            
            # Now we can delete BillingRuns
            deleted_runs = db.query(BillingRun).delete()
            print(f"Deleted {deleted_runs} BillingRuns.")
            
            db.commit()
            print("\nSUCCESS! The database has been wiped clean of transaction history.")
            print("You can now move your GMF files back into Cycle_1 and they will be treated as brand new uploads.")
        except Exception as e:
            db.rollback()
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    reset_test_data()
