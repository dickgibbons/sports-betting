# Soccer Betting System - Backtesting Guide

## Overview

The backtest system evaluates the enhanced soccer betting models on historical data from August 1, 2025 to present. This helps validate the system's performance before deploying it for live betting.

## Files

| File | Purpose |
|------|---------|
| `aws_backtest_soccer.py` | Main backtesting script |
| `aws_run_backtest.sh` | AWS automation wrapper |
| `test_backtest_short.sh` | Quick 5-day test |

## How It Works

### 1. **Historical Data Collection**
- Fetches matches for each day in the date range
- Uses the same API calls as the live betting system
- Retrieves actual match results (home goals, away goals, BTTS, etc.)

### 2. **Prediction Generation**
- Runs the production betting system for each historical date
- Uses the same confidence thresholds (99%, 99%, 98.5%, 98%)
- Applies the same quality filters (min odds, one-bet-per-match, top 10)

### 3. **Result Evaluation**
- Compares predictions against actual outcomes
- Calculates wins/losses for each bet
- Tracks bankroll growth using Kelly Criterion staking

### 4. **Performance Metrics**
- **Win Rate**: Percentage of correct predictions
- **ROI**: Return on investment
- **Profit/Loss**: Total profit in dollars
- **Bankroll Growth**: Percentage increase from initial bankroll
- **Market Performance**: Win rates broken down by market type

## Quick Start

### Local Testing (2 days)

```bash
cd "/Users/dickgibbons/soccer-betting-python/soccer/daily soccer"

# Test on Oct 17-18 only
python3 aws_backtest_soccer.py --start-date 2025-10-17 --end-date 2025-10-18
```

### Short Test (5 days)

```bash
./test_backtest_short.sh
```

### Full Backtest (Aug 1 - Present)

**On AWS EC2:**

```bash
# 1. SSH to your EC2 instance
ssh user@your-ec2-instance

# 2. Upload files
scp aws_backtest_soccer.py user@your-ec2:/path/to/project/
scp aws_run_backtest.sh user@your-ec2:/path/to/project/
scp soccer_best_bets_daily.py user@your-ec2:/path/to/project/
scp models/soccer_ml_models_enhanced.pkl user@your-ec2:/path/to/project/models/

# 3. Run backtest
cd /path/to/project/
chmod +x aws_run_backtest.sh
./aws_run_backtest.sh
```

**Locally (slower):**

```bash
python3 aws_backtest_soccer.py --start-date 2025-08-01 --end-date 2025-10-18
```

## Output Files

After running the backtest, you'll get:

### 1. `backtest_results_detailed.csv`
Complete record of every bet placed:

| Column | Description |
|--------|-------------|
| date | Match date |
| home_team | Home team name |
| away_team | Away team name |
| market | Bet market (Home Win, BTTS, etc.) |
| selection | Specific selection |
| odds | Decimal odds |
| confidence | Model confidence (99%+) |
| stake_pct | Kelly stake percentage |
| stake_amount | Dollar amount bet |
| actual_result | Actual match outcome |
| correct | True if prediction was correct |
| profit | Profit/loss for this bet |
| bankroll_after | Bankroll after this bet |

### 2. `backtest_results_daily.csv`
Daily summary of performance:

| Column | Description |
|--------|-------------|
| date | Date |
| bets | Number of bets placed |
| wins | Number of winning bets |
| losses | Number of losing bets |
| pending | Bets with no result found |
| profit | Daily profit/loss |
| roi | Daily ROI |
| bankroll | Bankroll at end of day |
| win_rate | Daily win rate |

### 3. `backtest_bankroll_chart.png`
Visual chart showing bankroll growth over time.

### 4. `backtest_YYYYMMDD_HHMMSS.log`
Full execution log with all output.

## Expected Runtime

- **2 days**: ~2-5 minutes
- **5 days**: ~5-15 minutes
- **Full backtest (Aug-Oct)**: ~30-90 minutes

Time varies based on:
- Number of matches per day
- API response times
- Network speed
- Rate limiting delays

## Rate Limiting

The backtest includes built-in delays to avoid hitting API rate limits:
- 1 second between dates
- 2 seconds after each daily backtest
- Individual fixture lookups are queued

If you hit rate limits, increase the delays in `aws_backtest_soccer.py`.

## Sample Output

