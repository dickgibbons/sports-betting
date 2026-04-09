# Claude Code Instructions - Sports Betting System

**IMPORTANT: Read this file first when user says "run sports betting" or asks about the sports betting system.**

---

## QUICK START - "RUN SPORTS BETTING"

When the user says **"run sports betting"**, do the following:

### Step 1: Launch All 5 Dashboards

```bash
cd /Users/dickgibbons/AI Projects/sports-betting

# Kill any existing dashboard processes
pkill -f "hockey_dashboard|soccer_dashboard|streamlit.*850"

# Wait for cleanup
sleep 2

# 1. Hockey Dashboard (port 8501) - Flask
nohup python3 dashboards/hockey/hockey_dashboard.py > logs/hockey_dashboard.log 2>&1 &

# 2. Soccer Dashboard (port 8502) - Flask
nohup python3 dashboards/soccer/soccer_dashboard.py > logs/soccer_dashboard.log 2>&1 &

# 3. NHL 1P Totals Dashboard (port 8505) - Streamlit
nohup streamlit run dashboards/nhl/nhl_1p_totals_ui.py --server.port 8505 --server.headless true > logs/nhl_dashboard.log 2>&1 &

# 4. Global Soccer Schedule Dashboard (port 8506) - Streamlit
nohup streamlit run dashboards/soccer/global_schedule_dashboard.py --server.port 8506 --server.headless true > logs/global_schedule_dashboard.log 2>&1 &

# 5. Performance Dashboard - Command-line only
# Run manually: python3 dashboards/performance/view_performance_by_sport.py
```

### Step 2: Run Daily Selections

```bash
cd /Users/dickgibbons/AI Projects/sports-betting

# Run Soccer Daily Selections
./run_soccer_daily.sh

# Run NHL/Hockey Daily Selections
./run_nhl_daily.sh
```

### Step 3: Verify Everything is Running

```bash
# Check all dashboard ports
lsof -i :8501 -i :8502 -i :8505 -i :8506 | grep LISTEN

# Test HTTP responses
curl -s -o /dev/null -w "Hockey (8501): %{http_code}\n" http://127.0.0.1:8501
curl -s -o /dev/null -w "Soccer (8502): %{http_code}\n" http://127.0.0.1:8502
curl -s -o /dev/null -w "NHL 1P (8505): %{http_code}\n" http://127.0.0.1:8505
curl -s -o /dev/null -w "Global Soccer (8506): %{http_code}\n" http://127.0.0.1:8506
```

### Step 4: Report to User

After completing steps 1-3, tell the user:

> All dashboards are running:
> - Hockey Dashboard: http://127.0.0.1:8501
> - Soccer Dashboard: http://127.0.0.1:8502
> - NHL 1P Totals: http://127.0.0.1:8505
> - Global Soccer Schedule (Enhanced Odds): http://127.0.0.1:8506
>
> Daily selections have been generated for soccer and hockey.
> Reports are in: `/Users/dickgibbons/AI Projects/sports-betting/reports/YYYY-MM-DD/`

---

## DASHBOARD REFERENCE

| Dashboard | Port | Type | File Path | Purpose |
|-----------|------|------|-----------|---------|
| Hockey | 8501 | Flask | `dashboards/hockey/hockey_dashboard.py` | International hockey schedule + team stats (20+ leagues) |
| Soccer | 8502 | Flask | `dashboards/soccer/soccer_dashboard.py` | Soccer schedule + team stats (50+ leagues) |
| NHL 1P Totals | 8505 | Streamlit | `dashboards/nhl/nhl_1p_totals_ui.py` | NHL first period totals analysis with charts |
| Global Soccer Schedule | 8506 | Streamlit | `dashboards/soccer/global_schedule_dashboard.py` | Enhanced soccer stats + American odds (see details below) |
| Performance | CLI | Python | `dashboards/performance/view_performance_by_sport.py` | Cumulative performance tracking (run manually) |

### Global Soccer Schedule Dashboard - Column Details

