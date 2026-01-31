# Daily Run Files & Folders Explained

This document explains what files and folders are used when running daily hockey (NHL) and soccer reports.

---

## 🏒 **NHL (Hockey) Daily Run**

**Entry Point:** `run_nhl_daily.sh`

### **Main Directories:**

#### 1. **`nhl/analyzers/`** - Core NHL Analysis Scripts
This is where most NHL analysis happens. The daily script runs these scripts in order:

- **`daily_nhl_report.py`** - Main NHL betting report generator
  - Uses models: `nhl_enhanced_models.pkl`
  - Imports: `nhl_enhanced_data.py`, `nhl_odds_api_failover.py`, `nhl_stats_api_failover.py`
  - Outputs: `nhl_daily_report_*.csv` files

- **`nhl_first_period_daily_report.py`** - First period analysis
  - Outputs to: `/Users/dickgibbons/betting_data/nhl_1p_daily_report.json` and `.csv`

- **`daily_goalie_saves_report.py`** - Goalie saves predictions
  - Uses models: `nhl_goalie_models.pkl`
  - Outputs: `nhl_goalie_saves_YYYY-MM-DD.txt`

- **`daily_player_shots_report.py`** - Player shots predictions
  - Uses models: `nhl_player_models.pkl`
  - Outputs: Player shots reports

- **`nhl_daily_b2b_finder.py`** - Back-to-back scheduling opportunities
  - Outputs: `nhl_b2b_opportunities_YYYY-MM-DD.txt`

- **`top5_daily_picks.py`** - Top 5 NHL picks of the day
  - Outputs: `nhl_top5_picks_YYYY-MM-DD.txt`

- **`nhl_daily_totals_report.py`** - ML-based totals predictions
  - Uses models: `nhl_totals_models.pkl`
  - Outputs: Totals predictions

#### 2. **`nhl/models/`** - Trained Machine Learning Models
Contains all the pickle (.pkl) model files:
- `nhl_1p_models.pkl` - First period models
- `totals_*.pkl` - Various totals models (gradient_boost, linear, random_forest, ridge, xgboost)
- `first_period_*.pkl` - First period specific models
- Other model files

#### 3. **`nhl/` (root level)**
- **`nhl_totals_strategy.py`** - Full game totals strategy (Over/Under)
  - Outputs: `nhl/nhl_totals_picks_YYYY-MM-DD.json` and `.txt`

#### 4. **Project Root Scripts**
- **`generate_1p_trend_reports.py`** - Generates NHL 1P trend reports
  - Outputs to: `/Users/dickgibbons/Daily Reports/YYYY-MM-DD/`

### **Data Directories:**

#### 5. **`data/`** - Shared Data Files
- `nhl_game_cache.db` - NHL game data cache (SQLite database)
- `nhl_1p_daily_report.json` - First period daily report data
- `nhl_first_period_stats.json` - First period statistics

#### 6. **`reports/`** - Generated Reports
- `reports/YYYY-MM-DD/` - Date-organized report files
  - All NHL reports are copied here after generation

#### 7. **External Output Locations:**
- `/Users/dickgibbons/betting_data/` - NHL 1P reports saved here
- `/Users/dickgibbons/Daily Reports/YYYY-MM-DD/` - Final daily reports destination

### **Output Files Created:**

When `run_nhl_daily.sh` runs, it creates:
1. `nhl_daily_report_*.csv` - Main betting report
2. `nhl_first_period_*.txt` and `.csv` - First period analysis
3. `nhl_goalie_saves_YYYY-MM-DD.txt` - Goalie predictions
4. `nhl_b2b_opportunities_YYYY-MM-DD.txt` - Back-to-back opportunities
5. `nhl_top5_picks_YYYY-MM-DD.txt` - Top 5 picks
6. `nhl_totals_picks_YYYY-MM-DD.json` and `.txt` - Totals strategy picks
7. `nhl_1p_*trend*.csv` - 1P trend reports (in Daily Reports folder)

---

## ⚽ **Soccer Daily Run**

**Entry Point:** `run_soccer_daily.sh`

### **Main Directories:**

#### 1. **`soccer/investigation/`** - Profitable Angles Analysis
- **`soccer_daily_profitable_report.py`** - **PRIMARY REPORT** (Step 0)
  - Shows all games in profitable leagues (Bundesliga, EPL, MLS, Eredivisie, La Liga, Serie A)
  - Based on 7,272 match analysis (2023-2025 seasons)
  - Outputs: Reports with confidence percentages for each bet type

#### 2. **`soccer/analyzers/daily soccer/`** - Daily Soccer Analysis Scripts
The main analysis directory:

- **`soccer_best_bets_daily.py`** - Main best bets generator (Step 1)
  - Uses models from `models/`:
    - `soccer_ml_models_with_form.pkl` (primary)
    - `soccer_ml_models_enhanced.pkl` (fallback)
    - `soccer_ml_models.pkl` (fallback)
    - `calibration_params.pkl` - Calibration parameters
  - Uses ProphitBet ensemble: `models/prophitbet_ensemble/prophitbet_xgb_ensemble.pkl`
  - Imports: `team_form_fetcher.py`, `prophitbet_ensemble.py`
  - Outputs to: `reports/YYYYMMDD/` subdirectory

