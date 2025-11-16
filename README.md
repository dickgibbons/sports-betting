# Sports Betting System

Unified sports betting analysis system with ML predictions and angle-based analysis.

## Directory Structure

```
sports-betting/
├── core/                   # Shared infrastructure
│   ├── bet_tracker.py     # Bet tracking and performance monitoring
│   ├── hybrid_predictor.py # ML + Angle hybrid predictions
│   ├── daily_hybrid_report.py # Main daily report generator
│   └── ...
│
├── nba/                    # NBA-specific code
│   ├── ml_system/         # XGBoost ML prediction system
│   ├── analyzers/         # NBA angle analyzers
│   ├── data/              # NBA team profiles
│   └── reports/           # NBA-specific reports
│
├── nhl/                    # NHL-specific code
│   ├── analyzers/         # NHL angle analyzers
│   ├── first_period/      # First period analysis
│   ├── data/              # NHL team profiles
│   └── reports/           # NHL-specific reports
│
├── soccer/                 # Soccer-specific code
│   ├── analyzers/
│   ├── data/
│   └── reports/
│
├── ncaa/                   # NCAA basketball code
│   ├── analyzers/
│   ├── data/
│   └── reports/
│
├── data/                   # Shared data
│   ├── bet_history.json   # All bet history
│   ├── angle_weights.json # Learned angle weights
│   └── team_profiles/     # Team-specific data
│
└── reports/                # All daily reports
    └── report_YYYY-MM-DD.txt
```

## Current Performance

- **Overall**: 33-43 (43.4%), Bankroll: $8,661 (-13.4%)
- **NHL**: 18-15 (54.5%), +$543 📈
- **NBA**: 15-28 (34.9%), -$1,882 📉

## Quick Start

```bash
cd ~/sports-betting/core
python3 daily_hybrid_report.py
```

## Recent Updates

- **Nov 15, 2025**: Integrated Expected Value (EV) filtering for NBA
- Now using ML-first approach for NBA (analyzes all games, not just angle opportunities)
- Positive EV requirement filters out heavy favorites with no value

