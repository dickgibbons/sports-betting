#!/bin/bash

################################################################################
# Setup 5:00 AM Daily Automation
# Configures cron job to run all sports betting reports at 5:00 AM daily
################################################################################

PROJECT_DIR="/Users/dickgibbons/sports-betting"

echo "========================================="
echo "Sports Betting - 5:00 AM Automation Setup"
echo "========================================="
echo ""

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$PROJECT_DIR/run_all_daily.sh"
chmod +x "$PROJECT_DIR/run_nhl_daily.sh"
chmod +x "$PROJECT_DIR/run_nba_daily.sh"
chmod +x "$PROJECT_DIR/run_ncaa_daily.sh"
chmod +x "$PROJECT_DIR/run_soccer_daily.sh"
chmod +x "$PROJECT_DIR/core/generate_sport_picks.py"
chmod +x "$PROJECT_DIR/generate_performance_trackers.py"
echo "✓ Scripts are executable"
echo ""

# Check existing cron jobs
echo "Current sports betting cron jobs:"
crontab -l 2>/dev/null | grep -i "sports-betting\|dickgibbons/sports" || echo "  (none found)"
echo ""

# Ask user for confirmation
echo "This will set up a cron job to run at 5:00 AM daily that will:"
echo "  1. Generate NHL daily picks → nhl_picks_YYYY-MM-DD.txt"
echo "  2. Generate NBA daily picks → nba_picks_YYYY-MM-DD.txt"
echo "  3. Generate NCAA daily picks → ncaa_picks_YYYY-MM-DD.txt"
echo "  4. Generate Soccer daily picks → soccer_picks_YYYY-MM-DD.txt"
echo "  5. Generate unified cross-sport report"
echo "  6. Update cumulative performance trackers"
echo ""
echo "All files will be saved to: $PROJECT_DIR/reports/YYYY-MM-DD/"
echo ""

read -p "Continue with setup? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Setup cancelled."
    exit 0
fi

# Remove any existing sports betting cron jobs
echo ""
echo "Removing existing sports betting cron jobs..."
crontab -l 2>/dev/null | grep -v "sports-betting" | grep -v "dickgibbons/sports" | crontab - 2>/dev/null

# Add new cron job for 5:00 AM daily
echo "Adding new cron job for 5:00 AM daily..."
(crontab -l 2>/dev/null; echo "# Sports Betting - Daily Reports at 5:00 AM") | crontab -
(crontab -l 2>/dev/null; echo "0 5 * * * cd $PROJECT_DIR && ./run_all_daily.sh") | crontab -

echo "✓ Cron job installed!"
echo ""

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Your new cron schedule:"
crontab -l | grep -i "sports\|$PROJECT_DIR"
echo ""
echo "📅 Schedule: Every day at 5:00 AM"
echo ""
echo "📊 What will be generated:"
echo "  • NHL picks file (nhl_picks_YYYY-MM-DD.txt)"
echo "  • NBA picks file (nba_picks_YYYY-MM-DD.txt)"
echo "  • NCAA picks file (ncaa_picks_YYYY-MM-DD.txt)"
echo "  • Soccer picks file (soccer_picks_YYYY-MM-DD.txt)"
echo "  • NHL first period trends (CSV + TXT)"
echo "  • Unified cross-sport report"
echo "  • Updated performance trackers"
echo ""
echo "📁 Output location: $PROJECT_DIR/reports/YYYY-MM-DD/"
echo ""
echo "To manually run now:"
echo "  ./run_all_daily.sh"
echo ""
echo "To view/edit cron jobs:"
echo "  crontab -e"
echo ""
echo "To remove automation:"
echo "  crontab -l | grep -v 'sports-betting' | crontab -"
echo ""
