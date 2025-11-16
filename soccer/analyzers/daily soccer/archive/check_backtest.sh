#!/bin/bash
# Quick backtest progress checker

LOG_FILE="backtest_sept_week1_full.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Backtest log not found: $LOG_FILE"
    exit 1
fi

echo "=================================================="
echo "⚽ BACKTEST PROGRESS MONITOR"
echo "=================================================="
echo ""

# Check if process is running
if pgrep -f "backtest_historical_2024_relaxed.py --start-date 2024-09-01" > /dev/null; then
    echo "✅ Status: RUNNING"
else
    echo "⚠️  Status: COMPLETED or STOPPED"
fi

echo ""
echo "📅 Latest Date Being Processed:"
tail -100 "$LOG_FILE" | grep "Backtesting 2024" | tail -1

echo ""
echo "📊 Latest Daily Summary:"
tail -100 "$LOG_FILE" | grep "Daily Summary" | tail -1

echo ""
echo "💰 Current Bankroll:"
tail -100 "$LOG_FILE" | grep "Bankroll:" | tail -1 | awk -F'Bankroll: ' '{print $2}'

echo ""
echo "🎯 Recent Bets (last 10):"
tail -50 "$LOG_FILE" | grep -E "✅|❌" | tail -10

echo ""
echo "=================================================="
echo "📝 Log file: $LOG_FILE"
echo "📊 Lines in log: $(wc -l < $LOG_FILE)"
echo "=================================================="
echo ""
echo "To see full log: tail -f $LOG_FILE"
