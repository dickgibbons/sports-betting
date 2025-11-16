# NHL Hockey Directory Structure

## Overview
The NHL Hockey directory has been organized for efficient daily operations. Active files used in automated overnight processes are in the root directory, while older/unused files are in the `archive/` folder.

---

## Active Files (Root Directory)

### Daily Automation
- **`automated_daily_system.sh`** - Main automation script (runs at 5:00 AM daily)
  - Updates models with yesterday's results
  - Retrains models on AWS
  - Generates daily predictions and reports
  - Manages cumulative tracking

- **`install_cron.sh`** - Cron job installer
- **`daily_workflow.sh`** - Manual workflow helper

### Model Files
- **`nhl_enhanced_models.pkl`** - Main game prediction models (672 KB)
  - Moneyline, spread, totals predictions
  - Updated via AWS training
  - Used by all prediction scripts

- **`nhl_goalie_models.pkl`** - Goalie saves prediction models (4.5 MB)
  - Predicts expected saves per goalie
  - Used by `daily_goalie_saves_report.py`

- **`nhl_player_models.pkl`** - Player shots prediction models (5.2 MB)
  - Predicts expected shots per player
  - Used by `daily_player_shots_report.py`

### Prediction Scripts
- **`daily_nhl_report.py`** - Daily game predictions generator
  - Called by automation script
  - Generates ML, spread, totals predictions
  - Used in overnight process

- **`bet_recommendations.py`** - Bet recommendations generator
  - Calculates implied odds and expected value
  - Ranks bets by profitability
  - Saves to reports/YYYYMMDD/

- **`top5_daily_picks.py`** - Top 5 best picks selector
  - Highlights highest-confidence bets
  - Used for quick daily review

- **`daily_player_shots_report.py`** - Player shots predictions
  - Predicts shots on goal for all players
  - Over/under recommendations
  - Season comparison data

- **`daily_goalie_saves_report.py`** - Goalie saves predictions
  - Predicts expected saves per goalie
  - Identifies likely starters
  - Save percentage projections

### Training Scripts
- **`nhl_enhanced_trainer.py`** - Main model trainer
  - Runs on AWS instance
  - Trains all game prediction models
  - Current production version

- **`nhl_player_trainer.py`** - Player shots model trainer
  - Trains player prediction models
  - Uses Random Forest ensemble

- **`nhl_goalie_trainer.py`** - Goalie saves model trainer
  - Trains goalie prediction models
  - Uses Gradient Boosting ensemble

### Performance Tracking
- **`cumulative_tracker.py`** - Performance tracker
  - Updates daily results
  - Calculates ROI, win rate
  - Manages bankroll tracking
  - Called by automation script

- **`update_model_with_results.py`** - Results fetcher
  - Fetches previous day's game results
  - Updates training data
  - Called before model training

- **`cumulative_results.csv`** - Historical bet results
  - All bets tracked with outcomes
  - Used by cumulative_tracker.py

- **`training_history.csv`** - Historical game data
  - Training dataset for models
  - Updated daily with results

### Supporting Libraries
- **`nhl_enhanced_data.py`** - Data processing library
  - Feature engineering
  - Data validation
  - Used by all scripts

- **`nhl_odds_api_failover.py`** - Odds API integration
  - The Odds API with failover
  - Used by prediction scripts

- **`nhl_stats_api_failover.py`** - NHL Stats API integration
  - Official NHL API with failover
  - Used by all data fetching

- **`nhl_goalie_fetcher.py`** - Goalie data fetcher
  - Starting goalie detection
  - Goalie stats retrieval

- **`nhl_bet_tracker.py`** - Bet tracking utilities
  - Performance calculation helpers
  - Used by cumulative tracker

### Documentation
- **`NHL_IMPLEMENTATION_SUMMARY.md`** - System implementation docs
- **`NHL_MODEL_ENHANCEMENT_SUMMARY.md`** - Model improvement history
- **`NHL_PERFORMANCE_ANALYSIS_AND_RECOMMENDATIONS.md`** - Analysis reports

---

## Directory Structure

```
/Users/dickgibbons/hockey/daily hockey/
├── automated_daily_system.sh          # Main automation
├── install_cron.sh                     # Cron installer
├── daily_workflow.sh                   # Manual workflow
│
├── daily_nhl_report.py                 # Daily game predictions (automated)
├── bet_recommendations.py              # Bet recommendations (automated)
├── top5_daily_picks.py                 # Top 5 picks (automated)
├── daily_player_shots_report.py        # Player shots predictions (automated)
├── daily_goalie_saves_report.py        # Goalie saves predictions (automated)
│
├── nhl_enhanced_trainer.py             # Main model trainer (AWS)
├── nhl_player_trainer.py               # Player model trainer (AWS)
├── nhl_goalie_trainer.py               # Goalie model trainer (AWS)
│
├── cumulative_tracker.py               # Performance tracking (automated)
├── update_model_with_results.py        # Results fetcher (automated)
│
├── nhl_enhanced_data.py                # Data processing library
├── nhl_odds_api_failover.py            # Odds API
├── nhl_stats_api_failover.py           # NHL Stats API
├── nhl_goalie_fetcher.py               # Goalie data
├── nhl_bet_tracker.py                  # Tracking utilities
│
├── nhl_enhanced_models.pkl             # Current game models (672 KB)
├── nhl_goalie_models.pkl               # Current goalie models (4.5 MB)
├── nhl_player_models.pkl               # Current player models (5.2 MB)
│
├── cumulative_results.csv              # Historical results
├── training_history.csv                # Historical training data
│
├── NHL_IMPLEMENTATION_SUMMARY.md       # Documentation
├── NHL_MODEL_ENHANCEMENT_SUMMARY.md    # Documentation
├── NHL_PERFORMANCE_ANALYSIS_AND_RECOMMENDATIONS.md
├── DIRECTORY_STRUCTURE.md              # This file
│
├── logs/                                # Daily automation logs
├── reports/                             # Daily prediction reports
├── models/                              # Model versioning
└── archive/                             # Old/unused files
```

