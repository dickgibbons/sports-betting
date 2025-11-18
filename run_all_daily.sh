#!/bin/bash

################################################################################
# Master Daily Report Generator - All Sports
# Runs daily reports for NHL, NBA, NCAA, and Soccer independently
################################################################################

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/dickgibbons/sports-betting"
REPORT_DIR="$PROJECT_DIR/reports"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_DIR/logs/all_sports_daily_$TIMESTAMP.log"

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$REPORT_DIR/$DATE"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "DAILY SPORTS BETTING REPORTS - ALL SPORTS"
log "Date: $DATE"
log "========================================="

# Parse command line arguments
RUN_NHL=true
RUN_NBA=true
RUN_NCAA=true
RUN_SOCCER=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --nhl-only)
            RUN_NBA=false
            RUN_NCAA=false
            RUN_SOCCER=false
            shift
            ;;
        --nba-only)
            RUN_NHL=false
            RUN_NCAA=false
            RUN_SOCCER=false
            shift
            ;;
        --ncaa-only)
            RUN_NHL=false
            RUN_NBA=false
            RUN_SOCCER=false
            shift
            ;;
        --soccer-only)
            RUN_NHL=false
            RUN_NBA=false
            RUN_NCAA=false
            shift
            ;;
        --no-nhl)
            RUN_NHL=false
            shift
            ;;
        --no-nba)
            RUN_NBA=false
            shift
            ;;
        --no-ncaa)
            RUN_NCAA=false
            shift
            ;;
        --no-soccer)
            RUN_SOCCER=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--nhl-only|--nba-only|--ncaa-only|--soccer-only] [--no-nhl] [--no-nba] [--no-ncaa] [--no-soccer]"
            exit 1
            ;;
    esac
done

# Run NHL reports
if [ "$RUN_NHL" = true ]; then
    log "========================================="
    log "Running NHL Daily Reports..."
    log "========================================="
    cd "$PROJECT_DIR"
    if ./run_nhl_daily.sh; then
        log "✓ NHL reports completed successfully"
    else
        log "✗ NHL reports failed (exit code: $?)"
    fi
fi

# Run NBA reports
if [ "$RUN_NBA" = true ]; then
    log "========================================="
    log "Running NBA Daily Reports..."
    log "========================================="
    cd "$PROJECT_DIR"
    if ./run_nba_daily.sh; then
        log "✓ NBA reports completed successfully"
    else
        log "✗ NBA reports failed (exit code: $?)"
    fi
fi

# Run NCAA reports
if [ "$RUN_NCAA" = true ]; then
    log "========================================="
    log "Running NCAA Daily Reports..."
    log "========================================="
    cd "$PROJECT_DIR"
    if ./run_ncaa_daily.sh; then
        log "✓ NCAA reports completed successfully"
    else
        log "✗ NCAA reports failed (exit code: $?)"
    fi
fi

# Run Soccer reports
if [ "$RUN_SOCCER" = true ]; then
    log "========================================="
    log "Running Soccer Daily Reports..."
    log "========================================="
    cd "$PROJECT_DIR"
    if ./run_soccer_daily.sh; then
        log "✓ Soccer reports completed successfully"
    else
        log "✗ Soccer reports failed (exit code: $?)"
    fi
fi

# Generate sport-specific picks files
log "========================================="
log "Generating Sport-Specific Picks Files..."
log "========================================="
cd "$PROJECT_DIR/core"
if python3 generate_sport_picks.py >> "$LOG_FILE" 2>&1; then
    log "✓ Sport-specific picks files generated"
else
    log "✗ Error generating sport-specific picks"
fi

# Generate unified cross-sport report
log "========================================="
log "Generating Unified Cross-Sport Report..."
log "========================================="
cd "$PROJECT_DIR/core"
if python3 daily_reports_runner.py >> "$LOG_FILE" 2>&1; then
    log "✓ Unified report generated successfully"
else
    log "✗ Error generating unified report"
fi

# Update cumulative performance trackers
log "========================================="
log "Updating Cumulative Performance Trackers..."
log "========================================="
cd "$PROJECT_DIR"
if python3 generate_performance_trackers.py >> "$LOG_FILE" 2>&1; then
    log "✓ Performance trackers updated"
else
    log "✗ Error updating performance trackers"
fi

# Summary
log "========================================="
log "DAILY REPORT GENERATION COMPLETE"
log "========================================="
log "Reports saved to: $REPORT_DIR/$DATE/"
log "Log file: $LOG_FILE"
log ""
log "📊 Sport-Specific Picks Files:"
log "  - nhl_picks_$DATE.txt"
log "  - nba_picks_$DATE.txt"
log "  - ncaa_picks_$DATE.txt"
log "  - soccer_picks_$DATE.txt"
log ""
log "📈 Performance Trackers Updated:"
log "  - performance_reports/*_cumulative_performance.csv"
log ""
log "To view all files:"
log "  ls -lh $REPORT_DIR/$DATE/"
log ""
