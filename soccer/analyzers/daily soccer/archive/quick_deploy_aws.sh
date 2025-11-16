#!/bin/bash
################################################################################
# Quick AWS Deployment - Automated version
# Uses existing AWS resources (sports-betting-key)
################################################################################

set -e

# Configuration - UPDATE THESE
KEY_NAME="sports-betting-key"
KEY_FILE="/Users/dickgibbons/.ssh/sports-betting-key.pem"  # Path to your .pem file
AWS_REGION="us-east-1"
INSTANCE_TYPE="t3.medium"

echo "==================================
☁️  QUICK AWS DEPLOYMENT
==================================
"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found: $KEY_FILE"
    echo "Please update KEY_FILE in this script or place the file in current directory"
    exit 1
fi

echo "Using key: $KEY_NAME"
echo "Region: $AWS_REGION"
echo "Instance type: $INSTANCE_TYPE"
echo ""

# Get default VPC
VPC_ID=$(aws ec2 describe-vpcs --region $AWS_REGION --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text)

# Check for existing security group
SG_NAME="soccer-backtest-sg"
SECURITY_GROUP=$(aws ec2 describe-security-groups \
    --region $AWS_REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "")

if [ "$SECURITY_GROUP" == "None" ] || [ -z "$SECURITY_GROUP" ]; then
    echo "Creating security group..."
    SECURITY_GROUP=$(aws ec2 create-security-group \
        --region $AWS_REGION \
        --group-name $SG_NAME \
        --description "Security group for soccer backtesting" \
        --vpc-id $VPC_ID \
        --query 'GroupId' \
        --output text)

    aws ec2 authorize-security-group-ingress \
        --region $AWS_REGION \
        --group-id $SECURITY_GROUP \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0

    echo "✅ Security group created: $SECURITY_GROUP"
else
    echo "✅ Using existing security group: $SECURITY_GROUP"
fi

# Use Ubuntu 22.04 AMI (has Python 3.10+, compatible with our models)
echo "Using Ubuntu 22.04 LTS AMI..."
AMI_ID="ami-0c398cb65a93047f2"
echo "Using AMI: $AMI_ID (Ubuntu 22.04)"

# Create user data script for Ubuntu
cat > /tmp/ec2_user_data.sh << 'EOF'
#!/bin/bash
apt-get update -y
apt-get install -y python3 python3-pip git
pip3 install requests pandas numpy scikit-learn joblib matplotlib
mkdir -p /home/ubuntu/soccer-backtest
chown ubuntu:ubuntu /home/ubuntu/soccer-backtest
echo "Setup complete" > /home/ubuntu/setup_complete.txt
EOF

# Launch instance
echo ""
echo "🚀 Launching EC2 instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --region $AWS_REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SECURITY_GROUP \
    --user-data file:///tmp/ec2_user_data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=soccer-backtest}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "✅ Instance launched: $INSTANCE_ID"
echo "Waiting for instance to start..."

aws ec2 wait instance-running --region $AWS_REGION --instance-ids $INSTANCE_ID

PUBLIC_IP=$(aws ec2 describe-instances \
    --region $AWS_REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "✅ Instance running"
echo "Public IP: $PUBLIC_IP"

# Wait for SSH
echo ""
echo "Waiting for SSH (60 seconds)..."
sleep 60

# Upload files
echo ""
echo "📤 Uploading files..."

ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "mkdir -p ~/soccer-backtest/models ~/soccer-backtest/output\ reports/Older"

scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
    aws_backtest_soccer.py \
    soccer_best_bets_daily.py \
    aws_run_backtest.sh \
    ubuntu@$PUBLIC_IP:~/soccer-backtest/

if [ -f "models/soccer_ml_models_enhanced.pkl" ]; then
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
        models/soccer_ml_models_enhanced.pkl \
        ubuntu@$PUBLIC_IP:~/soccer-backtest/models/
fi

if [ -f "output reports/Older/UPDATED_supported_leagues_database.csv" ]; then
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
        "output reports/Older/UPDATED_supported_leagues_database.csv" \
        ubuntu@$PUBLIC_IP:~/soccer-backtest/output\ reports/Older/
fi

echo "✅ Files uploaded"

# Make executable
ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP \
    "cd ~/soccer-backtest && chmod +x aws_run_backtest.sh"

# Start backtest
echo ""
echo "🏃 Starting backtest..."

ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP \
    "cd ~/soccer-backtest && nohup python3 aws_backtest_soccer.py --start-date 2025-08-01 --end-date 2025-10-17 > backtest.log 2>&1 &"

echo "✅ Backtest started!"

# Save connection info
cat > aws_connection_info.txt << EOFINFO
Instance ID: $INSTANCE_ID
Public IP: $PUBLIC_IP
Region: $AWS_REGION
OS: Ubuntu 22.04

SSH:
  ssh -i $KEY_FILE ubuntu@$PUBLIC_IP

Monitor:
  ssh -i $KEY_FILE ubuntu@$PUBLIC_IP 'tail -f ~/soccer-backtest/backtest.log'

Download Results:
  scp -i $KEY_FILE ubuntu@$PUBLIC_IP:~/soccer-backtest/backtest_results_*.csv .
  scp -i $KEY_FILE ubuntu@$PUBLIC_IP:~/soccer-backtest/*.png .

Stop:
  aws ec2 stop-instances --region $AWS_REGION --instance-ids $INSTANCE_ID

Terminate:
  aws ec2 terminate-instances --region $AWS_REGION --instance-ids $INSTANCE_ID
EOFINFO

echo ""
echo "=================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=================================="
echo ""
echo "Monitor backtest:"
echo "  ssh -i $KEY_FILE ubuntu@$PUBLIC_IP 'tail -f ~/soccer-backtest/backtest.log'"
echo ""
echo "Connection info saved to: aws_connection_info.txt"
echo ""
echo "Backtest will take ~30-90 minutes to complete"
echo ""

rm -f /tmp/ec2_user_data.sh
