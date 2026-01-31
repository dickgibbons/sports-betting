# Corners Backtesting - Over/Under 9.5 Corners

## Overview

This system analyzes and backtests betting strategies for **over/under 9.5 corners** in soccer matches using historical data from FootyStats API.

## Components

### 1. `footystats_api.py` (Updated)
- Enhanced to fetch corners data from FootyStats API
- Extracts home corners, away corners, and total corners
- Includes corners odds (over/under 9.5)

### 2. `corners_analyzer.py`
- Analyzes historical corners data
- Calculates league-specific statistics
- Identifies betting opportunities
- Generates insights for over/under 9.5 corners

### 3. `corners_backtest.py`
- Full backtesting engine for corners betting
- Supports multiple strategies: over, under, auto
- Uses Kelly Criterion for bankroll management
- Calculates profitability over historical data

### 4. `deploy_corners_to_aws.sh`
- Automated deployment to AWS EC2
- Uploads scripts and installs dependencies
- Provides instructions for running backtest

## Local Usage

### Analyze Historical Corners Data

```bash
cd "/Users/dickgibbons/soccer-betting-python/daily soccer"

# Analyze last 2 years
python3 corners_analyzer.py --start-date 2023-10-24 --end-date 2025-10-24

# Custom date range
python3 corners_analyzer.py --start-date 2024-01-01 --end-date 2024-12-31 --output my_analysis.csv
```

**Output:**
- Overall corners statistics
- League-specific analysis
- Distribution of corners per game
- Betting insights and recommendations
- CSV file with detailed match data

### Run Backtest Locally

```bash
cd "/Users/dickgibbons/soccer-betting-python/daily soccer"

# Backtest with auto strategy (finds best value bets)
python3 corners_backtest.py --start-date 2023-10-24 --end-date 2025-10-24 --strategy auto

# Backtest betting OVER 9.5 corners only
python3 corners_backtest.py --start-date 2023-10-24 --end-date 2025-10-24 --strategy over

# Backtest betting UNDER 9.5 corners only
python3 corners_backtest.py --start-date 2023-10-24 --end-date 2025-10-24 --strategy under
```

**Output:**
- Overall performance metrics (win rate, profit, ROI)
- Performance by selection (over vs under)
- Performance by league
- Detailed bets CSV
- Daily summary CSV

## AWS Deployment

### Prerequisites

1. **AWS EC2 Instance Running**
   - Instance type: t2.medium or larger recommended
   - Amazon Linux 2 or similar
   - Python 3.7+ installed

2. **SSH Key**
   - Correct SSH key pair (e.g., `my-aws-key.pem`)
   - Proper permissions set (chmod 400)

3. **Instance Access**
   - Security group allows SSH (port 22)
   - Public IP address available

### Start Your EC2 Instance

```bash
# Start instance
aws ec2 start-instances --instance-ids i-0272f49485acb073b

# Get public IP
aws ec2 describe-instances --instance-ids i-0272f49485acb073b \
  --query 'Reservations[0].Instances[0].PublicIpAddress'
```

### Deploy to AWS

```bash
cd "/Users/dickgibbons/soccer-betting-python/daily soccer"

# Deploy (replace with your instance IP and key path)
./deploy_corners_to_aws.sh 54.123.45.67 ~/.ssh/my-aws-key.pem
```

### Run Backtest on AWS

```bash
# SSH into instance
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP>

# Navigate to directory
cd ~/corners-backtest

# Run backtest for last 2 years (in background)
nohup python3 corners_backtest.py \
  --start-date 2023-10-24 \
  --end-date 2025-10-24 \
  --strategy auto \
  > backtest.log 2>&1 &

# Monitor progress
tail -f backtest.log

# Or use 'less' to view log
less backtest.log
```

### Monitor Backtest Progress

```bash
# View live log
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP> \
  'tail -f ~/corners-backtest/backtest.log'

# Check if process is running
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP> \
  'ps aux | grep corners_backtest'
```

### Download Results

```bash
# Download all results
scp -i ~/.ssh/my-aws-key.pem \
  ec2-user@<INSTANCE-IP>:~/corners-backtest/corners_backtest_*.csv .

# Download specific file
scp -i ~/.ssh/my-aws-key.pem \
  ec2-user@<INSTANCE-IP>:~/corners-backtest/corners_backtest_bets_auto.csv .

# Download log
scp -i ~/.ssh/my-aws-key.pem \
  ec2-user@<INSTANCE-IP>:~/corners-backtest/backtest.log .
```

### Stop Instance (Save Costs!)

```bash
# Stop instance when done
aws ec2 stop-instances --instance-ids i-0272f49485acb073b
```

## Backtesting Strategies

### 1. Auto Strategy (Recommended)
```bash
--strategy auto
```
- Automatically identifies best value bets
- Bets over or under based on Kelly Criterion
- Maximizes expected value
- **Best for comprehensive testing**

