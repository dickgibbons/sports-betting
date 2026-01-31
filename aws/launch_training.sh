#!/bin/bash
# Launch EC2 Training Instance
# Run from local machine to spin up an EC2 instance and start training

set -e

# Configuration
INSTANCE_TYPE="t3.medium"  # Good balance of cost and performance
AMI_ID="ami-0c7217cdde317cfec"  # Ubuntu 22.04 LTS (us-east-1)
KEY_NAME="sports-betting-key"
SECURITY_GROUP="sports-betting-sg"
REGION="us-east-1"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=============================================="
echo "Launching EC2 Training Instance"
echo "=============================================="

# Check if key pair exists, create if not
echo "Checking key pair..."
if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" 2>/dev/null; then
    echo "Creating key pair..."
    aws ec2 create-key-pair --key-name "$KEY_NAME" --region "$REGION" \
        --query 'KeyMaterial' --output text > ~/.ssh/${KEY_NAME}.pem
    chmod 400 ~/.ssh/${KEY_NAME}.pem
    echo "Key pair created: ~/.ssh/${KEY_NAME}.pem"
fi

# Check if security group exists, create if not
echo "Checking security group..."
SG_ID=$(aws ec2 describe-security-groups --group-names "$SECURITY_GROUP" --region "$REGION" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "")

if [ -z "$SG_ID" ] || [ "$SG_ID" == "None" ]; then
    echo "Creating security group..."
    SG_ID=$(aws ec2 create-security-group --group-name "$SECURITY_GROUP" \
        --description "Sports betting training server" --region "$REGION" \
        --query 'GroupId' --output text)

    # Allow SSH
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --region "$REGION" \
        --protocol tcp --port 22 --cidr 0.0.0.0/0
    echo "Security group created: $SG_ID"
fi

# Launch instance
echo "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --region "$REGION" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance launched: $INSTANCE_ID"
echo "Waiting for instance to be running..."

aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$REGION" \
    --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "=============================================="
echo "Instance ready!"
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "=============================================="
echo ""
echo "To connect and run training:"
echo ""
echo "  1. Wait ~1 minute for SSH to be ready"
echo ""
echo "  2. Copy training files:"
echo "     scp -i ~/.ssh/${KEY_NAME}.pem -r ${SCRIPT_DIR}/* ubuntu@${PUBLIC_IP}:~/"
echo ""
echo "  3. Connect to instance:"
echo "     ssh -i ~/.ssh/${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "  4. Run setup and training:"
echo "     chmod +x ec2_setup.sh && ./ec2_setup.sh"
echo "     source ~/nhl_training_env/bin/activate"
echo "     python3 train_all_models.py"
echo ""
echo "  5. Copy trained models back:"
echo "     scp -i ~/.ssh/${KEY_NAME}.pem -r ubuntu@${PUBLIC_IP}:~/trained_models/* ${SCRIPT_DIR}/../nhl/analyzers/"
echo ""
echo "  6. Terminate instance when done:"
echo "     aws ec2 terminate-instances --instance-ids $INSTANCE_ID --region $REGION"
echo ""
echo "Estimated cost: ~\$0.04/hour for t3.medium"
