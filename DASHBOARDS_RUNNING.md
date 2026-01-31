# 🚀 Dashboards Currently Running

All dashboards have been started and are available at the following URLs:

## 📊 Web Dashboards (Active)

### 1. **Hockey Dashboard** 🏒
- **Status**: ✅ Running
- **URL**: http://localhost:8503
- **Type**: Flask Web Application
- **Features**: Daily hockey schedule (NHL + international leagues) with team statistics
- **PID**: Check with `ps aux | grep hockey_dashboard`

### 2. **Soccer Dashboard** ⚽
- **Status**: ✅ Running  
- **URL**: http://localhost:8504
- **Type**: Flask Web Application
- **Features**: Daily soccer schedule with team statistics and form
- **PID**: Check with `ps aux | grep soccer_dashboard`

### 3. **NHL 1P Totals UI** 🏒
- **Status**: ✅ Running
- **URL**: http://localhost:8505
- **Type**: Streamlit Web Application
- **Features**: NHL 1st Period totals analysis with moving averages and trend visualizations
- **PID**: Check with `ps aux | grep streamlit`

## 📈 Command-Line Dashboards

### 4. **Performance Dashboard** 📊
- **Status**: ✅ Available
- **Run**: `python3 dashboards/performance/view_performance_by_sport.py`
- **Type**: Command-line output
- **Features**: Cumulative performance breakdown by sport and bet type

### Performance Summary (Latest Run):
- **NHL**: 50 bets, 70.0% win rate, -30.0% ROI
- **NBA**: 58 bets, 46.4% win rate, +11.0% ROI
- **NCAA**: 12 bets, 100.0% win rate, +350.0% ROI  
- **Soccer**: 25 bets, 25.0% win rate, -75.0% ROI

## 🔧 Management Commands

### Check Running Dashboards:
```bash
ps aux | grep -E "(soccer_dashboard|hockey_dashboard|streamlit.*nhl)" | grep -v grep
```

### View Logs:
```bash
# Soccer Dashboard
tail -f logs/soccer_dashboard.log

# Hockey Dashboard  
tail -f logs/hockey_dashboard.log

# NHL Dashboard
tail -f logs/nhl_dashboard.log
```

### Stop Dashboards:
```bash
# Find and kill processes
pkill -f soccer_dashboard.py
pkill -f hockey_dashboard.py
pkill -f streamlit.*nhl_1p_totals_ui.py
```

### Restart Dashboards:
```bash
cd /Users/dickgibbons/sports-betting

# Soccer Dashboard
python3 dashboards/soccer/soccer_dashboard.py > logs/soccer_dashboard.log 2>&1 &

# Hockey Dashboard
python3 dashboards/hockey/hockey_dashboard.py > logs/hockey_dashboard.log 2>&1 &

# NHL Dashboard
streamlit run dashboards/nhl/nhl_1p_totals_ui.py --server.port 8505 --server.headless true > logs/nhl_dashboard.log 2>&1 &
```

## 📝 Notes

- All web dashboards are running in the background
- Logs are being written to `logs/` directory
- Ports: Hockey (8503), Soccer (8504), NHL (8505)
- Access dashboards by opening the URLs in your web browser
- The performance dashboard can be run anytime with the command shown above

## 🔗 Quick Access Links

- [Hockey Dashboard](http://localhost:8503)
- [Soccer Dashboard](http://localhost:8504)  
- [NHL 1P Totals UI](http://localhost:8505)

---

*Last updated: January 15, 2026*