---

## Overnight Automation Process

1. **5:00 AM** - Cron triggers `automated_daily_system.sh`
2. **Fetch Results** - Run `update_model_with_results.py` to get yesterday's results
3. **Update Tracking** - Run `cumulative_tracker.py` to update performance metrics
4. **Model Training** - SSH to AWS, run all trainers:
   - `nhl_enhanced_trainer.py` (game predictions)
   - `nhl_player_trainer.py` (player shots)
   - `nhl_goalie_trainer.py` (goalie saves)
5. **Model Download** - Download updated models from AWS
6. **Generate Predictions**:
   - `daily_nhl_report.py` - Game predictions
   - `bet_recommendations.py` - Bet recommendations
   - `top5_daily_picks.py` - Top 5 picks
   - `daily_player_shots_report.py` - Player shots
   - `daily_goalie_saves_report.py` - Goalie saves
7. **Save Reports** - Move CSVs to `reports/YYYYMMDD/`
8. **Logging** - Save log to `logs/daily_automation_YYYYMMDD.log`

---

## Manual Daily Workflow

For best betting results, review these reports manually:

```bash
# View today's reports (auto-generated overnight)
ls -lh reports/$(date +%Y%m%d)/

# Files available:
# - nhl_daily_report_YYYY-MM-DD.csv          (game predictions)
# - bet_recommendations_YYYY-MM-DD.csv       (recommended bets with EV)
# - top5_best_bets_YYYY-MM-DD.csv            (top 5 picks)
# - player_shots_predictions_YYYY-MM-DD.csv  (player shots)
# - goalie_saves_predictions_YYYY-MM-DD.csv  (goalie saves)

# Manually regenerate if needed:
python3 daily_nhl_report.py
python3 bet_recommendations.py
python3 top5_daily_picks.py
python3 daily_player_shots_report.py
python3 daily_goalie_saves_report.py

# View cumulative performance:
python3 cumulative_tracker.py
```

---

## Archive Directory

Contains **~50 old/unused files:**

### Old Model Files
- `nhl_models_enhanced_params.pkl` - Old enhanced params version (31 MB)
- `nhl_models_with_totals_b2b.pkl` - Old B2B version
- `nhl_models_with_totals_b2b_splits.pkl` - Old B2B splits version
- 17 backup model files (`nhl_enhanced_models_backup_*.pkl`)

### Old Scripts
- `bet_recommendations_with_totals.py` - Old bet recommendations
- `bet_recommendations_enhanced.py` - Old enhanced version
- `nhl_trainer_enhanced_params.py` - Old trainer
- `nhl_trainer_with_totals_b2b.py` - Old B2B trainer
- `nhl_trainer_with_totals_b2b_splits.py` - Old B2B splits trainer
- `nhl_enhanced_data_with_splits.py` - Old data library
- `quick_train_player_goalie.py` - Test script
- `test_totals_b2b_predictions.py` - Test script
- `nhl_quick_backtest.py` - Backtest script
- `nhl_historical_backtest.py` - Historical backtest
- `hockey_api.py` - Old API file
- `hockey_config.py` - Old config

### Old Data/Reports
- Old dated CSVs: `bet_recommendations_2025-10-*.csv`
- Old predictions: `nhl_daily_report_2025-10-*.csv`
- Old player/goalie reports from Oct 14-16
- Old cumulative summaries
- Old backtest results

**Note:** Archive files are kept for reference but not used in daily operations.

---

## File Sizes

**Active Models:**
- Game models: 672 KB
- Goalie models: 4.5 MB
- Player models: 5.2 MB
- Scripts: ~150 KB total
- Data: ~100 KB
- Docs: ~50 KB

**Directories:**
- Archive: 40 MB
- Reports: 404 KB
- Logs: 936 KB

---

## Key Points

1. **26 active files** in root directory (plus 4 directories)
2. **~50 archived files** no longer needed daily
3. **Clean automation** - all overnight processes use current files
4. **Easy maintenance** - active files clearly separated
5. **Preserved history** - old files available in archive if needed
6. **Comprehensive predictions** - Game, player, and goalie models

---

## Model Performance Tracking

Current system performance (as of Oct 24, 2025):
- **Bankroll**: $885.32 (from $1,000 start)
- **Record**: 16W-14L (53.3% win rate)
- **ROI**: -11.47%
- **Total Bets**: 30

Performance data tracked in:
- `cumulative_results.csv` - All historical bets
- `reports/YYYYMMDD/cumulative_summary_*.csv` - Daily snapshots

---

Last Updated: October 24, 2025
