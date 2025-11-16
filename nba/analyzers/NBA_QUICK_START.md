# NBA Betting System - Quick Start Guide

## ✅ What's Been Created

Your NBA betting system is now set up with the following files:

```
/Users/dickgibbons/nba/daily nba/
├── nba_odds_api.py                     ✅ Simple odds API tester
├── nba_odds_api_failover.py            ✅ Production odds API with failover
├── nba_stats_api_failover.py           ✅ Stats API with failover
├── nba_enhanced_data.py                ✅ Data integration module
├── nba_enhanced_trainer.py             ✅ ML model trainer
├── nba_daily_report.py                 ✅ Daily predictions generator
├── NBA_SYSTEM_SETUP.md                 ✅ Detailed setup guide
├── NBA_QUICK_START.md                  ✅ This file
├── models/                             ✅ For trained models
└── logs/                               ✅ For system logs
```

## 🚀 Quick Start (3 Steps)

### Step 1: Test NBA Odds API (Already Works!)

```bash
cd "/Users/dickgibbons/nba/daily nba"
python3 nba_odds_api.py
```

**Result:** ✅ Working! Found 29 upcoming NBA games with odds

### Step 2: Train the Models

```bash
python3 nba_enhanced_trainer.py
```

This will:
- Fetch NBA team statistics
- Build enhanced features (offensive rating, pace, FG%, etc.)
- Train Random Forest and Gradient Boosting models
- Save models to `nba_enhanced_models.pkl`

**Note:** The NBA.com Stats API can be slow or timeout. The system has failover to:
1. NBA Official Stats API (primary)
2. BallDontLie API (backup)
3. ESPN API (backup)

**Expected time:** 5-10 minutes

### Step 3: Generate Daily Predictions

```bash
python3 nba_daily_report.py
```

This will:
- Get today's NBA games
- Fetch real odds from The-Odds-API
- Make predictions for each game
- Generate CSV report with:
  - Predicted winner and confidence
  - Expected total points
  - Spread predictions
  - Betting edges

**Output:** `reports/YYYYMMDD/nba_daily_report_YYYY-MM-DD.csv`

## 📊 What the System Predicts

For each NBA game, you get:

### 1. **Moneyline (Winner) Predictions**
- Predicted winner
- Win confidence (probability)
- Betting odds for winner
- Edge over bookmaker (%)

### 2. **Totals (Over/Under Points)**
- Expected total points
- Over/under line
- Over probability
- Edge on totals bet

### 3. **Spread Predictions**
- Expected margin of victory
- Spread coverage probability
- Confidence level (High/Medium/Low)

## 🎯 Example Report Output

```
🏀 Lakers @ Warriors
   Predicted Winner: Warriors (62.3%) | Edge: +8.5%
   Expected Total: 228.5 (O/U 225.5) | Over: 58.3%
   Spread: Warriors (Medium confidence)
```

## 🔧 NBA vs NHL Differences

| Aspect | NHL | NBA |
|--------|-----|-----|
| Games/day | 5-15 | 5-15 |
| Scoring | Low (6-7 goals) | High (220-230 pts) |
| Key Stats | xGoals, Corsi, Save% | Off Rating, Pace, FG% |
| Variance | High | Lower |
| Home Advantage | ~55% | ~58-60% |

## 📈 NBA-Specific Features

The ML models use these NBA-specific features:

**Offensive Metrics:**
- Points per game
- Offensive Rating (points per 100 possessions)
- Field Goal % (FG%)
- 3-Point % (3P%)
- Free Throw % (FT%)
- Effective FG% (accounts for 3-pointers)
- True Shooting % (overall efficiency)

**Defensive Metrics:**
- Points Against per game
- Defensive Rating

**Pace & Style:**
- Pace (possessions per game)
- Assists per game
- Turnovers per game
- Rebounds per game

**Win Metrics:**
- Win percentage
- Win/Loss record

## ⚠️ Known Issues & Solutions

### Issue 1: NBA.com Stats API Timeout

**Problem:** NBA.com Stats API is heavily rate-limited and often times out

**Solution:** System has 3-tier failover:
1. NBA Official API (primary)
2. BallDontLie API (backup) - free, no key needed
3. ESPN API (backup) - free, no key needed

If all fail, system will skip that game (no fake data)

