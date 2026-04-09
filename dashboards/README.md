# Dashboards Directory

This directory contains all dashboard/web UI applications organized by sport and purpose.

## 📊 Dashboard Structure

```
dashboards/
├── nhl/                      # NHL (Hockey) Dashboards
│   ├── nhl_1p_totals_ui.py   # Streamlit UI for NHL 1st Period Totals Analysis
│   └── templates/            # HTML templates (if any)
│
├── soccer/                   # Soccer Dashboards
│   ├── soccer_dashboard.py   # Flask-based Soccer Dashboard
│   ├── collect_soccer_daily_games.py  # Data collection for dashboard
│   ├── collect_soccer_team_stats.py   # Team stats collection
│   └── templates/
│       └── index.html        # Soccer dashboard HTML template
│
├── hockey/                   # Hockey Dashboards (General/International)
│   ├── hockey_dashboard.py   # Flask-based Hockey Dashboard
│   ├── collect_hockey_daily_games.py  # Data collection for dashboard
│   ├── collect_hockey_team_stats.py   # Team stats collection
│   └── templates/
│       └── index.html        # Hockey dashboard HTML template
│
└── performance/              # Performance Tracking Dashboards
    ├── show_performance.py   # Quick Performance Dashboard
    └── view_performance_by_sport.py  # View Performance by Sport
```

## 🎯 Dashboard Details

### 1. **NHL 1P Totals UI** (`nhl/nhl_1p_totals_ui.py`)
- **Type**: Streamlit web application
- **Purpose**: Shows daily NHL schedule with 1st Period totals analysis
- **Features**:
  - Team scoring trends vs opponent's allowed trends
  - Moving average visualizations
  - Color-coded analysis matching Excel format
- **Run**: `streamlit run dashboards/nhl/nhl_1p_totals_ui.py`

### 2. **Soccer Dashboard** (`soccer/soccer_dashboard.py`)
- **Type**: Flask web application
- **Purpose**: Daily soccer schedule with team statistics
- **Features**:
  - Daily fixture display
  - Team statistics and form
  - League standings
- **Run**: `python3 dashboards/soccer/soccer_dashboard.py`
- **Template**: `soccer/templates/index.html`

### 3. **Hockey Dashboard** (`hockey/hockey_dashboard.py`)
- **Type**: Flask web application
- **Purpose**: Daily hockey schedule (NHL + international leagues)
- **Features**:
  - Multi-league support (NHL, SHL, DEL, etc.)
  - Team statistics
  - Daily schedule view
- **Run**: `python3 dashboards/hockey/hockey_dashboard.py`
- **Template**: `hockey/templates/index.html`

### 4. **Performance Dashboards** (`performance/`)
- **Type**: Command-line dashboards
- **Purpose**: Track betting performance across sports
- **Scripts**:
  - `show_performance.py` - Quick performance overview
  - `view_performance_by_sport.py` - Detailed breakdown by sport
- **Run**: `python3 dashboards/performance/show_performance.py`

## 🚀 Usage

### Running Streamlit Dashboard (NHL)
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
streamlit run dashboards/nhl/nhl_1p_totals_ui.py
```

### Running Flask Dashboards (Soccer/Hockey)
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
# Soccer
python3 dashboards/soccer/soccer_dashboard.py

# Hockey
python3 dashboards/hockey/hockey_dashboard.py
```

### Running Performance Dashboard
```bash
cd /Users/dickgibbons/AI Projects/sports-betting
python3 dashboards/performance/show_performance.py
```

## 📝 Notes

- **Flask dashboards** typically run on `http://localhost:5000` (check each script for the port)
- **Streamlit dashboards** automatically open in your browser
- All dashboards use the same API keys from the main project
- Data collection scripts (`collect_*_daily_games.py`, `collect_*_team_stats.py`) are used to populate dashboard data

## 🔗 Related Files

- Main betting strategies are in `{sport}/strategies/`
- Data files are in `{sport}/data/`
- Performance tracking data in `betting_tracker.db` and `performance_reports/`
