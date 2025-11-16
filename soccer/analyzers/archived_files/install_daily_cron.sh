#!/bin/bash
#
# Install Daily Soccer Automation Cron Job
# Schedules daily_soccer_automation.sh to run at 5:00 AM every day
#

echo "🔧 Installing Daily Soccer Automation Cron Job"
echo "================================================"

# Path to automation script
AUTOMATION_SCRIPT="/Users/dickgibbons/soccer-betting-python/soccer/daily_soccer_automation.sh"

# Verify script exists
if [ ! -f "$AUTOMATION_SCRIPT" ]; then
    echo "❌ Error: Automation script not found at $AUTOMATION_SCRIPT"
    exit 1
fi

# Make sure script is executable
chmod +x "$AUTOMATION_SCRIPT"
echo "✅ Automation script is executable"

# Create cron job entry
CRON_ENTRY="0 5 * * * $AUTOMATION_SCRIPT"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$AUTOMATION_SCRIPT"; then
    echo "⚠️  Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "$AUTOMATION_SCRIPT" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job installed successfully"
echo ""
echo "📅 Schedule: Every day at 5:00 AM"
echo "📝 Script: $AUTOMATION_SCRIPT"
echo ""
echo "Current crontab:"
echo "----------------"
crontab -l | grep "$AUTOMATION_SCRIPT"
echo ""
echo "✅ Installation complete!"
echo ""
echo "To verify the cron job is running, check logs in:"
echo "  /Users/dickgibbons/soccer-betting-python/soccer/logs/"
echo ""
echo "To remove this cron job, run:"
echo "  crontab -l | grep -v 'daily_soccer_automation.sh' | crontab -"
