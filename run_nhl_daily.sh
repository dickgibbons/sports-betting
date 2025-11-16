#!/bin/bash

################################################################################
# NHL Daily Betting Report Generator
# Generates daily NHL predictions, player props, and first period analysis
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/dickgibbons/sports-betting"
REPORT_DIR="$PROJECT_DIR/reports"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_DIR/logs/nhl_daily_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$REPORT_DIR/$DATE"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "NHL Daily Report Generation Starting"
log "========================================="

# Step 1: Generate main NHL daily report
log "STEP 1: Generating NHL daily report..."
cd "$PROJECT_DIR/nhl/analyzers"
if python3 daily_nhl_report.py >> "$LOG_FILE" 2>&1; then
    log "✓ NHL daily report generated successfully"
else
    log "✗ Error generating NHL daily report"
fi

# Step 2: Generate NHL first period analysis
log "STEP 2: Generating NHL first period analysis..."
if python3 nhl_first_period_daily_report.py >> "$LOG_FILE" 2>&1; then
    log "✓ NHL first period analysis completed"
else
    log "✗ Error generating first period analysis"
fi

# Step 3: Generate goalie saves predictions
log "STEP 3: Generating goalie saves predictions..."
if python3 daily_goalie_saves_report.py >> "$LOG_FILE" 2>&1; then
    log "✓ Goalie saves predictions generated"
else
    log "✗ Error generating goalie saves predictions"
fi

# Step 4: Generate player shots predictions
log "STEP 4: Generating player shots predictions..."
if python3 daily_player_shots_report.py >> "$LOG_FILE" 2>&1; then
    log "✓ Player shots predictions generated"
else
    log "✗ Error generating player shots predictions"
fi

# Step 5: Check for back-to-back opportunities
log "STEP 5: Checking for back-to-back scheduling opportunities..."
if python3 nhl_daily_b2b_finder.py >> "$LOG_FILE" 2>&1; then
    log "✓ Back-to-back analysis completed"
else
    log "✗ Error analyzing back-to-back opportunities"
fi

# Step 6: Generate top 5 picks
log "STEP 6: Generating top 5 NHL picks..."
if python3 top5_daily_picks.py >> "$LOG_FILE" 2>&1; then
    log "✓ Top 5 picks generated"
else
    log "✗ Error generating top 5 picks"
fi

# Copy reports to date-organized directory
log "STEP 7: Organizing reports..."
cp nhl_daily_report_*.csv "$REPORT_DIR/$DATE/" 2>/dev/null || true
cp nhl_first_period_*.txt "$REPORT_DIR/$DATE/" 2>/dev/null || true
cp nhl_first_period_*.csv "$REPORT_DIR/$DATE/" 2>/dev/null || true
log "✓ Reports organized in $REPORT_DIR/$DATE/"

log "========================================="
log "NHL Daily Report Generation Complete"
log "Log file: $LOG_FILE"
log "========================================="
