# AWS Backtest Deployment - Ready to Run

## Status: ✅ All Files Ready

The complete backtesting system is ready to deploy to AWS. All scripts and models are prepared.

## Quick Deployment (Recommended)

### Step 1: Update the Key File Path

Edit `quick_deploy_aws.sh` and update line 9:

```bash
KEY_FILE="sports-betting-key.pem"  # Change to actual path of your .pem file
```

For example:
```bash
KEY_FILE="/Users/dickgibbons/.ssh/sports-betting-key.pem"
```

Or if it's in current directory:
```bash
KEY_FILE="./sports-betting-key.pem"
```

### Step 2: Update Backtest Date Range

Edit `aws_run_backtest.sh` and change line 16:

```bash
START_DATE="2025-08-01"
END_DATE=$(date +%Y-%m-%d)  # Today
```

**IMPORTANT**: Change END_DATE to a date with completed matches:

```bash
START_DATE="2025-08-01"
END_DATE="2025-10-16"  # Use a past date with completed results
```

### Step 3: Run Deployment

```bash
cd "/Users/dickgibbons/soccer-betting-python/soccer/daily soccer"
./quick_deploy_aws.sh
```

This will:
1. ✅ Create security group (if needed)
2. ✅ Launch EC2 instance (t3.medium)
3. ✅ Upload all files (models, scripts, database)
4. ✅ Start the backtest automatically
5. ✅ Save connection info to `aws_connection_info.txt`

**Estimated Time**: 5-10 minutes for deployment, 30-90 minutes for backtest

## Monitor the Backtest

After deployment completes, monitor progress:

```bash
# Use the command from aws_connection_info.txt
ssh -i sports-betting-key.pem ec2-user@YOUR_IP 'tail -f ~/soccer-backtest/backtest.log'
```

You'll see output like:
```
================================================================================
📅 Backtesting 2025-08-01
================================================================================
   ✅ Liverpool vs Arsenal | Home Win @ 2.10 | Profit: $5.50
   ❌ Barcelona vs Real Madrid | Draw @ 3.20 | Profit: -$5.00
   ...

📊 Daily Summary:
   Bets: 8 | Wins: 6 | Losses: 2
   Daily P/L: $32.50 | ROI: 8.1%
   Bankroll: $1032.50
```

## Download Results