```
================================================================================
⚽ SOCCER BETTING BACKTEST
================================================================================
Start Date: 2025-08-01
End Date: 2025-10-18
Initial Bankroll: $1000.00
Thresholds: Winners 99% | Totals 99% | BTTS 98%
================================================================================

================================================================================
📅 Backtesting 2025-08-01
================================================================================

📊 Fetching matches for 2025-08-01...
   ✅ Premier League: 4 upcoming matches
   ✅ La Liga: 3 upcoming matches
   ...

📊 After odds filter (>=1.50): 28 bets
📊 After one-bet-per-match filter: 18 bets
📊 Final selection (top 10 by EV): 10 bets

   ✅ Liverpool vs Arsenal | Home Win @ 2.10 | Profit: $5.50
   ❌ Barcelona vs Real Madrid | Draw @ 3.20 | Profit: -$5.00
   ...

📊 Daily Summary:
   Bets: 10 | Wins: 7 | Losses: 3 | Pending: 0
   Daily P/L: $15.50 | ROI: 3.1%
   Bankroll: $1015.50

================================================================================
📊 BACKTEST RESULTS
================================================================================

📈 Overall Performance:
   Total Bets: 245
   Wins: 183 | Losses: 62
   Win Rate: 74.7%
   Total Profit: $425.50
   ROI: 42.6%
   Final Bankroll: $1425.50
   Bankroll Growth: 42.6%

📊 Performance by Market:
   Home Win: 89 bets | 67 wins | 75.3% | $187.25
   Away Win: 45 bets | 33 wins | 73.3% | $98.40
   Draw: 34 bets | 24 wins | 70.6% | $52.15
   BTTS Yes: 42 bets | 32 wins | 76.2% | $54.20
   BTTS No: 35 bets | 27 wins | 77.1% | $33.50

✅ Detailed results saved to: backtest_results_detailed.csv
✅ Daily summary saved to: backtest_results_daily.csv
✅ Bankroll chart saved to: backtest_bankroll_chart.png
```

## Interpreting Results

### Good Performance Indicators
- **Win Rate**: 65%+ (system is designed for high accuracy)
- **ROI**: 15%+ over 2-3 months
- **Consistent Growth**: Steady upward bankroll trend
- **Low Drawdowns**: No prolonged losing streaks

### Warning Signs
- **Win Rate**: <60% (thresholds may need adjustment)
- **Negative ROI**: System isn't beating the odds
- **High Variance**: Large swings in bankroll
- **Many Pending**: Results not available (data quality issue)

## Troubleshooting

### "No result found for fixture"
- Match hasn't been completed yet (future date)
- API doesn't have result data
- Match was postponed/cancelled

**Solution**: Ignore pending bets or wait for results to become available.

### "Could not find fixture ID"
- Teams might have different names in different API endpoints
- Match was in a different league/season

**Solution**: The backtest will skip these and continue.

### API Rate Limit Errors
**Solution**: Increase sleep delays in the script:
```python
time.sleep(2)  # Change to 3 or 5
```

### Low Bet Count
- Thresholds too strict for historical period
- Fewer matches available in that date range

**Solution**: This is expected - quality over quantity.

## AWS Deployment

### EC2 Instance Recommendations

**Instance Type**: t3.medium or t3.large
- 2-4 vCPUs
- 4-8 GB RAM
- General purpose

**OS**: Amazon Linux 2 or Ubuntu 20.04+

**Storage**: 20 GB minimum

### Setup Steps

1. **Launch EC2 Instance**
   ```bash
   # Use AWS Console or CLI
   aws ec2 run-instances --image-id ami-xxxxx --instance-type t3.medium
   ```

2. **Install Dependencies**
   ```bash
   sudo yum update -y  # Amazon Linux
   sudo yum install -y python3 python3-pip git

   pip3 install --user requests pandas numpy scikit-learn joblib matplotlib
   ```

3. **Upload Files**
   ```bash
   scp -i your-key.pem aws_backtest_soccer.py ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/
   scp -i your-key.pem aws_run_backtest.sh ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/
   scp -i your-key.pem soccer_best_bets_daily.py ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/
   scp -i your-key.pem -r models ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/
   ```

4. **Run Backtest**
   ```bash
   ssh -i your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com
   chmod +x aws_run_backtest.sh
   nohup ./aws_run_backtest.sh > backtest.log 2>&1 &
   ```

5. **Monitor Progress**
   ```bash
   tail -f backtest.log
   ```

6. **Download Results**
   ```bash
   scp -i your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/backtest_results_*.csv .
   scp -i your-key.pem ec2-user@ec2-xx-xx-xx-xx.compute.amazonaws.com:~/backtest_bankroll_chart.png .
   ```

### Optional: S3 Integration

Update `S3_BUCKET` in `aws_run_backtest.sh`:

```bash
S3_BUCKET="s3://your-bucket-name/soccer-backtests"
```

Then the script will automatically upload results to S3.

## Next Steps After Backtest

1. **Review Results**: Analyze win rates, ROI, and market performance
2. **Adjust Thresholds**: If needed, tune confidence thresholds
3. **Validate Markets**: Identify which markets perform best
4. **Live Testing**: Run system on upcoming matches with paper trading
5. **Go Live**: Deploy for real betting with appropriate bankroll

## Notes

- **API Credits**: Backtesting uses API calls - monitor your quota
- **Historical Accuracy**: Past performance doesn't guarantee future results
- **Model Staleness**: Models trained on 2023-2024 data may degrade over time
- **Retraining**: Consider monthly retraining to capture new trends

---

**Created**: October 18, 2025
**Version**: 1.0
**Status**: Ready for AWS Deployment ✅
