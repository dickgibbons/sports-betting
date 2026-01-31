# File Organization Summary

This document describes the new organized structure for betting strategy files.

## 📁 New Directory Structure

### **NHL (Hockey) Organization**

```
nhl/
├── strategies/          # Daily betting strategy scripts (used in run_nhl_daily.sh)
│   ├── daily_nhl_report.py
│   ├── nhl_first_period_daily_report.py
│   ├── daily_goalie_saves_report.py
│   ├── daily_player_shots_report.py
│   ├── nhl_daily_b2b_finder.py
│   ├── top5_daily_picks.py
│   ├── nhl_daily_totals_report.py
│   ├── nhl_totals_strategy.py
│   ├── generate_1p_trend_reports.py
│   └── *.pkl            # Model files (nhl_enhanced_models.pkl, etc.)
│
├── utils/               # Utility modules (imported by strategies)
│   ├── nhl_enhanced_data.py
│   ├── nhl_odds_api_failover.py
│   ├── nhl_stats_api_failover.py
│   ├── nhl_goalie_fetcher.py
│   ├── nhl_game_cache.py
│   ├── nhl_ml_totals_predictor.py
│   ├── nhl_bet_tracker.py
│   └── cumulative_tracker.py
│
├── models/              # Backup/archived model files
├── training/            # Model training scripts (not used in daily runs)
│   ├── nhl_enhanced_trainer.py
│   ├── nhl_goalie_trainer.py
│   ├── nhl_player_trainer.py
│   └── update_model_with_results.py
│
├── analysis/            # Analysis/backtest scripts (not used in daily runs)
│   ├── nhl_betting_angles_analyzer.py
│   ├── nhl_schedule_analyzer.py
│   ├── nhl_rest_advantage_analyzer.py
│   ├── nhl_road_trip_backtest.py
│   ├── nhl_sog_props_analyzer.py
│   ├── nhl_value_bets_analyzer.py
│   ├── nhl_team_scoring_streaks.py
│   ├── nhl_goals_moving_average.py
│   └── nhl_daily_matchup_ma_report.py
│
└── docs/                # Documentation files
```

### **Soccer Organization**

```
soccer/
├── strategies/          # Daily betting strategy scripts (used in run_soccer_daily.sh)
│   ├── soccer_daily_profitable_report.py  (PRIMARY - Step 0)
│   ├── soccer_best_bets_daily.py          (Step 1)
│   ├── corners_analyzer.py                (Step 2)
│   └── first_half_analyzer.py             (Step 3)
│
├── utils/               # Utility modules (imported by strategies)
│   ├── team_form_fetcher.py
│   ├── team_stats_cache.py
│   ├── footystats_api.py
│   └── prophitbet_ensemble.py
│
├── models/              # Trained ML models
│   ├── soccer_ml_models_with_form.pkl
│   ├── soccer_ml_models_enhanced.pkl
│   ├── soccer_ml_models.pkl
│   ├── calibration_params.pkl
│   └── prophitbet_ensemble/
│
├── data/                # Data files and caches
│   ├── team_stats_cache.db
│   └── soccer_historical.db
│
├── training/            # Model training scripts
│   └── soccer_trainer_all_totals.py
│
├── analysis/            # Analysis/backtest scripts
│   ├── soccer_betting_angles_analyzer_v2.py
│   ├── soccer_betting_angles_analyzer.py
│   ├── soccer_bet_tracker.py
│   ├── comprehensive_backtest.py
│   ├── corners_backtest.py
│   ├── first_half_backtest.py
│   ├── full_market_backtest.py
│   ├── soccer_angle_investigation.py
│   └── soccer_profitable_angles_model.py
│
└── docs/                # Documentation files
```

### **Archive Structure**

```
archive/
├── nhl-unused/          # Unused/legacy NHL files
├── soccer-unused/       # Unused/legacy soccer files
├── core-unused/         # Unused core files
└── root-unused/         # Unused root-level scripts
```

## 🔄 Updated Run Scripts

### **run_nhl_daily.sh**
- Changed working directory from `nhl/analyzers/` to `nhl/strategies/`
- All strategy scripts now run from the strategies directory

### **run_soccer_daily.sh**
- Changed working directory from `soccer/investigation/` and `soccer/analyzers/daily soccer/` to `soccer/strategies/`
- All strategy scripts now run from the strategies directory

## 📝 Import Path Updates

All Python scripts have been updated to:
- Import utility modules from `{sport}/utils/`
- Reference model files in `{sport}/strategies/` (for daily scripts) or `{sport}/models/`
- Use proper sys.path modifications to find dependencies

## ✅ What Changed

### **Moved Files:**
- **NHL**: 9 strategy scripts, 8 utility modules → organized by function
- **Soccer**: 4 strategy scripts, 4 utility modules → organized by function
- **Core**: Sport-specific analyzers moved to respective sport folders
- **Root**: `generate_1p_trend_reports.py` moved to `nhl/strategies/`

### **Archived Files:**
- Old output files (CSV, TXT reports)
- Legacy scripts no longer used in daily runs
- Training/analysis scripts moved to dedicated folders
- Documentation moved to `docs/` folders

## 🎯 Benefits

1. **Clear Separation**: Daily strategies vs. training vs. analysis
2. **Easy Navigation**: Find files by purpose (strategy, utility, training, analysis)
3. **Reduced Clutter**: Unused files archived
4. **Sport Organization**: Each sport has its own complete structure
5. **Maintainable**: Easy to add new strategies or utilities

## 📌 Notes

- Model files (`.pkl`) used by daily scripts remain in `strategies/` for easy access
- Utility modules are separate to allow reuse across multiple strategies
- All scripts maintain backward compatibility with existing data paths
- Report output locations remain unchanged (still go to `reports/YYYY-MM-DD/`)
