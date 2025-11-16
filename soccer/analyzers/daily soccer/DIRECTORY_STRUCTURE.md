# Soccer Betting Directory Structure

## Overview
The Soccer Betting directory has been organized for efficient daily operations. Active files used for daily predictions are in the root directory, while backtest scripts, analysis tools, and old files are in the `archive/` folder.

---

## Active Files (Root Directory)

### Daily Prediction Scripts
- **`soccer_best_bets_daily.py`** - Main daily predictions generator
  - Generates BTTS (Both Teams To Score) predictions
  - Analyzes betting value and edge
  - Produces daily bet recommendations
  - Uses FootyStats API for live data

### Training Scripts
- **`soccer_trainer_all_totals.py`** - Model trainer
  - Trains all soccer prediction models
  - Supports multiple markets (BTTS, Over/Under, Match Result)
  - Uses Random Forest and Gradient Boosting ensembles
  - Current production trainer

### Supporting Libraries
- **`footystats_api.py`** - FootyStats API integration
  - Handles API authentication and rate limiting
  - Fetches live match data
  - Provides historical data for training
  - Used by all prediction scripts

- **`team_form_fetcher.py`** - Team form data fetcher
  - Retrieves recent team performance
  - Calculates form metrics
  - Supports feature engineering

- **`team_stats_cache.py`** - Team statistics cache
  - Caches frequently accessed team data
  - Reduces API calls
  - Improves performance

- **`soccer_bet_tracker.py`** - Bet tracking utilities
  - Performance calculation helpers
  - ROI tracking
  - Bankroll management

### Data Files
- **`soccer_cumulative_performance.csv`** - Historical bet results
  - All bets tracked with outcomes
  - Performance metrics
  - Used for cumulative analysis

### Model Files
- **`models/soccer_ml_models_with_form.pkl`** - Current production models (44 MB)
  - BTTS predictions
  - Over/Under predictions
  - Match result predictions
  - Trained with team form features

- **`models/calibration_params.pkl`** - Model calibration parameters (1.8 KB)
  - Probability calibration settings
  - Used to adjust prediction confidence

### Configuration
- **`requirements.txt`** - Python dependencies
  - All required packages
  - Version specifications

### Documentation
- **`README.md`** - System overview and usage
- **`QUICK_START.md`** - Quick start guide
- **`training_all_totals.log`** - Recent training log

---

## Directory Structure

```
/Users/dickgibbons/soccer-betting-python/daily soccer/
├── soccer_best_bets_daily.py           # Daily predictions (manual run)
├── soccer_trainer_all_totals.py        # Model trainer
│
├── footystats_api.py                   # API integration
├── team_form_fetcher.py                # Form data fetcher
├── team_stats_cache.py                 # Stats cache
├── soccer_bet_tracker.py               # Tracking utilities
│
├── soccer_cumulative_performance.csv   # Historical results
├── training_all_totals.log             # Recent training log
│
├── requirements.txt                    # Dependencies
├── README.md                           # Documentation
├── QUICK_START.md                      # Quick start guide
├── DIRECTORY_STRUCTURE.md              # This file
│
├── models/                              # Model files
│   ├── soccer_ml_models_with_form.pkl   # Current models (44 MB)
│   └── calibration_params.pkl           # Calibration params (1.8 KB)
│
├── data/                                # Training data
└── archive/                             # Old/unused files (496 MB)
```

---

## Daily Workflow

For daily soccer betting predictions:

```bash
# Change to soccer directory
cd "/Users/dickgibbons/soccer-betting-python/daily soccer"

# Generate daily predictions
python3 soccer_best_bets_daily.py
```

---

## Training Workflow

To retrain models with updated data:

```bash
# Change to soccer directory
cd "/Users/dickgibbons/soccer-betting-python/daily soccer"

# Train models (can take 30-60 minutes)
python3 soccer_trainer_all_totals.py

# Models saved to models/soccer_ml_models_with_form.pkl
# Training log: training_all_totals.log
```

---

## Archive Directory

Contains **77 old/unused files** (496 MB total):

### Backtest Scripts
- `aws_backtest_soccer.py` - AWS backtest runner
- `footystats_backtest_soccer.py` - FootyStats backtest
- `backtest_historical_2024.py` - Historical backtest
- `backtest_historical_2024_relaxed.py` - Relaxed threshold backtest
- `backtest_calibrated_2024.py` - Calibrated backtest
- `check_backtest.py` - Backtest checker

### Analysis Scripts
- `analyze_backtest_by_league.py` - League-specific analysis
- `analyze_thresholds.py` - Threshold analysis
- `analyze_volume_control.py` - Volume control analysis
- `calibrate_models.py` - Model calibration
- `rebuild_cumulative_history.py` - History rebuilder
- `test_api_team_stats.py` - API testing

