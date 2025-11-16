# Soccer Backtest - Quick Start Guide

## Current Status

✅ **Production System**: Ready (7-10 bets/day, 99% confidence)
⚠️ **AWS Backtest**: Needs Python version fix (choose option below)

## Run Backtest on AWS (3 Options)

### Option A: Ubuntu AMI (Easiest - Recommended)

```bash
# 1. Get Ubuntu AMI ID
AMI_ID=$(aws ec2 describe-images --region us-east-1 --owners 099720109477 \
  --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-*" \
  --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text)

# 2. Edit quick_deploy_aws.sh, change line 55 to:
#    AMI_ID="$AMI_ID"

# 3. Deploy
./quick_deploy_aws.sh

# 4. Monitor (wait 30-60 min)
ssh -i ~/.ssh/sports-betting-key.pem ubuntu@PUBLIC_IP 'tail -f ~/soccer-backtest/backtest.log'

# 5. Download results
scp -i ~/.ssh/sports-betting-key.pem ubuntu@PUBLIC_IP:~/soccer-backtest/backtest_results_*.csv .
```

### Option B: Retrain on AWS

```bash
# 1. Deploy
./quick_deploy_aws.sh

# 2. Upload trainer
scp -i ~/.ssh/sports-betting-key.pem soccer_trainer_enhanced.py ec2-user@IP:~/soccer-backtest/

# 3. SSH and train
ssh -i ~/.ssh/sports-betting-key.pem ec2-user@IP
cd ~/soccer-backtest
python3 soccer_trainer_enhanced.py

# 4. Run backtest
python3 aws_backtest_soccer.py --start-date 2025-10-01 --end-date 2025-10-16
```

### Option C: Match scikit-learn Version

```bash
# Locally downgrade and retrain
pip3 install scikit-learn==1.0.2
python3 soccer_trainer_enhanced.py

# Then deploy
./quick_deploy_aws.sh
```

## Files Location

All ready in: `/Users/dickgibbons/soccer-betting-python/soccer/daily soccer/`

## Documentation

- `BACKTEST_SUMMARY.md` - Full summary
- `AWS_DEPLOYMENT_INSTRUCTIONS.md` - Detailed guide  
- `BACKTEST_README.md` - Complete docs
- `AWS_INSTANCE_INFO.md` - Instance details

## Terminate Instance

```bash
aws ec2 terminate-instances --region us-east-1 --instance-ids INSTANCE_ID
```

## Cost

~$0.04-0.08 per backtest (1-2 hours runtime)
