# AWS Soccer Backtest - Instance Information

## Instance Details

**Instance ID**: i-0137ec195fb516497
**Public IP**: 3.90.105.9
**Region**: us-east-1
**Instance Type**: t3.medium
**AMI**: ami-057a9f77fd28e08c5 (Amazon Linux 2)
**Security Group**: sg-09a241c85c68799f2
**Key Name**: sports-betting-key
**Key File**: /Users/dickgibbons/.ssh/sports-betting-key.pem

**Status**: ⚠️ WILL BE TERMINATED (to avoid charges)

## Issue Encountered

**Scikit-learn Version Mismatch**
- Local models trained with: scikit-learn 1.6.1 (Python 3.9+)
- AWS EC2 has: scikit-learn 1.0.2 (Python 3.7)
- Model pickle files are incompatible between versions

## Solution for Future Deployment

### Option A: Use Ubuntu AMI with Python 3.9+

```bash
# Find Ubuntu 22.04 AMI
aws ec2 describe-images \
    --region us-east-1 \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --output text

# Launch with Ubuntu (will have Python 3.10+)
# Then models will load correctly
```

### Option B: Retrain Models on AWS

```bash
# SSH to instance
ssh -i /Users/dickgibbons/.ssh/sports-betting-key.pem ec2-user@PUBLIC_IP

# Upload trainer
scp -i /Users/dickgibbons/.ssh/sports-betting-key.pem \
    soccer_trainer_enhanced.py \
    ec2-user@PUBLIC_IP:~/soccer-backtest/

# Install dependencies and train
pip3 install --user scikit-learn joblib pandas numpy requests
cd ~/soccer-backtest
python3 soccer_trainer_enhanced.py

# Then run backtest
python3 aws_backtest_soccer.py --start-date 2025-10-01 --end-date 2025-10-16
```

### Option C: Downgrade Local scikit-learn and Retrain

```bash
# On your local Mac
cd "/Users/dickgibbons/soccer-betting-python/soccer/daily soccer"
pip3 install scikit-learn==1.0.2
python3 soccer_trainer_enhanced.py

# Then upload the compatible model to AWS
scp -i /Users/dickgibbons/.ssh/sports-betting-key.pem \
    models/soccer_ml_models_enhanced.pkl \
    ec2-user@PUBLIC_IP:~/soccer-backtest/models/
```

## Files Already on AWS

✅ Uploaded to instance:
- `aws_backtest_soccer.py`
- `soccer_best_bets_daily.py`
- `aws_run_backtest.sh`
- `models/soccer_ml_models_enhanced.pkl` (incompatible version)
- `output reports/Older/UPDATED_supported_leagues_database.csv`

## Cost Summary

**Instance Runtime**: ~30 minutes
**Estimated Cost**: $0.02-0.03 (t3.medium @ $0.0416/hour)
**Status**: Will terminate to prevent further charges

## Termination Commands

```bash
# Stop instance (can restart later)
aws ec2 stop-instances --region us-east-1 --instance-ids i-0137ec195fb516497

# Terminate instance (permanent deletion)
aws ec2 terminate-instances --region us-east-1 --instance-ids i-0137ec195fb516497

# Cleanup security group after termination
aws ec2 delete-security-group --region us-east-1 --group-id sg-09a241c85c68799f2
```

## Next Steps

When ready to retry:

1. **Choose solution** (A, B, or C above)
2. **Run deployment script**: `./quick_deploy_aws.sh`
3. **Use Ubuntu AMI** OR **retrain models** to match Python version
4. **Monitor backtest**: Takes ~30-60 minutes for Oct 1-16
5. **Download results** when complete
6. **Terminate instance** to avoid charges

## Local Files Ready

All scripts are ready in:
```
/Users/dickgibbons/soccer-betting-python/soccer/daily soccer/
```

- ✅ `quick_deploy_aws.sh` - Automated deployment
- ✅ `aws_backtest_soccer.py` - Backtesting engine
- ✅ `aws_run_backtest.sh` - AWS wrapper script
- ✅ `AWS_DEPLOYMENT_INSTRUCTIONS.md` - Full guide
- ✅ `BACKTEST_README.md` - Documentation

---

**Recommendation**: Use **Option A (Ubuntu AMI)** for cleanest deployment with Python 3.10+ that matches your local environment.
