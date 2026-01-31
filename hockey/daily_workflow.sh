#!/bin/bash
#
# NHL Daily Workflow - Automated Learning & Prediction
# This script should be run daily (via cron or manually)
#

cd "$(dirname "$0")"

echo "🏒 NHL DAILY WORKFLOW"
echo "===================================================================================="
date
echo ""

# Step 1: Update models with yesterday's results
echo "📊 STEP 1: Updating models with yesterday's results..."
echo "------------------------------------------------------------------------------------"
python3 update_model_with_results.py
echo ""

# Step 2: Generate today's predictions
TODAY=$(date +%Y-%m-%d)
echo "🔮 STEP 2: Generating predictions for $TODAY..."
echo "------------------------------------------------------------------------------------"
python3 daily_nhl_report.py --date $TODAY
echo ""

# Step 3: Check if predictions were generated
REPORT_FILE="nhl_daily_report_${TODAY}.csv"
if [ -f "$REPORT_FILE" ]; then
    echo "✅ Report generated: $REPORT_FILE"
    echo ""
    echo "📋 Preview:"
    head -5 "$REPORT_FILE"
else
    echo "⚠️  No games scheduled for today"
fi

echo ""
echo "===================================================================================="
echo "✅ Daily workflow complete!"
echo "===================================================================================="
