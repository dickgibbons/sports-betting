# Dashboard Access Guide

## 🔗 Quick Access URLs

All dashboards are running. Try these URLs in your browser:

### ✅ Hockey Dashboard (Port 8503)
- **Primary**: http://127.0.0.1:8503
- **Alternative**: http://localhost:8503

### ✅ Soccer Dashboard (Port 8504)  
- **Primary**: http://127.0.0.1:8504
- **Alternative**: http://localhost:8504

### ✅ NHL Dashboard (Port 8505)
- **Primary**: http://127.0.0.1:8505
- **Alternative**: http://localhost:8505

## ⚠️ Troubleshooting "ERR_CONNECTION_REFUSED"

If you see "ERR_CONNECTION_REFUSED", try these steps:

### 1. **Use 127.0.0.1 instead of localhost**
   - Sometimes browsers have issues with `localhost`
   - Always try `http://127.0.0.1:XXXX` first

### 2. **Hard Refresh Your Browser**
   - **Mac**: Cmd + Shift + R
   - **Windows/Linux**: Ctrl + Shift + R
   - This clears cached connection errors

### 3. **Check if Dashboards are Running**
   ```bash
   # Check if ports are listening
   lsof -i :8503 -i :8504 -i :8505
   
   # Test HTTP response
   curl http://127.0.0.1:8503
   curl http://127.0.0.1:8504
   curl http://127.0.0.1:8505
   ```

### 4. **Restart a Specific Dashboard**
   ```bash
   cd /Users/dickgibbons/sports-betting
   
   # Restart Hockey
   pkill -f hockey_dashboard.py
   nohup python3 dashboards/hockey/hockey_dashboard.py > logs/hockey_dashboard.log 2>&1 &
   
   # Restart Soccer
   pkill -f soccer_dashboard.py
   nohup python3 dashboards/soccer/soccer_dashboard.py > logs/soccer_dashboard.log 2>&1 &
   
   # Restart NHL
   pkill -f streamlit.*nhl
   nohup streamlit run dashboards/nhl/nhl_1p_totals_ui.py --server.port 8505 --server.headless true > logs/nhl_dashboard.log 2>&1 &
   ```

### 5. **Check Firewall Settings**
   - macOS: System Preferences → Security & Privacy → Firewall
   - Make sure Python/Flask/Streamlit aren't blocked

### 6. **Try a Different Browser**
   - Chrome, Firefox, Safari, Edge
   - Sometimes browser extensions block localhost connections

### 7. **Clear Browser Cache**
   - Clear cookies and cached data for localhost/127.0.0.1
   - Or use Incognito/Private mode

## 📋 Verify Dashboard Status

Run this command to check all dashboards:

```bash
cd /Users/dickgibbons/sports-betting
echo "Checking dashboards..."
lsof -i :8503 -i :8504 -i :8505 | grep LISTEN
curl -s -o /dev/null -w "Hockey (8503): %{http_code}\n" http://127.0.0.1:8503
curl -s -o /dev/null -w "Soccer (8504): %{http_code}\n" http://127.0.0.1:8504
curl -s -o /dev/null -w "NHL (8505): %{http_code}\n" http://127.0.0.1:8505
```

Expected output:
- All ports should show `LISTEN`
- All HTTP codes should be `200`

## 🚀 Restart All Dashboards

If you need to restart everything:

```bash
cd /Users/dickgibbons/sports-betting

# Kill all dashboards
pkill -f "hockey_dashboard|soccer_dashboard|streamlit.*nhl"

# Wait a moment
sleep 2

# Restart all
nohup python3 dashboards/hockey/hockey_dashboard.py > logs/hockey_dashboard.log 2>&1 &
nohup python3 dashboards/soccer/soccer_dashboard.py > logs/soccer_dashboard.log 2>&1 &
nohup streamlit run dashboards/nhl/nhl_1p_totals_ui.py --server.port 8505 --server.headless true > logs/nhl_dashboard.log 2>&1 &

# Wait for them to start
sleep 5

# Verify
curl -s -o /dev/null -w "Hockey: %{http_code}\n" http://127.0.0.1:8503
curl -s -o /dev/null -w "Soccer: %{http_code}\n" http://127.0.0.1:8504
curl -s -o /dev/null -w "NHL: %{http_code}\n" http://127.0.0.1:8505
```

---

**Note**: Dashboards are running in the background using `nohup`. They will continue running even after you close the terminal. To stop them, use `pkill -f "dashboard_name"`.
