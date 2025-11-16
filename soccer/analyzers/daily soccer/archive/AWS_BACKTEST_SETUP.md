# AWS Backtest Setup Guide - Form-Enhanced Models

## Overview
This guide explains how to run the Phase 2 form-enhanced backtest on AWS EC2.

## Prerequisites
1. AWS EC2 instance (t2.medium or larger recommended)
2. Correct SSH key pair (the instance uses `my-aws-key`, not `sports-betting-key`)
3. Python 3.7+ installed on the instance
4. Sufficient disk space (~500MB for models and data)

## Quick Start

### Option 1: Automated Deployment (Recommended)

Once you have the correct SSH key, run:

```bash
cd "/Users/dickgibbons/soccer-betting-python/soccer/daily soccer"
./deploy_to_aws.sh <instance-ip> ~/.ssh/my-aws-key.pem
```

This script will:
- Upload all necessary Python files
- Upload the form-enhanced models (21MB)
- Upload league database
- Install Python dependencies
- Provide instructions for running the backtest

### Option 2: Manual Deployment

1. **Start your EC2 instance:**
```bash
aws ec2 start-instances --instance-ids i-0272f49485acb073b
aws ec2 describe-instances --instance-ids i-0272f49485acb073b --query 'Reservations[0].Instances[0].PublicIpAddress'
```

2. **Create directories:**
```bash
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP> \
  'mkdir -p ~/soccer-backtest/models ~/soccer-backtest/data ~/soccer-backtest/output\ reports/Older'
```

3. **Upload files:**
```bash
cd "/Users/dickgibbons/soccer-betting-python/soccer/daily soccer"

scp -i ~/.ssh/my-aws-key.pem \
  soccer_best_bets_daily.py \
  aws_backtest_soccer.py \
  team_form_fetcher.py \
  team_stats_cache.py \
  ec2-user@<INSTANCE-IP>:~/soccer-backtest/

scp -i ~/.ssh/my-aws-key.pem \
  models/soccer_ml_models_with_form.pkl \
  ec2-user@<INSTANCE-IP>:~/soccer-backtest/models/

scp -i ~/.ssh/my-aws-key.pem \
  "output reports/Older/UPDATED_supported_leagues_database.csv" \
  ec2-user@<INSTANCE-IP>:~/soccer-backtest/output\ reports/Older/
```

4. **Install dependencies:**
```bash
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP> \
  'cd ~/soccer-backtest && python3 -m pip install --user numpy pandas scikit-learn joblib requests'
```

## Running the Backtest

### Full Historical Backtest (August 15 - October 17, 2024)
```bash
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP>
cd ~/soccer-backtest
nohup python3 aws_backtest_soccer.py --start-date 2024-08-15 --end-date 2024-10-17 > backtest.log 2>&1 &
```

### Monitor Progress
```bash
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP> 'tail -f ~/soccer-backtest/backtest.log'
```

### Download Results
```bash
scp -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP>:~/soccer-backtest/backtest_results_*.csv .
```

## Expected Runtime
- Full backtest (63 days): ~6-8 hours
- Approximate API calls: ~3,000-4,000
- Results: ~100-200 bets total

## Stopping the Instance
Don't forget to stop the instance when done to save costs:
```bash
aws ec2 stop-instances --instance-ids i-0272f49485acb073b
```

## Troubleshooting

### SSH Key Issues
The instance was created with `my-aws-key`. If you're getting permission denied:
1. Check which key the instance expects:
   ```bash
   aws ec2 describe-instances --instance-ids i-0272f49485acb073b \
     --query 'Reservations[0].Instances[0].KeyName'
   ```
2. Ensure you have the correct .pem file with proper permissions (chmod 400)

### Python Dependency Issues
If packages fail to install, try:
```bash
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP>
sudo yum install -y python3-pip python3-devel gcc
python3 -m pip install --user --upgrade pip
python3 -m pip install --user numpy pandas scikit-learn joblib requests
```

### Form Features Not Loading
Verify the form-enhanced models are loaded:
```bash
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP>
cd ~/soccer-backtest
python3 -c "from soccer_best_bets_daily import SoccerBestBetsGenerator; SoccerBestBetsGenerator()"
```

You should see: `🚀 Using FORM-ENHANCED models (Phase 2)`

## File Structure on AWS
```
~/soccer-backtest/
├── soccer_best_bets_daily.py           # Main prediction system
├── aws_backtest_soccer.py               # Backtest runner
├── team_form_fetcher.py                 # Form feature fetcher
├── team_stats_cache.py                  # Caching system
├── models/
│   └── soccer_ml_models_with_form.pkl   # 45-feature models (21MB)
├── data/
│   └── team_stats_cache.db              # Will be created during backtest
├── output reports/Older/
│   └── UPDATED_supported_leagues_database.csv
├── backtest.log                         # Execution log
├── backtest_results_detailed.csv        # Bet-by-bet results
└── backtest_results_daily.csv           # Daily summary
```

## What the Backtest Tests
The backtest validates the **Phase 2 form-enhanced models** that include:
- 13 odds-based features (existing)
- 16 home team form features (new)
- 16 away team form features (new)
- **Total: 45 features**

Expected improvements:
- BTTS Yes: 72% → 77-82% WR (+5-10 points)
- Match Winners: 42% → 52-58% WR (+10-16 points)
- System ROI: -67% → +15-30% (+80-100 points)

## Created: October 19, 2025
