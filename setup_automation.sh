#!/bin/bash

################################################################################
# Automation Setup Script
# Sets up cron jobs for daily betting report generation
################################################################################

PROJECT_DIR="/Users/dickgibbons/sports-betting"

echo "========================================="
echo "Sports Betting Daily Automation Setup"
echo "========================================="
echo ""

# Make all scripts executable
echo "Making scripts executable..."
chmod +x "$PROJECT_DIR/run_nhl_daily.sh"
chmod +x "$PROJECT_DIR/run_nba_daily.sh"
chmod +x "$PROJECT_DIR/run_ncaa_daily.sh"
chmod +x "$PROJECT_DIR/run_soccer_daily.sh"
chmod +x "$PROJECT_DIR/run_all_daily.sh"
echo "✓ Scripts are now executable"
echo ""

# Show current crontab
echo "Current cron jobs:"
crontab -l 2>/dev/null || echo "  (none)"
echo ""

# Ask user for automation preference
echo "How would you like to set up automation?"
echo "1) Run ALL sports daily at 5:00 AM"
echo "2) Run each sport at different times"
echo "3) Run only specific sports"
echo "4) Manual setup (show commands only)"
echo "5) Skip automation setup"
echo ""
read -p "Select option (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Setting up cron job to run all sports at 5:00 AM daily..."
        (crontab -l 2>/dev/null; echo "# Sports Betting - All Sports Daily at 5:00 AM") | crontab -
        (crontab -l 2>/dev/null; echo "0 5 * * * cd $PROJECT_DIR && ./run_all_daily.sh") | crontab -
        echo "✓ Cron job installed!"
        ;;
    2)
        echo ""
        echo "Setting up staggered cron jobs..."
        (crontab -l 2>/dev/null; echo "# Sports Betting - Staggered Schedule") | crontab -
        (crontab -l 2>/dev/null; echo "0 5 * * * cd $PROJECT_DIR && ./run_nhl_daily.sh  # NHL at 5:00 AM") | crontab -
        (crontab -l 2>/dev/null; echo "0 6 * * * cd $PROJECT_DIR && ./run_nba_daily.sh  # NBA at 6:00 AM") | crontab -
        (crontab -l 2>/dev/null; echo "0 7 * * * cd $PROJECT_DIR && ./run_ncaa_daily.sh  # NCAA at 7:00 AM") | crontab -
        (crontab -l 2>/dev/null; echo "0 8 * * * cd $PROJECT_DIR && ./run_soccer_daily.sh  # Soccer at 8:00 AM") | crontab -
        echo "✓ Staggered cron jobs installed!"
        ;;
    3)
        echo ""
        echo "Which sports would you like to automate? (y/n for each)"
        read -p "NHL? (y/n): " nhl_choice
        read -p "NBA? (y/n): " nba_choice
        read -p "NCAA? (y/n): " ncaa_choice
        read -p "Soccer? (y/n): " soccer_choice

        (crontab -l 2>/dev/null; echo "# Sports Betting - Custom Selection") | crontab -

        [[ "$nhl_choice" == "y" ]] && (crontab -l 2>/dev/null; echo "0 5 * * * cd $PROJECT_DIR && ./run_nhl_daily.sh") | crontab -
        [[ "$nba_choice" == "y" ]] && (crontab -l 2>/dev/null; echo "0 6 * * * cd $PROJECT_DIR && ./run_nba_daily.sh") | crontab -
        [[ "$ncaa_choice" == "y" ]] && (crontab -l 2>/dev/null; echo "0 7 * * * cd $PROJECT_DIR && ./run_ncaa_daily.sh") | crontab -
        [[ "$soccer_choice" == "y" ]] && (crontab -l 2>/dev/null; echo "0 8 * * * cd $PROJECT_DIR && ./run_soccer_daily.sh") | crontab -

        echo "✓ Custom cron jobs installed!"
        ;;
    4)
        echo ""
        echo "Manual Setup - Add these lines to your crontab (crontab -e):"
        echo ""
        echo "# All sports at 5:00 AM daily:"
        echo "0 5 * * * cd $PROJECT_DIR && ./run_all_daily.sh"
        echo ""
        echo "# Or individual sports at different times:"
        echo "0 5 * * * cd $PROJECT_DIR && ./run_nhl_daily.sh"
        echo "0 6 * * * cd $PROJECT_DIR && ./run_nba_daily.sh"
        echo "0 7 * * * cd $PROJECT_DIR && ./run_ncaa_daily.sh"
        echo "0 8 * * * cd $PROJECT_DIR && ./run_soccer_daily.sh"
        echo ""
        exit 0
        ;;
    5)
        echo "Skipping automation setup."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Your new cron jobs:"
crontab -l | grep -i "sports\|$PROJECT_DIR"
echo ""
echo "To manually run reports:"
echo "  All sports:    ./run_all_daily.sh"
echo "  NHL only:      ./run_nhl_daily.sh"
echo "  NBA only:      ./run_nba_daily.sh"
echo "  NCAA only:     ./run_ncaa_daily.sh"
echo "  Soccer only:   ./run_soccer_daily.sh"
echo ""
echo "Logs will be saved to: $PROJECT_DIR/logs/"
echo "Reports will be saved to: $PROJECT_DIR/reports/YYYY-MM-DD/"
echo ""