### Old Trainers
- `soccer_trainer_enhanced.py` - Old enhanced trainer
- `soccer_trainer_with_form.py` - Old form trainer
- `improved_betting_predictor.py` - Old predictor
- `improved_daily_manager.py` - Old daily manager
- `streamlined_daily_generator.py` - Old generator
- `soccer_best_bets_enhanced.py` - Old enhanced version

### AWS Deployment Scripts
- `aws_run_backtest.sh` - AWS backtest runner
- `aws_train_enhanced_soccer.sh` - AWS trainer
- `deploy_to_aws.sh` - Deployment script
- `quick_deploy_aws.sh` - Quick deploy script
- `check_backtest.sh` - Backtest checker
- `test_backtest_short.sh` - Short backtest test
- `aws_connection_info.txt` - AWS credentials

### Old Documentation
- `AWS_BACKTEST_SETUP.md`
- `AWS_DEPLOYMENT_INSTRUCTIONS.md`
- `AWS_INSTANCE_INFO.md`
- `BACKTEST_ANALYSIS_SUMMARY.md`
- `BACKTEST_FINAL_ANALYSIS.md`
- `BACKTEST_README.md`
- `BACKTEST_SUMMARY.md`
- `CALIBRATION_SUMMARY.md`
- `ENHANCED_MODELS_README.md`
- `FINAL_STATUS.md`
- `FOOTYSTATS_BACKTEST_README.md`
- `LEAGUE_ANALYSIS_RESULTS.md`
- `PHASE_2_IMPLEMENTATION_STATUS.md`
- `README_BACKTEST_LIMITATION.md`
- `SOCCER_IMPROVEMENT_STRATEGIES.md`
- `STEPS_1-4_COMPLETE.md`
- `TEAM_FORM_FEATURES_DESIGN.md`

### Old Backtest Results
- Backtest logs: `backtest_2024_full.log`, `backtest_all_markets_full.log`, `backtest_calibrated_full_2024.log`, etc.
- Backtest CSVs: `backtest_2024_relaxed_daily.csv`, `backtest_2024_relaxed_detailed.csv`, etc.
- Backtest charts: `footystats_backtest_charts_*.png`
- FootyStats data: `footystats_backtest_daily_*.csv`, `footystats_backtest_detailed_*.csv`

### Old Model Files
- `improved_soccer_models.pkl` (18 MB)
- `multi_league_models.pkl` (5.7 MB)
- `multi_market_models.pkl` (65 MB)
- `soccer_ml_models_aws.pkl` (332 KB)
- `soccer_ml_models_enhanced.pkl` (149 MB)
- `soccer_ml_models.pkl` (31 MB)
- `soccer_prediction_models.pkl` (1.5 MB)
- Multiple backup files: `soccer_ml_models_backup_*.pkl`
- Enhanced backups: `soccer_ml_models_enhanced_backup_*.pkl`
- Form model backups: `soccer_ml_models_with_form_backup_*.pkl`

### Other Archives
- `calibration_plots/` directory - Old calibration visualizations

**Note:** Archive files are kept for reference but not used in daily operations.

---

## File Sizes

**Active Files:**
- Scripts: ~45 KB total
- API libraries: ~15 KB
- Data: ~10 KB
- Documentation: ~8 KB

**Models:**
- Current models: 44 MB
- Calibration: 1.8 KB
- Total: 44 MB

**Directories:**
- Archive: 496 MB (77 files)
- Data: Cached team stats
- Models: 44 MB

---

## Key Points

1. **12 active files** in root directory (plus 3 subdirectories)
2. **77 archived files** no longer needed daily (496 MB)
3. **Clean workflow** - only essential production files in root
4. **Easy maintenance** - active files clearly separated from backtest/analysis tools
5. **Preserved history** - old files and backtest results available in archive if needed
6. **FootyStats API** - Live data integration for predictions
7. **Streamlined structure** - moved up one level for easier access

---

## Model Performance

Current system focuses on:
- **BTTS (Both Teams To Score)** - Primary market
- **Over/Under Goals** - Secondary market
- **Match Result** - Tertiary market

Models trained with:
- Random Forest (100 estimators)
- Gradient Boosting (100 estimators)
- 36+ features including odds, team stats, form data
- Cross-validation for accuracy

Typical performance:
- 7-10 bets per day
- 99% confidence threshold
- Value-based selection using Kelly Criterion

---

## API Integration

**FootyStats API:**
- League: Premier League (ID: 1625) and others
- Rate Limiting: 1 second between requests
- Request Limit: 1800 per hour
- Data Points: 380+ historical matches for training

**Configuration:**
- API key stored in environment or script
- Automatic retry with failover
- Response caching for efficiency

---

## Dependencies

Key Python packages (see `requirements.txt`):
- `requests` - API calls
- `scikit-learn` - Machine learning
- `numpy` - Numerical computing
- `pandas` - Data manipulation (optional)
- `joblib` - Model serialization

---

Last Updated: October 24, 2025
