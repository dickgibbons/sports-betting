#!/bin/bash

################################################################################
# NBA Daily Betting Report Generator
# Generates daily NBA predictions with ML models and betting angles
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/dickgibbons/sports-betting"
REPORT_DIR="$PROJECT_DIR/reports"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_DIR/logs/nba_daily_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$REPORT_DIR/$DATE"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "NBA Daily Report Generation Starting"
log "========================================="

# Step 1: Generate main NBA daily report
log "STEP 1: Generating NBA daily report with ML predictions..."
cd "$PROJECT_DIR/nba/analyzers"
if python3 nba_daily_report.py >> "$LOG_FILE" 2>&1; then
    log "✓ NBA daily report generated successfully"
else
    log "✗ Error generating NBA daily report"
fi

# Step 2: Generate betting angles analysis
log "STEP 2: Analyzing NBA betting angles..."
if python3 nba_betting_angles_analyzer_v2.py >> "$LOG_FILE" 2>&1; then
    log "✓ NBA betting angles analyzed"
else
    log "✗ Error analyzing betting angles"
fi

# Copy reports to date-organized directory
log "STEP 3: Organizing reports..."
cp nba_daily_report_*.csv "$REPORT_DIR/$DATE/" 2>/dev/null || true
cp nba_report_*.txt "$REPORT_DIR/$DATE/" 2>/dev/null || true
log "✓ Reports organized in $REPORT_DIR/$DATE/"

log "========================================="
log "NBA Daily Report Generation Complete"
log "Log file: $LOG_FILE"
log "========================================="
