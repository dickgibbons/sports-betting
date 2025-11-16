#!/bin/bash
#
# Soccer Betting Daily Automation Setup
# This script sets up automated daily execution
#

echo "⚽ Setting up Soccer Betting Daily Automation"
echo "============================================="

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "📁 Script directory: $SCRIPT_DIR"

# Create the daily runner script
RUNNER_SCRIPT="$SCRIPT_DIR/run_daily_automation.sh"
cat > "$RUNNER_SCRIPT" << 'EOF'
#!/bin/bash
#
# Daily Soccer Betting Automation Runner
# This script runs the daily automation and handles logging
#

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Set up logging
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"
DATE=$(date +%Y%m%d)
LOG_FILE="$LOG_DIR/automation_$DATE.log"

echo "🚀 Starting daily automation at $(date)" >> "$LOG_FILE"
echo "📁 Working directory: $SCRIPT_DIR" >> "$LOG_FILE"

# Run the automation with timeout
timeout 30m python3 daily_automation.py >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Daily automation completed successfully at $(date)" >> "$LOG_FILE"
else
    echo "❌ Daily automation failed with exit code $EXIT_CODE at $(date)" >> "$LOG_FILE"
fi

# Keep only last 30 days of logs
find "$LOG_DIR" -name "automation_*.log" -type f -mtime +30 -delete

exit $EXIT_CODE
EOF

# Make runner script executable
chmod +x "$RUNNER_SCRIPT"
echo "✅ Created automation runner: $RUNNER_SCRIPT"

# Create email configuration
echo "📧 Setting up email configuration..."
python3 email_reports.py
echo "📝 Email config template created. Please edit email_config.json"

# Check current crontab
echo ""
echo "📅 Current crontab entries:"
crontab -l 2>/dev/null || echo "(No existing crontab)"

# Propose crontab entry
echo ""
echo "🕒 Recommended crontab entry (runs daily at 8:00 AM):"
echo "0 8 * * * $RUNNER_SCRIPT"
echo ""
echo "📋 To set up automated daily execution:"
echo "1. Run: crontab -e"
echo "2. Add this line: 0 8 * * * $RUNNER_SCRIPT"
echo "3. Save and exit"
echo ""
echo "⏰ Alternative times:"
echo "   Morning: 0 8 * * * (8:00 AM)"
echo "   Afternoon: 0 14 * * * (2:00 PM)"
echo "   Evening: 0 20 * * * (8:00 PM)"
echo ""

# Test automation setup
echo "🧪 Testing automation setup..."
if [ -f "$SCRIPT_DIR/daily_automation.py" ]; then
    echo "✅ Main automation script found"
else
    echo "❌ Main automation script missing"
fi

if [ -f "$SCRIPT_DIR/email_reports.py" ]; then
    echo "✅ Email script found"
else
    echo "❌ Email script missing"
fi

echo ""
echo "🎯 Setup Summary:"
echo "✅ Automation runner created: $RUNNER_SCRIPT"
echo "📧 Email config template created: email_config.json"
echo "📁 Log directory will be: $SCRIPT_DIR/logs"
echo ""
echo "📝 Next steps:"
echo "1. Edit email_config.json with your email settings"
echo "2. Set up crontab entry for daily execution"
echo "3. Test with: $RUNNER_SCRIPT"
echo ""
echo "🚀 Automation setup complete!"