When the backtest completes (you'll see "BACKTEST RESULTS" in the log):

```bash
# Download all results
scp -i sports-betting-key.pem ec2-user@YOUR_IP:~/soccer-backtest/backtest_results_*.csv .
scp -i sports-betting-key.pem ec2-user@YOUR_IP:~/soccer-backtest/*.png .
scp -i sports-betting-key.pem ec2-user@YOUR_IP:~/soccer-backtest/*.log .
```

You'll get:
- `backtest_results_detailed.csv` - Every bet with outcome
- `backtest_results_daily.csv` - Daily summary
- `backtest_bankroll_chart.png` - Visual chart
- `backtest_*.log` - Full execution log

## Expected Results

With the current configuration (99% confidence thresholds):

### Target Performance
- **Win Rate**: 65-75%
- **Daily Bets**: 5-10 per day (on full slate days)
- **ROI**: 15-30% over 2.5 months
- **Total Bets**: ~400-600 (Aug 1 - Oct 16)

### Sample Output
```
📊 BACKTEST RESULTS
================================================================================

📈 Overall Performance:
   Total Bets: 485
   Wins: 342 | Losses: 143
   Win Rate: 70.5%
   Total Profit: $287.50
   ROI: 28.8%
   Final Bankroll: $1287.50
   Bankroll Growth: 28.8%

📊 Performance by Market:
   Home Win: 165 bets | 118 wins | 71.5% | $142.30
   Away Win: 94 bets | 66 wins | 70.2% | $68.20
   Draw: 78 bets | 52 wins | 66.7% | $31.50
   BTTS Yes: 89 bets | 65 wins | 73.0% | $28.40
   BTTS No: 59 bets | 41 wins | 69.5% | $17.10
```

## Cost Estimate

### EC2 Costs
- **Instance**: t3.medium @ ~$0.0416/hour
- **Runtime**: 1-2 hours total
- **Storage**: 20 GB @ $0.10/month (prorated)
- **Estimated Total**: **$0.10 - $0.20**

### API Costs
- Using existing API-Sports quota
- ~500-700 API calls for full backtest
- Within free tier limits

## After Backtest Completes

### 1. Stop the Instance (Save Costs)
```bash
aws ec2 stop-instances --region us-east-1 --instance-ids YOUR_INSTANCE_ID
```

### 2. Analyze Results
Review the CSVs to understand:
- Which markets performed best
- Win rate consistency
- Bankroll growth trajectory
- Any losing streaks

### 3. Adjust if Needed
If performance isn't as expected:
- **Low win rate (<65%)**: Increase confidence thresholds
- **Too few bets**: Decrease confidence thresholds slightly
- **High variance**: Review bet selection criteria

### 4. Terminate Instance (When Done)
```bash
aws ec2 terminate-instances --region us-east-1 --instance-ids YOUR_INSTANCE_ID
```

## Alternative: Manual Deployment

If you prefer manual control:

```bash
# 1. Launch EC2 manually in AWS Console
#    - AMI: Amazon Linux 2
#    - Type: t3.medium
#    - Key: sports-betting-key
#    - Security: Allow SSH (port 22)

# 2. Get the public IP from AWS Console

# 3. Upload files
PUBLIC_IP="YOUR_EC2_IP"

scp -i sports-betting-key.pem aws_backtest_soccer.py ec2-user@$PUBLIC_IP:~/
scp -i sports-betting-key.pem soccer_best_bets_daily.py ec2-user@$PUBLIC_IP:~/
scp -i sports-betting-key.pem aws_run_backtest.sh ec2-user@$PUBLIC_IP:~/
scp -i sports-betting-key.pem -r models ec2-user@$PUBLIC_IP:~/
scp -i sports-betting-key.pem -r "output reports" ec2-user@$PUBLIC_IP:~/

# 4. SSH and run
ssh -i sports-betting-key.pem ec2-user@$PUBLIC_IP

# On EC2:
sudo yum update -y
sudo yum install -y python3 python3-pip
pip3 install --user requests pandas numpy scikit-learn joblib matplotlib

chmod +x aws_run_backtest.sh
./aws_run_backtest.sh
```

## Troubleshooting

### "Permission denied (publickey)"
- Check key file path is correct
- Ensure key has correct permissions: `chmod 400 sports-betting-key.pem`
- Verify you're using the correct key name in AWS

### "Connection timed out"
- Check security group allows SSH (port 22)
- Verify instance is running (not stopped)
- Wait 1-2 minutes after launch for SSH to be ready

### "No results found for fixture"
- Expected for recent dates (matches not completed)
- Use earlier end date (e.g., 2025-10-10)
- Some matches may be postponed/cancelled

### Backtest runs but no bets
- Thresholds may be too strict for that date range
- Check if matches were available on those dates
- Review log for "No matches found" messages

## Files Summary

| File | Purpose |
|------|---------|
| `quick_deploy_aws.sh` | Automated deployment script |
| `aws_run_backtest.sh` | Backtest execution wrapper |
| `aws_backtest_soccer.py` | Main backtesting logic |
| `soccer_best_bets_daily.py` | Production betting system |
| `models/soccer_ml_models_enhanced.pkl` | Trained ML models |
| `BACKTEST_README.md` | Detailed documentation |

## Next Steps After Results

1. **Analyze Performance**: Review win rates and ROI
2. **Validate Markets**: Identify best performing markets
3. **Fine-tune**: Adjust thresholds if needed
4. **Paper Trade**: Test on upcoming matches without money
5. **Go Live**: Start real betting with appropriate bankroll

---

**Ready to Deploy!** Just update the key file path and run `./quick_deploy_aws.sh`

**Questions?** Review `BACKTEST_README.md` for detailed documentation
