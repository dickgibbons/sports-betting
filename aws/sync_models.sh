#!/bin/bash
# Sync trained models from EC2 back to local machine
# Run this after training completes on EC2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZERS_DIR="${SCRIPT_DIR}/../nhl/analyzers"
KEY_NAME="sports-betting-key"

# Check if instance IP provided
if [ -z "$1" ]; then
    echo "Usage: ./sync_models.sh <EC2_PUBLIC_IP>"
    echo ""
    echo "Example: ./sync_models.sh 54.123.45.67"
    exit 1
fi

PUBLIC_IP=$1

echo "=============================================="
echo "Syncing Models from EC2"
echo "=============================================="
echo "Source: ubuntu@${PUBLIC_IP}:~/trained_models/"
echo "Destination: ${ANALYZERS_DIR}/"
echo ""

# Copy models
echo "Copying trained models..."
scp -i ~/.ssh/${KEY_NAME}.pem -r ubuntu@${PUBLIC_IP}:~/trained_models/* ${ANALYZERS_DIR}/

echo ""
echo "=============================================="
echo "Models synced successfully!"
echo "=============================================="
echo ""
echo "Files copied to ${ANALYZERS_DIR}:"
ls -la ${ANALYZERS_DIR}/*.pkl 2>/dev/null || echo "No .pkl files found"
echo ""
echo "Now run your daily reports to test the new models."
