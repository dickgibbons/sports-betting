#!/bin/bash
#
# Deploy Corners Backtesting to AWS EC2
#
# Usage:
#   ./deploy_corners_to_aws.sh <instance-ip> <ssh-key-path>
#
# Example:
#   ./deploy_corners_to_aws.sh 54.123.45.67 ~/.ssh/my-aws-key.pem
#

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <instance-ip> <ssh-key-path>"
    echo "Example: $0 54.123.45.67 ~/.ssh/my-aws-key.pem"
    exit 1
fi

INSTANCE_IP=$1
SSH_KEY=$2
REMOTE_USER="ec2-user"
REMOTE_DIR="~/corners-backtest"

echo "========================================"
echo "Deploying Corners Backtest to AWS"
echo "========================================"
echo "Instance: $INSTANCE_IP"
echo "SSH Key: $SSH_KEY"
echo "========================================"

# Verify SSH key permissions
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ SSH key not found: $SSH_KEY"
    exit 1
fi

chmod 400 "$SSH_KEY"
echo "✅ SSH key permissions verified"

# Create remote directories
echo ""
echo "📁 Creating remote directories..."
ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" \
    "mkdir -p $REMOTE_DIR"

echo "✅ Directories created"

# Upload Python scripts
echo ""
echo "📤 Uploading Python scripts..."

scp -i "$SSH_KEY" \
    footystats_api.py \
    corners_analyzer.py \
    corners_backtest.py \
    "$REMOTE_USER@$INSTANCE_IP:$REMOTE_DIR/"

echo "✅ Scripts uploaded"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."

ssh -i "$SSH_KEY" "$REMOTE_USER@$INSTANCE_IP" << 'EOF'
cd ~/corners-backtest

# Install required packages
python3 -m pip install --user --upgrade pip
python3 -m pip install --user requests pandas numpy

echo "✅ Dependencies installed"
EOF

echo ""
echo "========================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "========================================"
echo ""
echo "To run the backtest on AWS:"
echo ""
echo "1. SSH into the instance:"
echo "   ssh -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP"
echo ""
echo "2. Navigate to the directory:"
echo "   cd ~/corners-backtest"
echo ""
echo "3. Run the backtest (last 2 years):"
echo "   nohup python3 corners_backtest.py --start-date 2023-10-24 --end-date 2025-10-24 --strategy auto > backtest.log 2>&1 &"
echo ""
echo "4. Monitor progress:"
echo "   tail -f ~/corners-backtest/backtest.log"
echo ""
echo "5. Download results when complete:"
echo "   scp -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP:~/corners-backtest/corners_backtest_*.csv ."
echo ""
echo "========================================"
