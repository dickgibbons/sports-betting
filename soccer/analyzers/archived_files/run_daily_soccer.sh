#!/bin/bash

# Daily Soccer Betting Report Automation Script
# Runs every morning to generate today's betting recommendations

echo "🚀 Starting Daily Soccer Betting Report..."
echo "📅 Date: $(date)"
echo ""

# Change to soccer directory
cd "/Users/richardgibbons/soccer betting python/soccer"

# Run the daily betting report generator
echo "⚽ Running Daily Betting Report Generator..."
python3 daily_betting_report_generator.py

# Check if it completed successfully
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Daily soccer betting report completed successfully!"
    echo "📊 Check output reports/ folder for today's picks"
    
    # Show quick summary of today's picks
    DATE_STR=$(date +%Y%m%d)
    
    if [ -f "output reports/daily_picks_${DATE_STR}.csv" ]; then
        MAIN_PICKS=$(tail -n +2 "output reports/daily_picks_${DATE_STR}.csv" | wc -l)
        echo ""
        echo "📋 Main Strategy Picks: ${MAIN_PICKS} high-edge opportunities"
    fi
    
    if [ -f "output reports/high_confidence_picks_${DATE_STR}.csv" ]; then
        HIGH_CONF_PICKS=$(tail -n +2 "output reports/high_confidence_picks_${DATE_STR}.csv" | wc -l)
        echo "🎯 High Confidence Picks: ${HIGH_CONF_PICKS} safe bets (70%+ confidence)"
    fi
    
    echo ""
    echo "📊 REPORTS GENERATED:"
    echo "   • daily_picks_${DATE_STR}.csv - Main betting strategy"
    echo "   • high_confidence_picks_${DATE_STR}.csv - Conservative picks"
    echo "   • daily_report_${DATE_STR}.txt - Formatted report"
    
else
    echo ""
    echo "❌ Daily soccer report failed with exit code: $?"
    echo "Check the logs for details"
fi

echo ""
echo "🎯 Daily soccer automation complete - $(date)"