The Global Soccer Schedule dashboard (port 8506) displays comprehensive team statistics with the following columns:

**Basic Info:**
- Match, Time, Country, League, Location, Team

**Records & Standings:**
- Record (W-D-L overall)
- H/A Record (home or away specific)
- Standing (position/total points, e.g., "2/32pts")
- Avg GF, Avg GA (average goals for/against)

**BTTS (Both Teams To Score):**
- BTTS - % in last 10 games overall
- BTTS L5 - % in last 5 games
- BTTS H/A - % in last 10 home games (for home team) or away games (for away team)

**Game Totals (Over percentages):**
- Ov 1.5, Ov 2.5, Ov 3.5 - % of games over 1.5/2.5/3.5 total goals (overall)
- Ov 1.5 H/A, Ov 2.5 H/A, Ov 3.5 H/A - same but home/away specific

**Team Totals (Goals the team scores):**
- Team Ov 1.5, Team Ov 2.5 - % team scored 2+/3+ goals (overall)
- Team Ov 1.5 H/A, Team Ov 2.5 H/A - same but home/away specific

**Other:**
- 1H Score% - % team scored in first half

**Odds (American format):**
- H Odds, D Odds, A Odds - Home/Draw/Away in American odds (e.g., -150, +200)

**To refresh team stats data:**
```bash
cd /Users/dickgibbons/AI Projects/sports-betting/dashboards/soccer
python3 team_stats_collector.py
```

---

## DAILY SELECTION SCRIPTS

### Soccer Daily Pipeline (`./run_soccer_daily.sh`)

Runs 4 scripts in order from `/Users/dickgibbons/AI Projects/sports-betting/soccer/strategies/`:

1. **soccer_daily_profitable_report.py** - Analyzes profitable leagues (Bundesliga, EPL, MLS, etc.)
2. **soccer_best_bets_daily.py** - Main best bets (BTTS, Totals) using ML models
3. **corners_analyzer.py** - Corners over/under predictions
4. **first_half_analyzer.py** - First half match predictions

**Output**: `soccer/strategies/reports/YYYYMMDD/` and `reports/YYYY-MM-DD/`

**Models Used** (in `soccer/strategies/models/`):
- `soccer_ml_models_with_form.pkl`
- `prophitbet_xgb_ensemble.pkl`

### NHL/Hockey Daily Pipeline (`./run_nhl_daily.sh`)

Runs 9 scripts in order from `/Users/dickgibbons/AI Projects/sports-betting/nhl/strategies/`:

1. **daily_nhl_report.py** - Main NHL predictions
2. **nhl_first_period_daily_report.py** - 1P analysis
3. **daily_goalie_saves_report.py** - Goalie saves predictions
4. **daily_player_shots_report.py** - Player shots predictions
5. **nhl_daily_b2b_finder.py** - Back-to-back opportunities
6. **top5_daily_picks.py** - Top 5 picks of the day
7. **nhl_daily_totals_report.py** - ML totals predictions
8. **generate_1p_trend_reports.py** - 1P trend analysis
9. **nhl_totals_strategy.py** - Over/Under strategy

**Output**: `reports/YYYY-MM-DD/` and `/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/YYYY-MM-DD/`

**Models Used** (in `nhl/strategies/`):
- `nhl_enhanced_models.pkl`
- `nhl_goalie_models.pkl`
- `nhl_player_models.pkl`
- `nhl_totals_models.pkl`

---

## GOLF/PGA SYSTEM

**Location**: `/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/`

**Purpose**: PGA Tour tournament predictions using DataGolf API

### Key Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `run_collection.py` | Data collection | `python run_collection.py [test|current|historical|all]` |
| `betting_simulation.py` | Tournament simulations | `python scripts/betting_simulation.py` |
| `course_profiles.py` | Course-specific analysis | `python scripts/course_profiles.py` |
| `backtest_model.py` | Model validation | `python scripts/backtest_model.py` |

### Quick Commands

```bash
cd /Users/dickgibbons/AI Projects/sports-betting/PGA_Bets

# Test API connection
python run_collection.py test

# Get current tournament data
python run_collection.py current

# Get historical data
python run_collection.py historical
```

