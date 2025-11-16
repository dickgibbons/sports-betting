#!/bin/bash
#
# Daily Soccer Automation Script
# Runs at 5:00 AM every day
# 1. Verifies system date
# 2. Retrains models on AWS with latest data
# 3. Generates daily soccer reports
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log file
LOG_DIR="/Users/dickgibbons/soccer-betting-python/soccer/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/daily_automation_$(date +%Y%m%d).log"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Start automation
log "=================================="
log "DAILY SOCCER AUTOMATION STARTED"
log "=================================="

# STEP 1: Verify system date
log_info "STEP 1: Verifying system date..."

CURRENT_DATE=$(date '+%Y-%m-%d')
CURRENT_TIME=$(date '+%H:%M:%S')
CURRENT_DAY=$(date '+%A')

log "Current Date: $CURRENT_DATE ($CURRENT_DAY)"
log "Current Time: $CURRENT_TIME"

# Check if date seems reasonable (between 2025-2030)
YEAR=$(date '+%Y')
if [ "$YEAR" -lt 2025 ] || [ "$YEAR" -gt 2030 ]; then
    log_error "System date appears incorrect. Year is $YEAR"
    log_error "Please check system date settings."
    exit 1
fi

log "✅ Date verification passed"

# STEP 2: Retrain models on AWS
log_info "STEP 2: Retraining models on AWS with latest data..."

AWS_KEY="/Users/dickgibbons/.ssh/my-aws-key"
AWS_HOST="ec2-user@54.90.205.84"
AWS_SOCCER_DIR="~/soccer"

log "Connecting to AWS instance: $AWS_HOST"

# Check if AWS key exists
if [ ! -f "$AWS_KEY" ]; then
    log_error "AWS key not found at $AWS_KEY"
    exit 1
fi

# Check if AWS instance is reachable
if ! ssh -i "$AWS_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$AWS_HOST" "echo 'Connected'" &>/dev/null; then
    log_error "Cannot connect to AWS instance"
    log_warning "Skipping model retraining - will use existing models"
else
    log "✅ Connected to AWS instance"

    # Run training script on AWS
    log "Starting model retraining (this may take 10-15 minutes)..."

    TRAINING_OUTPUT=$(ssh -i "$AWS_KEY" "$AWS_HOST" "cd $AWS_SOCCER_DIR && python3 aws_fetch_and_train.py 2>&1")
    TRAINING_EXIT_CODE=$?

    if [ $TRAINING_EXIT_CODE -eq 0 ]; then
        log "✅ Model retraining completed successfully"
        echo "$TRAINING_OUTPUT" >> "$LOG_FILE"

        # Download updated models
        log "Downloading updated models from AWS..."
        MODELS_DIR="/Users/dickgibbons/soccer-betting-python/soccer/daily soccer/models"

        # List of model files to download
        MODELS=(
            "improved_betting_predictor_model.pkl"
            "improved_daily_manager_model.pkl"
        )

        for MODEL in "${MODELS[@]}"; do
            if scp -i "$AWS_KEY" "$AWS_HOST:$AWS_SOCCER_DIR/$MODEL" "$MODELS_DIR/" 2>/dev/null; then
                log "✅ Downloaded: $MODEL"
            else
                log_warning "Could not download $MODEL (may not exist)"
            fi
        done

        log "✅ Model synchronization complete"
    else
        log_error "Model retraining failed with exit code $TRAINING_EXIT_CODE"
        log_warning "Continuing with existing models"
        echo "$TRAINING_OUTPUT" >> "$LOG_FILE"
    fi
fi

# STEP 3: Generate daily reports
log_info "STEP 3: Generating daily soccer reports..."

DAILY_SOCCER_DIR="/Users/dickgibbons/soccer-betting-python/soccer/daily soccer"

cd "$DAILY_SOCCER_DIR"

if python3 streamlined_daily_generator.py >> "$LOG_FILE" 2>&1; then
    log "✅ Daily reports generated successfully"

    # Check if reports were created
    REPORT_DIR="/Users/dickgibbons/soccer-betting-python/soccer/reports/$(date +%Y%m%d)"
    if [ -d "$REPORT_DIR" ]; then
        REPORT_COUNT=$(ls -1 "$REPORT_DIR" | wc -l)
        log "Created $REPORT_COUNT files in $REPORT_DIR"
    fi
else
    log_error "Failed to generate daily reports"
    exit 1
fi

# Summary
log "=================================="
log "DAILY AUTOMATION COMPLETED"
log "=================================="
log "Date: $CURRENT_DATE"
log "Reports Location: /Users/dickgibbons/soccer-betting-python/soccer/reports/$(date +%Y%m%d)"
log "Log File: $LOG_FILE"
log "=================================="

exit 0
