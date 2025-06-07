#!/usr/bin/env bash
# Legacy Reimbursement System Implementation
# Usage: ./run.sh <trip_duration_days> <miles_traveled> <total_receipts_amount>

# Call the Python calculation script with the three arguments
python3 calculate_reimbursement.py "$1" "$2" "$3"
