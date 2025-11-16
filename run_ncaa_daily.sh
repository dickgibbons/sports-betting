#!/bin/bash

################################################################################
# NCAA Daily Betting Report Generator
# Generates daily NCAA basketball predictions and betting angles
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/dickgibbons/sports-betting"
REPORT_DIR="$PROJECT_DIR/reports"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_DIR/logs/ncaa_daily_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$REPORT_DIR/$DATE"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "NCAA Daily Report Generation Starting"
log "========================================="

# Step 1: Generate NCAA betting angles analysis
log "STEP 1: Analyzing NCAA betting angles..."
cd "$PROJECT_DIR/ncaa/analyzers"
if python3 ncaa_betting_angles_analyzer.py >> "$LOG_FILE" 2>&1; then
    log "✓ NCAA betting angles analyzed"
else
    log "✗ Error analyzing NCAA betting angles"
fi

# Copy reports to date-organized directory
log "STEP 2: Organizing reports..."
cp ncaa_report_*.txt "$REPORT_DIR/$DATE/" 2>/dev/null || true
log "✓ Reports organized in $REPORT_DIR/$DATE/"

log "========================================="
log "NCAA Daily Report Generation Complete"
log "Log file: $LOG_FILE"
log "========================================="
