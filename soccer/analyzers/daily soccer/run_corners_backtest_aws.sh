#!/bin/bash
#
# Quick Start: Run Corners Backtest on AWS
#
# This script:
# 1. Starts the EC2 instance
# 2. Deploys the corners backtest code
# 3. Runs the backtest for the last 2 years
# 4. Shows you how to monitor progress
#

set -e

# Configuration
INSTANCE_ID="i-0272f49485acb073b"  # Update with your instance ID
SSH_KEY="$HOME/.ssh/my-aws-key.pem"  # Update with your SSH key path

echo "========================================"
echo "⚽ CORNERS BACKTEST - AWS Quick Start"
echo "========================================"

# Start instance
echo ""
echo "🚀 Starting EC2 instance..."
aws ec2 start-instances --instance-ids "$INSTANCE_ID"

echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID"

# Get instance IP
INSTANCE_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "✅ Instance running at: $INSTANCE_IP"

# Wait for SSH to be ready
echo ""
echo "⏳ Waiting for SSH to be ready..."
sleep 30

# Deploy code
echo ""
echo "📤 Deploying corners backtest code..."
./deploy_corners_to_aws.sh "$INSTANCE_IP" "$SSH_KEY"

# Run backtest
echo ""
echo "🎯 Starting backtest on AWS..."
echo ""

START_DATE="2023-10-24"  # 2 years ago
END_DATE=$(date +%Y-%m-%d)  # Today

ssh -i "$SSH_KEY" "ec2-user@$INSTANCE_IP" << EOF
cd ~/corners-backtest
nohup python3 corners_backtest.py \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --strategy auto \
  > backtest.log 2>&1 &
echo "✅ Backtest started!"
echo ""
echo "Process ID: \$!"
EOF

echo ""
echo "========================================"
echo "✅ BACKTEST RUNNING ON AWS!"
echo "========================================"
echo ""
echo "Instance IP: $INSTANCE_IP"
echo "SSH Key: $SSH_KEY"
echo ""
echo "📊 To monitor progress:"
echo "   ssh -i $SSH_KEY ec2-user@$INSTANCE_IP 'tail -f ~/corners-backtest/backtest.log'"
echo ""
echo "📥 To download results when complete:"
echo "   scp -i $SSH_KEY ec2-user@$INSTANCE_IP:~/corners-backtest/corners_backtest_*.csv ."
echo ""
echo "🛑 To stop the instance (save costs!):"
echo "   aws ec2 stop-instances --instance-ids $INSTANCE_ID"
echo ""
echo "⏱️  Expected runtime: 8-12 hours"
echo "========================================"