- **`corners_analyzer.py`** - Corners over/under analysis (Step 2)
  - Outputs: Corners analysis reports

- **`first_half_analyzer.py`** - First half predictions (Step 3)
  - Outputs: First half analysis reports

#### 3. **`soccer/analyzers/daily soccer/models/`** - Trained Models
Contains ML models:
- `soccer_ml_models_with_form.pkl` - Primary model with team form
- `soccer_ml_models_enhanced.pkl` - Enhanced version
- `soccer_ml_models.pkl` - Standard model
- `calibration_params.pkl` - Model calibration parameters
- `prophitbet_ensemble/prophitbet_xgb_ensemble.pkl` - ProphitBet ensemble model

#### 4. **`soccer/analyzers/daily soccer/data/`** - Data Cache
- `team_stats_cache.db` - SQLite database for team statistics cache

#### 5. **`soccer/investigation/data/`** - Investigation Data
- `soccer_historical.db` - Historical soccer match database

#### 6. **`soccer/analyzers/daily soccer/reports/`** - Generated Reports
- `reports/YYYYMMDD/` - Date-organized subdirectories
  - Contains: `soccer_best_bets_YYYY-MM-DD.txt`, JSON files, etc.
  - Reports are copied from here to main reports directory

#### 7. **`soccer/analyzers/daily soccer/Soccer reports/`** - Legacy Reports Location
Contains historical reports organized by date (20251014, 20251016, etc.)

### **Data Directories:**

#### 8. **`soccer/data/`** - Soccer Data Files
- May contain additional soccer-specific data files

#### 9. **`reports/`** - Generated Reports (Same as NHL)
- `reports/YYYY-MM-DD/` - Date-organized report files
  - Soccer reports are copied here after generation

#### 10. **External Output Locations:**
- `/Users/dickgibbons/Daily Reports/YYYY-MM-DD/` - Final daily reports destination
  - Soccer reports copied here: `soccer_*` files

### **Output Files Created:**

When `run_soccer_daily.sh` runs, it creates:
1. Profitable angles report (from `soccer/investigation/`)
2. `soccer_best_bets_*.txt` - Best bets report (BTTS, Totals)
3. `soccer_*_YYYY-MM-DD.json` - JSON format reports
4. Corners analysis reports
5. First half analysis reports

---

## 🔄 **Shared Resources (Both Sports)**

### **Core Modules (`core/`):**
- Used by post-processing scripts
- `generate_sport_picks.py` - Generates sport-specific picks files
- `daily_reports_runner.py` - Unified cross-sport report generator

### **Logs:**
- `logs/` - All daily run logs
  - `nhl_daily_YYYYMMDD_HHMMSS.log`
  - `soccer_daily_YYYYMMDD_HHMMSS.log`

### **Database:**
- `betting_tracker.db` - Unified betting tracking database (SQLite)
  - Used by `log_daily_predictions.py` and `track_performance.py`

### **Performance Tracking:**
- `performance_reports/` - Cumulative performance CSVs
  - `nhl_cumulative_performance.csv`
  - `soccer_cumulative_performance.csv`

---

## 📋 **Execution Flow**

### **NHL Flow:**
1. `run_nhl_daily.sh` → Calls scripts in `nhl/analyzers/`
2. Scripts load models from `nhl/models/` or `nhl/analyzers/`
3. Scripts use data from `data/nhl_game_cache.db`
4. Reports generated in `nhl/analyzers/` or `nhl/`
5. Reports copied to `reports/YYYY-MM-DD/`
6. Reports copied to `/Users/dickgibbons/Daily Reports/YYYY-MM-DD/`

### **Soccer Flow:**
1. `run_soccer_daily.sh` → Calls scripts in `soccer/investigation/` and `soccer/analyzers/daily soccer/`
2. Scripts load models from `soccer/analyzers/daily soccer/models/`
3. Scripts use data from `soccer/analyzers/daily soccer/data/team_stats_cache.db`
4. Reports generated in `soccer/analyzers/daily soccer/reports/YYYYMMDD/`
5. Reports copied to `reports/YYYY-MM-DD/`
6. Reports copied to `/Users/dickgibbons/Daily Reports/YYYY-MM-DD/`

---

## 🗂️ **Key File Types**

- **`.pkl`** - Pickled Python objects (trained ML models)
- **`.db`** - SQLite databases (cached data)
- **`.json`** - JSON data files (reports, configuration)
- **`.csv`** - CSV reports (betting recommendations)
- **`.txt`** - Text reports (human-readable betting picks)
- **`.log`** - Log files (execution logs)

---

## 🔑 **Important Notes**

1. **Model Files Must Exist:** The scripts will fail if required `.pkl` model files are missing
2. **API Keys:** Scripts use hardcoded API keys or environment variables for external APIs
3. **Date Format:** Most scripts use `YYYY-MM-DD` format for dates
4. **Report Organization:** Reports are organized by date in both `reports/YYYY-MM-DD/` and `/Users/dickgibbons/Daily Reports/YYYY-MM-DD/`
5. **Cache Databases:** Both systems use SQLite databases to cache API data and reduce API calls
