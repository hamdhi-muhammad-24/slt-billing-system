#!/bin/bash
# SLT Billing System Bi-Directional Google Drive Sync Script
# Runs in a loop to provide near-instantaneous GMF detection and output upload.

echo "Starting SLT Billing Google Drive Sync Daemon..."
echo "Syncing every 5 seconds..."

while true; do
  # 1. MOVE new GMF files from Google Drive to the VM.
  # This deletes them from Drive's Cycle folders after downloading to prevent loops.
  rclone move gdrive:SLT_GMF_Uploads /root/SLT_GMF_Uploads \
    --exclude "/Output/**" \
    --exclude "/Output/" \
    --exclude "/Processed/**" \
    --exclude "/Processed/" \
    --exclude "/Failed/**" \
    --exclude "/Failed/" \
    --delete-empty-src-dirs \
    --quiet

  # 2. COPY generated output PDFs from the VM back to Google Drive.
  # We use copy (not move) so the PDFs remain on the VM's disk for the Web UI to serve.
  rclone copy /root/SLT_GMF_Uploads/Output gdrive:SLT_GMF_Uploads/Output \
    --quiet

  # 3. MOVE Processed & Failed archive folders from the VM back to Google Drive.
  # This cleans up VM storage while keeping archives safe in Google Drive.
  rclone move /root/SLT_GMF_Uploads/Processed gdrive:SLT_GMF_Uploads/Processed \
    --delete-empty-src-dirs \
    --quiet
    
  rclone move /root/SLT_GMF_Uploads/Failed gdrive:SLT_GMF_Uploads/Failed \
    --delete-empty-src-dirs \
    --quiet

  # Check every 5 seconds
  sleep 5
done
