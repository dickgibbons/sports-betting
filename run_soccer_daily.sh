#!/bin/bash

################################################################################
# Soccer Daily Betting Report Generator
# Generates daily soccer predictions including BTTS, totals, and corners
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/dickgibbons/sports-betting"
REPORT_DIR="$PROJECT_DIR/reports"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_DIR/logs/soccer_daily_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$REPORT_DIR/$DATE"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "Soccer Daily Report Generation Starting"
log "========================================="

# Step 0: Generate PROFITABLE ANGLES DAILY REPORT (PRIMARY - based on 7,272 match analysis)
log "STEP 0: Generating profitable angles daily report..."
cd "$PROJECT_DIR/soccer/strategies"
if python3 soccer_daily_profitable_report.py >> "$LOG_FILE" 2>&1; then
    log "✓ Profitable angles report generated (All games in Bundesliga/EPL/MLS/Eredivisie with confidence %)"
else
    log "✗ Error generating profitable angles report"
fi

# Step 1: Generate main soccer best bets (legacy - for comparison)
log "STEP 1: Generating soccer best bets (BTTS, Totals)..."
if python3 soccer_best_bets_daily.py >> "$LOG_FILE" 2>&1; then
    log "✓ Soccer best bets generated successfully"
else
    log "✗ Error generating soccer best bets"
fi

# Step 2: Generate corners analysis
log "STEP 2: Generating corners over/under analysis..."
if python3 corners_analyzer.py >> "$LOG_FILE" 2>&1; then
    log "✓ Corners analysis completed"
else
    log "✗ Error generating corners analysis"
fi

# Step 3: Generate first half analysis
log "STEP 3: Generating first half predictions..."
if python3 first_half_analyzer.py >> "$LOG_FILE" 2>&1; then
    log "✓ First half analysis completed"
else
    log "✗ Error generating first half analysis"
fi

# Copy reports to date-organized directory
log "STEP 4: Organizing reports..."
cp soccer_report_*.txt "$REPORT_DIR/$DATE/" 2>/dev/null || true
cp reports/*/*.json "$REPORT_DIR/$DATE/" 2>/dev/null || true
log "✓ Reports organized in $REPORT_DIR/$DATE/"

# Copy to central Daily Reports folder
DAILY_REPORTS="/Users/dickgibbons/Daily Reports/$DATE"
mkdir -p "$DAILY_REPORTS"
DATE_SHORT=$(date +%Y%m%d)
cp "$PROJECT_DIR/soccer/strategies/reports"/*/soccer_* "$DAILY_REPORTS/" 2>/dev/null || true
log "✓ Reports copied to $DAILY_REPORTS/"

log "========================================="
log "Soccer Daily Report Generation Complete"
log "Log file: $LOG_FILE"
log "========================================="