### Data Available
- Player rankings and skill ratings
- Strokes Gained breakdowns (OTT, APP, ARG, PUTT)
- Pre-tournament win/top 5/top 10 probabilities
- Betting odds from 8+ sportsbooks
- Course history and fit analysis

---

## OTHER SPORTS (DISABLED BY DEFAULT)

### NBA
- Script: `./run_nba_daily.sh`
- Location: External repo at `/Users/dickgibbons/NBA-Machine-Learning-Sports-Betting`
- Status: Disabled (no historical spread data)

### NCAA Basketball
- Script: `./run_ncaa_daily.sh`
- Location: `ncaa/analyzers/ncaa_betting_angles_analyzer.py`
- Status: Disabled by default

To enable, edit `run_all_daily.sh` and uncomment the relevant lines.

---

## PERFORMANCE TRACKING

### View Performance
```bash
# Quick summary
python3 track_performance.py show

# Detailed by sport
python3 dashboards/performance/view_performance_by_sport.py
```

### Update Results
```bash
python3 track_performance.py update
```

### Database
- Main tracker: `betting_tracker.db` (SQLite)
- Performance CSVs: `performance_reports/`

---

## TROUBLESHOOTING

### Dashboard Won't Start
```bash
# Check if port is in use
lsof -i :8501  # Replace with port number

# Kill specific dashboard
pkill -f hockey_dashboard.py
pkill -f soccer_dashboard.py
pkill -f "streamlit.*8505"
pkill -f "streamlit.*8506"
```

### Daily Scripts Fail
```bash
# Check logs
tail -100 logs/all_sports_daily_*.log

# Run individual script manually
cd /Users/dickgibbons/AI Projects/sports-betting
python3 soccer/strategies/soccer_best_bets_daily.py
```

### Missing Data Files
Key data locations:
- NHL cache: `data/nhl_game_cache.db`
- Soccer stats: `soccer/strategies/data/team_stats_cache.db`
- Global Soccer dashboard stats: `dashboards/soccer/data/team_stats/team_stats_current.csv`
- Team stats CSVs: `/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/`

---

## DIRECTORY STRUCTURE

```
/Users/dickgibbons/AI Projects/sports-betting/
├── dashboards/
│   ├── hockey/hockey_dashboard.py      # Port 8501
│   ├── soccer/soccer_dashboard.py      # Port 8502
│   ├── soccer/global_schedule_dashboard.py  # Port 8506
│   ├── soccer/team_stats_collector.py  # Fetches team stats from FootyStats API
│   ├── nhl/nhl_1p_totals_ui.py        # Port 8505
│   └── performance/                    # CLI dashboards
├── nhl/strategies/                     # NHL daily scripts (9 scripts)
├── soccer/strategies/                  # Soccer daily scripts (4 scripts)
├── PGA_Bets/                          # Golf prediction system
├── core/                              # Post-processing scripts
├── reports/                           # Daily reports by date
├── logs/                              # Execution logs
├── run_soccer_daily.sh                # Soccer runner
├── run_nhl_daily.sh                   # NHL runner
├── run_all_daily.sh                   # All sports runner
└── CLAUDE_CODE_INSTRUCTIONS.md        # THIS FILE
```

---

## CRON AUTOMATION

Current setup runs all daily scripts at 5:00 AM:

```bash
# View current cron
crontab -l

# Expected entry
0 5 * * * cd /Users/dickgibbons/AI Projects/sports-betting && ./run_all_daily.sh
```

To modify:
```bash
crontab -e
```

---

## SUMMARY

When user says **"run sports betting"**:
1. Launch 4 web dashboards (ports 8501, 8502, 8505, 8506)
2. Run `./run_soccer_daily.sh`
3. Run `./run_nhl_daily.sh`
4. Verify all dashboards are accessible
5. Report URLs and status to user

The system covers **Hockey, Soccer, and Golf** with automated daily predictions, web dashboards, and performance tracking.
