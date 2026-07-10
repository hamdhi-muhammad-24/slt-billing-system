#!/bin/bash
# SLT Billing System Bi-Directional Google Drive Sync Script
# Runs in a loop to provide near-instantaneous GMF detection and output upload.

echo "Starting SLT Billing Google Drive Sync Daemon..."
echo "Syncing every 5 seconds..."

# LOOP 1: GMF Downloads (Runs in background, check every 5 seconds)
# This loop is never blocked by slow upload operations.
while true; do
  rclone copy gdrive:SLT_GMF_Uploads /root/SLT_GMF_Uploads \
    --exclude "/Output/**" \
    --exclude "/Output/" \
    --exclude "/Processed/**" \
    --exclude "/Processed/" \
    --exclude "/Failed/**" \
    --exclude "/Failed/" \
    --quiet
  sleep 5
done &

# LOOP 2: Output, Processed, & Failed Uploads (Runs in foreground, check every 60 seconds)
while true; do
  # Copy generated output PDFs from VM to Google Drive (if not already syncing)
  if ! pgrep -f "rclone copy /root/SLT_GMF_Uploads/Output" > /dev/null; then
    rclone copy /root/SLT_GMF_Uploads/Output gdrive:SLT_GMF_Uploads/Output --quiet &
  fi

  # Copy Processed folders from VM to Google Drive (if not already syncing)
  if ! pgrep -f "rclone copy /root/SLT_GMF_Uploads/Processed" > /dev/null; then
    rclone copy /root/SLT_GMF_Uploads/Processed gdrive:SLT_GMF_Uploads/Processed --quiet &
  fi

  # Copy Failed folders from VM to Google Drive (if not already syncing)
  if ! pgrep -f "rclone copy /root/SLT_GMF_Uploads/Failed" > /dev/null; then
    rclone copy /root/SLT_GMF_Uploads/Failed gdrive:SLT_GMF_Uploads/Failed --quiet &
  fi

  sleep 60
done
