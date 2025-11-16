#!/bin/bash
#
# Soccer Automated Daily System
# Runs complete workflow: learning, predictions, recommendations, tracking
# Matches NHL automated_daily_system.sh structure
#
# To run at 5am EST daily, add to crontab:
# 0 5 * * * cd /Users/dickgibbons/soccer-betting-python/soccer && ./automated_daily_system_soccer.sh >> logs/daily_$(date +\%Y\%m\%d).log 2>&1
#

cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs
mkdir -p reports/$(date +%Y-%m)

# Set variables
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d)
LOG_FILE="logs/daily_${TODAY//-/}.log"
REPORT_DIR="reports/$(date +%Y-%m)"

# Start logging
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                     ⚽ SOCCER AUTOMATED DAILY SYSTEM                           ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📅 Date: $TODAY"
echo "⏰ Time: $(date '+%I:%M %p %Z')"
echo "📁 Working Directory: $(pwd)"
echo ""

# ============================================================================
# STEP 1: Update Models with Yesterday's Results
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 STEP 1: CONTINUOUS LEARNING - Updating models with $YESTERDAY results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 update_models_with_results.py --date $YESTERDAY

echo ""

# ============================================================================
# STEP 2: Update Cumulative Tracker with Yesterday's Bet Results
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💰 STEP 2: TRACKING PERFORMANCE - Updating with $YESTERDAY bet results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 cumulative_tracker_soccer.py --update $YESTERDAY

echo ""

# ============================================================================
# STEP 3: Generate Today's Full Match Report
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 STEP 3: DAILY PREDICTIONS - Generating full match report for $TODAY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 daily_soccer_report.py --date $TODAY

# Copy to reports directory
if [ -f "soccer_daily_report_${TODAY}.csv" ]; then
    cp "soccer_daily_report_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   📁 Copied to: ${REPORT_DIR}/soccer_daily_report_${TODAY}.csv"
fi

echo ""

# ============================================================================
# STEP 4: Generate Bet Recommendations
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 STEP 4: BET RECOMMENDATIONS - Filtering high-value bets for $TODAY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 bet_recommendations_soccer.py --date $TODAY --min-edge 0.03 --min-confidence 0.48

# Copy to reports directory
if [ -f "bet_recommendations_soccer_${TODAY}.csv" ]; then
    cp "bet_recommendations_soccer_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   📁 Copied to: ${REPORT_DIR}/bet_recommendations_soccer_${TODAY}.csv"
fi

echo ""

# ============================================================================
# STEP 5: Generate Cumulative Performance Summary
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 STEP 5: PERFORMANCE SUMMARY - Overall results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python3 cumulative_tracker_soccer.py --summary

# Copy to reports directory
if [ -f "cumulative_summary_soccer_${TODAY}.csv" ]; then
    cp "cumulative_summary_soccer_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   📁 Copied to: ${REPORT_DIR}/cumulative_summary_soccer_${TODAY}.csv"
fi

echo ""

# ============================================================================
# STEP 6: Weekly Full Retrain (Sunday only)
# ============================================================================
if [ $(date +%u) -eq 7 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔨 SUNDAY SPECIAL: Full model retrain on all historical data"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python3 update_models_with_results.py --auto --days 7 --full-retrain

    echo ""
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                           ✅ DAILY SYSTEM COMPLETE                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Files Generated:"
echo "   • soccer_daily_report_${TODAY}.csv         - Full match predictions"
echo "   • bet_recommendations_soccer_${TODAY}.csv  - Recommended bets only"
echo "   • cumulative_summary_soccer_${TODAY}.csv   - Performance tracker"
echo ""
echo "📂 Location: ${REPORT_DIR}/"
echo ""
echo "⏰ Completed at: $(date '+%I:%M %p %Z')"
echo ""

# ============================================================================
# Optional: Email Reports (uncomment if email configured)
# ============================================================================
# if [ -f "bet_recommendations_soccer_${TODAY}.csv" ]; then
#     cat bet_recommendations_soccer_${TODAY}.csv | mail -s "Soccer Bet Recommendations - $TODAY" your@email.com
# fi

# Keep logs for 30 days only
find logs/ -name "daily_*.log" -mtime +30 -delete

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