### Issue 2: Training Data Collection

**Problem:** NBA.com API may not return historical games

**Solution:** Trainer has fallback to use current season team stats to generate synthetic training data based on team matchups

### Issue 3: Team Name Matching

**Problem:** Different APIs use different team names (e.g., "LA Lakers" vs "Los Angeles Lakers")

**Solution:** Enhanced fuzzy matching in `nba_enhanced_data.py` team_map

## 🛠️ Advanced Usage

### Train with More Games

```bash
# Edit nba_enhanced_trainer.py, change line 215:
X, y = trainer.collect_enhanced_training_data(num_games=1000)  # Default is 500
```

### Generate Report for Specific Date

```bash
python3 nba_daily_report.py --date 2025-10-26
```

### Check Failover System

```bash
# Test odds failover
python3 nba_odds_api_failover.py

# Test stats failover
python3 nba_stats_api_failover.py
```

## 📁 File Descriptions

### `nba_odds_api.py`
Simple tester for The-Odds-API. Use this to verify odds API is working.

### `nba_odds_api_failover.py`
Production odds fetcher with failover:
- Primary: The-Odds-API (your paid API key)
- Backup: ESPN API

### `nba_stats_api_failover.py`
Stats fetcher with failover:
- Primary: NBA.com Official Stats
- Backup 1: BallDontLie API
- Backup 2: ESPN API

### `nba_enhanced_data.py`
Core data integration module. Fetches team stats and builds ML features:
- Team statistics (PPG, FG%, etc.)
- Advanced metrics (Offensive/Defensive Rating, Pace)
- Differential features (home vs away)

### `nba_enhanced_trainer.py`
ML model trainer:
- Collects historical games
- Builds training dataset with enhanced features
- Trains Random Forest and Gradient Boosting models
- Saves trained models to `nba_enhanced_models.pkl`

### `nba_daily_report.py`
Daily predictions generator:
- Gets today's games from NBA schedule
- Fetches real odds
- Loads trained models
- Makes predictions
- Generates CSV report

## 🔄 Automation (Future)

Once you verify the system works, you can automate it with cron:

```bash
# Add to crontab (run at 4 PM daily, before NBA games start at 7 PM)
0 16 * * * cd /Users/dickgibbons/nba/daily\ nba && python3 nba_daily_report.py
```

## 📞 Troubleshooting

### "Models not found" error
**Solution:** Run `python3 nba_enhanced_trainer.py` first to train models

### "No games found" error
**Possible causes:**
1. No NBA games scheduled for today (check NBA schedule)
2. All games already started
3. NBA API down

### "No real odds available" error
**Possible causes:**
1. The-Odds-API quota exceeded (check usage at the-odds-api.com)
2. Game too far in future (odds not posted yet)
3. Both The-Odds-API and ESPN failed

**Solution:** System will skip games without real odds (by design - no fake data)

### API timeout errors
**Solution:** This is expected with NBA.com Stats API. The failover system will try backup sources automatically.

## 📊 Recommended Markets

Based on NBA characteristics:

1. ✅ **Spreads** - Most reliable, lower variance than moneyline
2. ✅ **Totals** - More predictable than NHL (less variance in scoring)
3. ✅ **Team Totals** - Good for strong offensive/defensive teams
4. ⚠️ **Moneyline** - Avoid heavy favorites (poor value)

## 🎯 Next Steps

1. **Today:** Train the models (`python3 nba_enhanced_trainer.py`)
2. **Today:** Generate first predictions (`python3 nba_daily_report.py`)
3. **This week:** Track predictions vs actual results
4. **This month:** Analyze model performance, tune parameters
5. **Future:** Set up automation with cron

## 📈 Comparison to Your NHL System

**Similarities:**
- Same ML approach (Random Forest + Gradient Boosting)
- Same failover architecture
- Same report format
- Same betting edge calculations

**Differences:**
- NBA has more predictable scoring (lower variance)
- NBA has stronger home court advantage (~58% vs ~55%)
- NBA back-to-backs are even more impactful than NHL
- NBA has more player-specific impact (injuries matter more)

---

**Created:** October 25, 2024
**Status:** ✅ Complete - Ready to train models and generate predictions
**Next Action:** Run `python3 nba_enhanced_trainer.py`
