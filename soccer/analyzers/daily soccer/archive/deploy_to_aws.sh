#!/usr/bin/bash
# Deploy Soccer Backtest to AWS EC2
# Usage: ./deploy_to_aws.sh <instance-ip> <ssh-key-path>

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: ./deploy_to_aws.sh <instance-ip> <ssh-key-path>"
    echo "Example: ./deploy_to_aws.sh 52.91.197.156 ~/.ssh/my-aws-key.pem"
    exit 1
fi

INSTANCE_IP=$1
SSH_KEY=$2
REMOTE_USER="ec2-user"  # Change to 'ubuntu' if using Ubuntu AMI

echo "📦 Deploying Soccer Backtest to AWS EC2 at $INSTANCE_IP"
echo "============================================================"

# Create remote directory
echo "📁 Creating remote directories..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$INSTANCE_IP" 'mkdir -p ~/soccer-backtest/models ~/soccer-backtest/data ~/soccer-backtest/output\ reports/Older'

# Upload Python files
echo "📤 Uploading Python files..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    soccer_best_bets_daily.py \
    aws_backtest_soccer.py \
    team_form_fetcher.py \
    team_stats_cache.py \
    "$REMOTE_USER@$INSTANCE_IP:~/soccer-backtest/"

# Upload models
echo "📤 Uploading form-enhanced models..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    models/soccer_ml_models_with_form.pkl \
    "$REMOTE_USER@$INSTANCE_IP:~/soccer-backtest/models/"

# Upload league database
echo "📤 Uploading league database..."
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no \
    "output reports/Older/UPDATED_supported_leagues_database.csv" \
    "$REMOTE_USER@$INSTANCE_IP:~/soccer-backtest/output\ reports/Older/"

# Install dependencies
echo "📦 Installing Python dependencies..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$REMOTE_USER@$INSTANCE_IP" << 'EOF'
cd ~/soccer-backtest
python3 -m pip install --user --quiet numpy pandas scikit-learn joblib requests
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "To run the backtest:"
echo "  ssh -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP"
echo "  cd ~/soccer-backtest"
echo "  nohup python3 aws_backtest_soccer.py --start-date 2024-08-15 --end-date 2024-10-17 > backtest.log 2>&1 &"
echo ""
echo "To monitor progress:"
echo "  ssh -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP 'tail -f ~/soccer-backtest/backtest.log'"
echo ""
echo "To download results when complete:"
echo "  scp -i $SSH_KEY $REMOTE_USER@$INSTANCE_IP:~/soccer-backtest/backtest_results_*.csv ."
echo ""
