#!/bin/bash
#
# Install NHL Betting System Cron Job
# Automatically sets up daily 5am EST execution
#

echo "🏒 NHL Betting System - Cron Job Installer"
echo "=========================================="
echo ""

HOCKEY_DIR="/Users/dickgibbons/soccer-betting-python/hockey"
CRON_TIME="0 5 * * *"  # 5:00 AM daily

echo "This will install a cron job to run the automated system at 5:00 AM EST daily"
echo ""
echo "Job details:"
echo "  Time: 5:00 AM EST (Every Day)"
echo "  Location: $HOCKEY_DIR"
echo "  Script: automated_daily_system.sh"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled"
    exit 1
fi

# Backup existing crontab
echo "📋 Backing up existing crontab..."
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null
echo "   ✅ Backup saved"

# Check if job already exists
if crontab -l 2>/dev/null | grep -q "automated_daily_system.sh"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    crontab -l | grep "automated_daily_system.sh"
    echo ""
    read -p "Replace existing job? (y/n) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 1
    fi

    # Remove old job
    crontab -l | grep -v "automated_daily_system.sh" | crontab -
    echo "   ✅ Removed old job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_TIME cd $HOCKEY_DIR && ./automated_daily_system.sh >> logs/daily_\$(date +\\%Y\\%m\\%d).log 2>&1") | crontab -

echo ""
echo "✅ Cron job installed successfully!"
echo ""
echo "📋 Current crontab:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
crontab -l
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Installation Complete!"
echo ""
echo "The automated system will now run daily at 5:00 AM EST"
echo ""
echo "Next steps:"
echo "  1. Test the system now: ./automated_daily_system.sh"
echo "  2. Wait until 5:00 AM tomorrow for automatic run"
echo "  3. Check logs in: $HOCKEY_DIR/logs/"
echo "  4. Reports will be in: $HOCKEY_DIR/reports/"
echo ""
echo "To uninstall: crontab -e (then delete the line)"
echo ""
