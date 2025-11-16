# Sports Betting Daily Automation Guide

Complete guide for running daily betting reports independently for each sport.

## Table of Contents
- [Quick Start](#quick-start)
- [Available Scripts](#available-scripts)
- [Setup Instructions](#setup-instructions)
- [Running Reports Manually](#running-reports-manually)
- [Automated Scheduling](#automated-scheduling)
- [Understanding the Output](#understanding-the-output)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install Dependencies
```bash
cd /Users/dickgibbons/sports-betting
pip3 install -r requirements.txt
```

### 2. Set Up Automation (Interactive)
```bash
chmod +x setup_automation.sh
./setup_automation.sh
```

### 3. Run Reports Manually
```bash
# All sports
./run_all_daily.sh

# Individual sports
./run_nhl_daily.sh
./run_nba_daily.sh
./run_ncaa_daily.sh
./run_soccer_daily.sh
```

---

## Available Scripts

### Individual Sport Scripts

| Script | Description | What It Generates |
|--------|-------------|-------------------|
| `run_nhl_daily.sh` | NHL daily reports | Main predictions, first period analysis, goalie/player props, back-to-back opportunities, top 5 picks |
| `run_nba_daily.sh` | NBA daily reports | ML predictions, betting angles, moneyline/totals forecasts |
| `run_ncaa_daily.sh` | NCAA daily reports | Betting angles, spread analysis |
| `run_soccer_daily.sh` | Soccer daily reports | BTTS, totals (O/U 2.5), corners, first half predictions |

### Master Scripts

| Script | Description |
|--------|-------------|
| `run_all_daily.sh` | Runs all sports + unified cross-sport report |
| `setup_automation.sh` | Interactive setup for cron jobs |

### Advanced Options for `run_all_daily.sh`

```bash
# Run specific sports only
./run_all_daily.sh --nhl-only
./run_all_daily.sh --nba-only
./run_all_daily.sh --soccer-only

# Exclude specific sports
./run_all_daily.sh --no-soccer --no-ncaa  # NHL + NBA only
./run_all_daily.sh --no-nba               # All except NBA
```

---

## Setup Instructions

### Step 1: Verify Python Environment

Make sure you have Python 3.9+ installed:
```bash
python3 --version
```

### Step 2: Install Required Packages

```bash
cd /Users/dickgibbons/sports-betting
pip3 install -r requirements.txt
```

For Apple Silicon (M1/M2/M3), optionally install TensorFlow Metal for GPU acceleration:
```bash
pip3 install tensorflow-metal==1.1.0
```

### Step 3: Verify API Keys

The following API keys are hardcoded in the scripts (already set up):

| API | Key | Purpose |
|-----|-----|---------|
| The-Odds-API | `518c226b561ad7586ec8c5dd1144e3fb` | Live betting odds |
| Hockey-API | `960c628e1c91c4b1f125e1eec52ad862` | NHL game data |
| FootyStats | `ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11` | Soccer data |
| Football API | `960c628e1c91c4b1f125e1eec52ad862` | Soccer match data |

### Step 4: Make Scripts Executable

```bash
chmod +x run_*.sh setup_automation.sh
```

---

## Running Reports Manually

### NHL Reports
```bash
./run_nhl_daily.sh
```

**Generates:**
- Main NHL daily report (CSV)
- First period analysis (TXT + CSV)
- Goalie saves predictions
- Player shots predictions
- Back-to-back opportunities
- Top 5 best bets

**Output location:** `/Users/dickgibbons/sports-betting/reports/YYYY-MM-DD/`

### NBA Reports
```bash
./run_nba_daily.sh
```

**Generates:**
- NBA daily report with ML predictions (CSV)
- Betting angles analysis
- Moneyline and totals forecasts

### NCAA Reports
```bash
./run_ncaa_daily.sh
```

**Generates:**
- NCAA betting angles
- Spread analysis

### Soccer Reports
```bash
./run_soccer_daily.sh
```

**Generates:**
- Best bets (BTTS, Over/Under 2.5)
- Corners over/under 9.5 analysis
- First half predictions

### All Sports + Unified Report
```bash
./run_all_daily.sh
```

**Generates all individual sport reports PLUS:**
- Unified cross-sport top 10 picks
- Combined performance tracking
- Expected value rankings across all sports

---

## Automated Scheduling

### Option 1: Interactive Setup (Recommended)

```bash
./setup_automation.sh
```

This will guide you through:
1. Running all sports at once (5:00 AM daily)
2. Staggered schedule (different times for each sport)
3. Custom selection (choose which sports to automate)
4. Manual setup (show cron commands only)

### Option 2: Manual Cron Setup

Edit your crontab:
```bash
crontab -e
```

**Example 1: All sports at 5:00 AM daily**
```cron
0 5 * * * cd /Users/dickgibbons/sports-betting && ./run_all_daily.sh
```

**Example 2: Staggered schedule**
```cron
# NHL at 5:00 AM
0 5 * * * cd /Users/dickgibbons/sports-betting && ./run_nhl_daily.sh

# NBA at 6:00 AM
0 6 * * * cd /Users/dickgibbons/sports-betting && ./run_nba_daily.sh

# NCAA at 7:00 AM
0 7 * * * cd /Users/dickgibbons/sports-betting && ./run_ncaa_daily.sh

# Soccer at 8:00 AM
0 8 * * * cd /Users/dickgibbons/sports-betting && ./run_soccer_daily.sh
```

**Example 3: NHL and NBA only, weekdays only**
```cron
0 5 * * 1-5 cd /Users/dickgibbons/sports-betting && ./run_nhl_daily.sh
0 6 * * 1-5 cd /Users/dickgibbons/sports-betting && ./run_nba_daily.sh
```

### Verify Cron Jobs
```bash
crontab -l
```

---

## Understanding the Output

### Directory Structure
```
/Users/dickgibbons/sports-betting/
├── reports/
│   ├── 2025-11-16/                    # Date-organized reports
│   │   ├── nhl_daily_report_2025-11-16.csv
│   │   ├── nhl_first_period_trends_2025-11-16.txt
│   │   ├── nhl_first_period_trends_2025-11-16.csv
│   │   ├── nba_daily_report_2025-11-16.csv
│   │   ├── nba_report_2025-11-16.txt
│   │   ├── ncaa_report_2025-11-16.txt
│   │   └── soccer_report_2025-11-16.txt
│   └── report_2025-11-16.txt          # Unified cross-sport report
│
├── logs/
│   ├── nhl_daily_20251116_050001.log
│   ├── nba_daily_20251116_060001.log
│   └── all_sports_daily_20251116_050001.log
│
└── data/
    └── bet_history.json                # Bet tracking database
```

### Report Contents

**NHL Report (`nhl_daily_report_*.csv`):**
- Game matchups
- Predictions (ML, spread, totals)
- Confidence scores (0-100%)
- Edge percentages
- Odds from multiple sportsbooks

**NBA Report (`nba_daily_report_*.csv`):**
- ML predictions with XGBoost model
- Confidence levels
- Expected value (EV) filtering
- Totals forecasts

**Soccer Report (`soccer_report_*.txt`):**
- High-confidence picks only (60-75% threshold)
- BTTS Yes/No predictions
- Over/Under 2.5 goals
- Kelly Criterion bet sizing

**Unified Report (`report_YYYY-MM-DD.txt`):**
- Top 10 bets across ALL sports
- Ranked by expected value
- Performance tracking (wins/losses/pushes)
- Current bankroll and ROI

---

## Troubleshooting

### Issue: "Permission denied" when running scripts

**Solution:**
```bash
chmod +x run_*.sh setup_automation.sh
```

### Issue: "Python module not found"

**Solution:**
```bash
pip3 install -r requirements.txt
```

### Issue: Cron job not running

**Check cron logs:**
```bash
# macOS
tail -f /var/log/cron.log

# Or check system logs
log show --predicate 'process == "cron"' --last 1h
```

**Verify cron jobs are installed:**
```bash
crontab -l
```

**Test script manually:**
```bash
cd /Users/dickgibbons/sports-betting
./run_all_daily.sh
```

### Issue: API rate limits or errors

**Check log files:**
```bash
tail -50 /Users/dickgibbons/sports-betting/logs/nhl_daily_*.log
```

**Common API issues:**
- Rate limits: Wait and retry
- Invalid keys: Verify API keys in scripts
- No games today: Normal, script will skip

### Issue: No reports generated

**Verify output directory exists:**
```bash
mkdir -p /Users/dickgibbons/sports-betting/reports/$(date +%Y-%m-%d)
```

**Check for errors in logs:**
```bash
grep -i error /Users/dickgibbons/sports-betting/logs/*.log
```

### Issue: Models not found (nhl_enhanced_models.pkl)

**Solution:** Run training scripts first:
```bash
# NHL model training
cd /Users/dickgibbons/sports-betting/nhl/analyzers
python3 nhl_enhanced_trainer.py

# NBA model training
cd /Users/dickgibbons/sports-betting/nba/analyzers
python3 nba_enhanced_trainer.py
```

---

## Advanced Configuration

### Change Report Times

Edit the cron schedule:
```bash
crontab -e
```

Cron time format: `minute hour day month weekday`

Examples:
- `0 5 * * *` - 5:00 AM daily
- `30 14 * * *` - 2:30 PM daily
- `0 5 * * 1-5` - 5:00 AM weekdays only
- `0 */6 * * *` - Every 6 hours

### Email Reports (Optional)

Add email notification to cron:
```cron
0 5 * * * cd /Users/dickgibbons/sports-betting && ./run_all_daily.sh && mail -s "Daily Betting Report" your@email.com < reports/$(date +\%Y-\%m-\%d)/report*.txt
```

### AWS Integration (NHL Advanced)

The NHL has optional AWS integration for model training:
```bash
cd /Users/dickgibbons/sports-betting/nhl/analyzers
./automated_daily_system.sh
```

This uses EC2 instance for heavy computation. Requires:
- SSH key: `/Users/dickgibbons/.ssh/my-aws-key`
- AWS host: `ec2-user@3.93.56.53`

---

## Performance Tracking

View current performance:
```bash
# Check bet history
cat /Users/dickgibbons/sports-betting/data/bet_history.json | python3 -m json.tool

# View latest unified report
cat /Users/dickgibbons/sports-betting/reports/$(date +%Y-%m-%d)/report_*.txt
```

**Current System Performance (as of Nov 15, 2025):**
- Overall: 33-43 (43.4%), -$1,339 (-13.4%)
- NHL: 18-15 (54.5%), +$543
- NBA: 15-28 (34.9%), -$1,882

---

## Support & Documentation

- **Main README:** `/Users/dickgibbons/sports-betting/README.md`
- **NHL Documentation:** `/Users/dickgibbons/sports-betting/nhl/analyzers/*.md`
- **NBA Quick Start:** `/Users/dickgibbons/sports-betting/nba/analyzers/NBA_QUICK_START.md`
- **Soccer Documentation:** `/Users/dickgibbons/sports-betting/soccer/analyzers/daily soccer/README.md`

For issues, check log files in `/Users/dickgibbons/sports-betting/logs/`