### 2. Over Strategy
```bash
--strategy over
```
- Only bets on OVER 9.5 corners
- Good for high-scoring leagues
- Tests over-specific profitability

### 3. Under Strategy
```bash
--strategy under
```
- Only bets on UNDER 9.5 corners
- Good for defensive leagues
- Tests under-specific profitability

## Expected Runtime

### Backtest Duration
- **2 years (730 days)**: ~8-12 hours on AWS t2.medium
- **1 year (365 days)**: ~4-6 hours
- **6 months (180 days)**: ~2-3 hours

### Factors Affecting Runtime
- API rate limiting (1 request per second)
- Number of matches per day (varies by season)
- Network latency

### Approximate API Calls
- **2 years**: ~1,500-2,000 API calls
- **1 year**: ~750-1,000 API calls

## Interpreting Results

### Key Metrics

**Overall Performance:**
- `Total Bets`: Number of bets placed
- `Win Rate`: Percentage of correct predictions
- `Total Profit`: Net profit/loss in dollars
- `ROI`: Return on investment percentage
- `Bankroll Growth`: Final bankroll vs initial bankroll

**By Selection:**
- Over 9.5: Performance betting over
- Under 9.5: Performance betting under

**By League:**
- Shows which leagues are most profitable
- Helps identify league-specific patterns

### Good Backtest Results

✅ **Profitable System:**
- Win rate > 52% (break-even at typical odds ~1.9)
- Positive total profit
- ROI > 5%
- Bankroll growth > 0%

⚠️ **Warning Signs:**
- Win rate < 50%
- Negative total profit
- ROI < -5%
- Steep bankroll decline

## Configuration

### Bankroll Settings

Edit `corners_backtest.py` to adjust:

```python
INITIAL_BANKROLL = 1000.0      # Starting bankroll
KELLY_FRACTION = 0.25          # Quarter-Kelly (conservative)
MAX_BET_SIZE = 0.05            # Max 5% of bankroll per bet
```

### Kelly Criterion
- Uses Kelly Criterion for optimal stake sizing
- Conservative quarter-Kelly to reduce variance
- Cap at 5% to prevent large bets

## Troubleshooting

### SSH Connection Issues

```bash
# Verify instance is running
aws ec2 describe-instances --instance-ids i-0272f49485acb073b \
  --query 'Reservations[0].Instances[0].State.Name'

# Check security group allows SSH
aws ec2 describe-instances --instance-ids i-0272f49485acb073b \
  --query 'Reservations[0].Instances[0].SecurityGroups'
```

### Python Dependency Issues

```bash
# SSH into instance
ssh -i ~/.ssh/my-aws-key.pem ec2-user@<INSTANCE-IP>

# Install dependencies manually
sudo yum install -y python3-pip python3-devel gcc
python3 -m pip install --user --upgrade pip
python3 -m pip install --user requests pandas numpy
```

### API Rate Limiting

If you hit API rate limits:
- Backtest automatically handles rate limiting
- Uses 1 second delay between requests
- FootyStats allows 1,800 requests/hour

### No Corners Data

Some matches may not have corners data:
- Script automatically filters out matches without corners
- This is normal for some leagues/dates
- Results based on available data only

## File Structure

```
~/corners-backtest/
├── footystats_api.py              # API integration with corners data
├── corners_analyzer.py            # Historical analysis tool
├── corners_backtest.py            # Backtesting engine
├── backtest.log                   # Execution log
├── corners_backtest_bets_auto.csv      # Detailed bet results
├── corners_backtest_daily_auto.csv     # Daily summary
└── corners_analysis.csv           # Analysis output (if run)
```

## Sample Commands

### Quick Test (Last 30 Days)

```bash
python3 corners_backtest.py \
  --start-date 2025-09-24 \
  --end-date 2025-10-24 \
  --strategy auto
```

### Full 2-Year Backtest

```bash
python3 corners_backtest.py \
  --start-date 2023-10-24 \
  --end-date 2025-10-24 \
  --strategy auto
```

### League Analysis Only

```bash
python3 corners_analyzer.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output 2024_corners_analysis.csv
```

## Next Steps

1. **Run Analysis First**
   - Use `corners_analyzer.py` to understand data
   - Identify which leagues have consistent patterns
   - Check over/under rates by league

2. **Run Backtest**
   - Start with auto strategy
   - Use 2-year period for robust results
   - Review profitability by league

3. **Refine Strategy**
   - Focus on profitable leagues
   - Consider league-specific strategies
   - Adjust Kelly fraction based on risk tolerance

4. **Forward Testing**
   - Test on recent data (out-of-sample)
   - Compare with backtest results
   - Validate strategy before live betting

## Support

For issues or questions:
- Check the backtest log for errors
- Verify API key is valid in `footystats_api.py`
- Ensure sufficient API quota remaining

## Created: October 24, 2025

Last Updated: October 24, 2025
