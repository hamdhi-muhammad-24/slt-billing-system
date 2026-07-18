#!/bin/bash
# SLT Billing System Bi-Directional Google Drive Sync Script
# Runs in a loop to provide near-instantaneous GMF detection and output upload.

echo "Starting SLT Billing Google Drive Sync Daemon..."
echo "Syncing every 5 seconds..."

# LOOP 1: GMF Downloads (Runs in background, check every 5 seconds)
# This loop is never blocked by slow upload operations.
while true; do
  rclone copy gdrive:SLT_GMF_Uploads /var/slt-billing/gmf_uploads \
    --exclude "/Output/**" \
    --exclude "/Output/" \
    --exclude "/Processed/**" \
    --exclude "/Processed/" \
    --exclude "/Failed/**" \
    --exclude "/Failed/" \
    --exclude "/Test_GMFs/**" \
    --exclude "/Test_GMFs/" \
    --exclude "desktop.ini" \
    --exclude "Thumbs.db" \
    --exclude "DESKTOP.INI" \
    --exclude "THUMBS.DB" \
    --quiet

  # Copy test GMF files (retains them on Google Drive)
  rclone copy gdrive:SLT_GMF_Uploads/Test_GMFs /var/slt-billing/gmf_uploads/Test_GMFs \
    --exclude "desktop.ini" \
    --exclude "Thumbs.db" \
    --exclude "DESKTOP.INI" \
    --exclude "THUMBS.DB" \
    --quiet
  sleep 5
done &

# LOOP 2: Output, Processed, & Failed Uploads (Runs in foreground, check every 60 seconds)
while true; do
  # Copy generated output PDFs from VM to Google Drive (if not already syncing)
  if ! pgrep -f "rclone copy /var/slt-billing/gmf_uploads/Output" > /dev/null; then
    rclone copy /var/slt-billing/gmf_uploads/Output gdrive:SLT_GMF_Uploads/Output \
      --exclude "desktop.ini" \
      --exclude "Thumbs.db" \
      --exclude "DESKTOP.INI" \
      --exclude "THUMBS.DB" \
      --quiet &
  fi

  # Delete original cycle files from Google Drive once the worker has archived
  # them locally as Processed. rclone is configured on the VM host, not inside
  # the app containers.
  if ! pgrep -f "rclone deletefile gdrive:SLT_GMF_Uploads/Cycle_" > /dev/null; then
    find /var/slt-billing/gmf_uploads/Processed -type f -print0 2>/dev/null | while IFS= read -r -d '' file; do
      cycle="$(basename "$(dirname "$file")")"
      filename="$(basename "$file")"
      case "$cycle" in
        Cycle_1|Cycle_2|Cycle_3|Cycle_4)
          rclone deletefile "gdrive:SLT_GMF_Uploads/${cycle}/${filename}" --quiet || true
          ;;
      esac
    done &
  fi

  # Move Processed folders from VM to Google Drive (if not already syncing)
  if ! pgrep -f "rclone move /var/slt-billing/gmf_uploads/Processed" > /dev/null; then
    rclone move /var/slt-billing/gmf_uploads/Processed gdrive:SLT_GMF_Uploads/Processed \
      --exclude "desktop.ini" \
      --exclude "Thumbs.db" \
      --exclude "DESKTOP.INI" \
      --exclude "THUMBS.DB" \
      --delete-empty-src-dirs --quiet &
  fi

  # Delete original cycle files from Google Drive once the worker has archived
  # them locally as Failed.
  if ! pgrep -f "rclone deletefile gdrive:SLT_GMF_Uploads/Cycle_" > /dev/null; then
    find /var/slt-billing/gmf_uploads/Failed -type f -print0 2>/dev/null | while IFS= read -r -d '' file; do
      cycle="$(basename "$(dirname "$file")")"
      filename="$(basename "$file")"
      case "$cycle" in
        Cycle_1|Cycle_2|Cycle_3|Cycle_4)
          rclone deletefile "gdrive:SLT_GMF_Uploads/${cycle}/${filename}" --quiet || true
          ;;
      esac
    done &
  fi

  # Move Failed folders from VM to Google Drive (if not already syncing)
  if ! pgrep -f "rclone move /var/slt-billing/gmf_uploads/Failed" > /dev/null; then
    rclone move /var/slt-billing/gmf_uploads/Failed gdrive:SLT_GMF_Uploads/Failed \
      --exclude "desktop.ini" \
      --exclude "Thumbs.db" \
      --exclude "DESKTOP.INI" \
      --exclude "THUMBS.DB" \
      --delete-empty-src-dirs --quiet &
  fi

  sleep 60
done
