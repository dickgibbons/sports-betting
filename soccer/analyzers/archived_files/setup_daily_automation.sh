#!/bin/bash

# Setup Daily Soccer Betting Automation
# This script sets up the daily automation using crontab

echo "🚀 Setting up Daily Soccer Betting Automation..."
echo ""

# Backup existing crontab
echo "📋 Backing up existing crontab..."
crontab -l > crontab_backup_$(date +%Y%m%d).txt 2>/dev/null || echo "No existing crontab found"

# Create the cron job entry
# Run at 8:00 AM every day
CRON_JOB="0 8 * * * /Users/richardgibbons/soccer\ betting\ python/soccer/run_daily_soccer.sh >> /Users/richardgibbons/soccer\ betting\ python/soccer/daily_automation.log 2>&1"

echo "🕐 Adding cron job to run daily at 8:00 AM..."
echo "Job: $CRON_JOB"

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# Verify the cron job was added
echo ""
echo "✅ Cron job added successfully!"
echo ""
echo "📋 Current crontab entries:"
crontab -l

echo ""
echo "🎯 AUTOMATION SETUP COMPLETE!"
echo ""
echo "📅 Your daily soccer report will now run automatically at 8:00 AM every day"
echo "📊 Results will be saved to: output reports/"
echo "📝 Logs will be saved to: daily_automation.log"
echo ""
echo "🔧 To manually run the report anytime:"
echo "   ./run_daily_soccer.sh"
echo ""
echo "🔧 To disable automation:"
echo "   crontab -e (then delete the soccer line)"
echo ""
echo "🔧 To view automation logs:"
echo "   tail -f daily_automation.log"