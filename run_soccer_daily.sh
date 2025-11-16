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

# Step 1: Generate main soccer best bets
log "STEP 1: Generating soccer best bets (BTTS, Totals)..."
cd "$PROJECT_DIR/soccer/analyzers/daily soccer"
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
cp reports/$DATE*.json "$REPORT_DIR/$DATE/" 2>/dev/null || true
log "✓ Reports organized in $REPORT_DIR/$DATE/"

log "========================================="
log "Soccer Daily Report Generation Complete"
log "Log file: $LOG_FILE"
log "========================================="
