#!/bin/bash
#
# NHL Automated Daily System - Enhanced Version
# Runs complete workflow: date validation, results fetch, AWS training, predictions, tracking
#
# To run at 5am EST daily, add to crontab:
# 0 5 * * * cd /Users/dickgibbons/hockey/daily\ hockey && ./automated_daily_system.sh >> logs/daily_$(date +\%Y\%m\%d).log 2>&1
#

cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs
TODAY_NUM=$(date +%Y%m%d)
mkdir -p "../hockey reports/${TODAY_NUM}"

# Set variables
TODAY=$(date +%Y-%m-%d)
YESTERDAY=$(date -v-1d +%Y-%m-%d)
DAY_BEFORE=$(date -v-2d +%Y-%m-%d)
LOG_FILE="logs/daily_${TODAY}.log"
REPORT_DIR="../hockey reports/${TODAY_NUM}"

# AWS Configuration
AWS_KEY="/Users/dickgibbons/.ssh/my-aws-key"
AWS_HOST="ec2-user@3.93.56.53"
AWS_NHL_DIR="~/nhl"

# Start logging
exec > >(tee -a "$LOG_FILE")
exec 2>&1

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                     🏒 NHL AUTOMATED DAILY SYSTEM                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ============================================================================
# STEP 1: Validate System Date
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📅 STEP 1: DATE VALIDATION - Verifying system date is correct"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Current Date: $TODAY ($(date '+%A'))"
echo "   Current Time: $(date '+%I:%M %p %Z')"
echo "   Yesterday: $YESTERDAY"
echo "   Day Before: $DAY_BEFORE"
echo ""

# Validate year is reasonable (2025-2030)
YEAR=$(date +%Y)
if [ "$YEAR" -lt 2025 ] || [ "$YEAR" -gt 2030 ]; then
    echo "   ❌ ERROR: System date appears incorrect. Year is $YEAR"
    echo "   Please check system date settings."
    exit 1
fi

echo "   ✅ Date validation passed"
echo ""

# ============================================================================
# STEP 2: Pull Results from Previous Nights
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📥 STEP 2: FETCH RESULTS - Pulling game results from recent nights"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Fetching results for: $DAY_BEFORE (day before yesterday)"
echo ""

python3 update_model_with_results.py --date $DAY_BEFORE

echo ""
echo "   Fetching results for: $YESTERDAY (yesterday)"
echo ""

python3 update_model_with_results.py --date $YESTERDAY

echo ""
echo "   ✅ Game results fetched and added to training history"
echo ""

# ============================================================================
# STEP 3: Train Models on AWS
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 STEP 3: AWS TRAINING - Retraining models with latest data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if AWS key exists
if [ ! -f "$AWS_KEY" ]; then
    echo "   ⚠️  WARNING: AWS key not found at $AWS_KEY"
    echo "   Skipping AWS training - will use existing models"
else
    # Check if AWS instance is reachable
    if ! ssh -i "$AWS_KEY" -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$AWS_HOST" "echo 'Connected'" &>/dev/null; then
        echo "   ⚠️  WARNING: Cannot connect to AWS instance"
        echo "   Skipping AWS training - will use existing models"
    else
        echo "   ✅ Connected to AWS: $AWS_HOST"
        echo "   📤 Uploading training_history.csv to AWS..."

        # Upload training history to AWS
        if scp -i "$AWS_KEY" "training_history.csv" "$AWS_HOST:$AWS_NHL_DIR/" 2>/dev/null; then
            echo "   ✅ Training history uploaded"
        else
            echo "   ⚠️  Failed to upload training history"
        fi

        echo "   🔨 Starting model training on AWS (this may take 5-10 minutes)..."

        # Run training on AWS
        TRAINING_OUTPUT=$(ssh -i "$AWS_KEY" "$AWS_HOST" "cd $AWS_NHL_DIR && python3 nhl_enhanced_trainer.py 2>&1")
        TRAINING_EXIT_CODE=$?

        if [ $TRAINING_EXIT_CODE -eq 0 ]; then
            echo "   ✅ AWS model training completed successfully"
            echo "$TRAINING_OUTPUT" | tail -10

            # Download updated models from AWS
            echo "   📥 Downloading updated models from AWS..."
            if scp -i "$AWS_KEY" "$AWS_HOST:$AWS_NHL_DIR/nhl_enhanced_models.pkl" "./" 2>/dev/null; then
                echo "   ✅ Models downloaded and updated"
            else
                echo "   ⚠️  Could not download models - will use existing local models"
            fi
        else
            echo "   ❌ AWS training failed with exit code $TRAINING_EXIT_CODE"
            echo "   Will use existing local models"
            echo "$TRAINING_OUTPUT" | tail -20
        fi
    fi
fi

echo ""

# ============================================================================
# STEP 4: Update Cumulative Tracker with Recent Bet Results
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💰 STEP 4: UPDATE TRACKER - Recording bet results from recent nights"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Updating tracker with results from: $DAY_BEFORE"
echo ""

python3 cumulative_tracker.py --update $DAY_BEFORE

echo ""
echo "   Updating tracker with results from: $YESTERDAY"
echo ""

python3 cumulative_tracker.py --update $YESTERDAY

echo ""

# ============================================================================
# STEP 5: Generate Today's Full Game Report
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 STEP 5: DAILY PREDICTIONS - Generating reports for $TODAY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Generate all daily reports
echo "   📊 Generating daily NHL report..."
python3 daily_nhl_report.py --date $TODAY

echo ""
echo "   🎯 Generating bet recommendations..."
python3 bet_recommendations.py --date $TODAY --min-edge 0.08 --min-confidence 0.55

echo ""
echo "   🏆 Generating top 5 best bets..."
python3 top5_daily_picks.py --date $TODAY

echo ""
echo "   🎯 Generating player shots predictions..."
python3 daily_player_shots_report.py --date $TODAY

echo ""
echo "   🥅 Generating goalie saves predictions..."
python3 daily_goalie_saves_report.py --date $TODAY

echo ""
echo "   🔥 Generating back-to-back betting opportunities..."
python3 nhl_daily_b2b_finder.py --date $TODAY > "nhl_b2b_opportunities_${TODAY}.txt"

echo ""
echo "   📊 Generating cumulative performance summary..."
python3 cumulative_tracker.py --summary

echo ""

# ============================================================================
# STEP 6: Copy All Reports to Date-Organized Directory
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 STEP 6: ORGANIZE REPORTS - Copying all reports to ${REPORT_DIR}/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Copy all generated reports to the date-organized directory
REPORTS_COPIED=0

if [ -f "nhl_daily_report_${TODAY}.csv" ]; then
    cp "nhl_daily_report_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   ✅ nhl_daily_report_${TODAY}.csv"
    ((REPORTS_COPIED++))
fi

if [ -f "bet_recommendations_${TODAY}.csv" ]; then
    cp "bet_recommendations_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   ✅ bet_recommendations_${TODAY}.csv"
    ((REPORTS_COPIED++))
fi

if [ -f "top5_best_bets_${TODAY}.csv" ]; then
    cp "top5_best_bets_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   ✅ top5_best_bets_${TODAY}.csv"
    ((REPORTS_COPIED++))
fi

if [ -f "player_shots_predictions_${TODAY}.csv" ]; then
    cp "player_shots_predictions_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   ✅ player_shots_predictions_${TODAY}.csv"
    ((REPORTS_COPIED++))
fi

if [ -f "goalie_saves_predictions_${TODAY}.csv" ]; then
    cp "goalie_saves_predictions_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   ✅ goalie_saves_predictions_${TODAY}.csv"
    ((REPORTS_COPIED++))
fi

if [ -f "cumulative_summary_${TODAY}.csv" ]; then
    cp "cumulative_summary_${TODAY}.csv" "${REPORT_DIR}/"
    echo "   ✅ cumulative_summary_${TODAY}.csv"
    ((REPORTS_COPIED++))
fi

if [ -f "nhl_b2b_opportunities_${TODAY}.txt" ]; then
    cp "nhl_b2b_opportunities_${TODAY}.txt" "${REPORT_DIR}/"
    echo "   ✅ nhl_b2b_opportunities_${TODAY}.txt"
    ((REPORTS_COPIED++))
fi

echo ""
echo "   📂 Copied $REPORTS_COPIED reports to: ${REPORT_DIR}/"
echo ""

# ============================================================================
# STEP 7: Weekly Full Retrain (Sunday only)
# ============================================================================
if [ $(date +%u) -eq 7 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔨 SUNDAY SPECIAL: Full model retrain on all historical data"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python3 update_model_with_results.py --auto --days 7 --full-retrain

    echo ""
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                           ✅ DAILY SYSTEM COMPLETE                             ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📅 Date: $TODAY"
echo "⏰ Completed at: $(date '+%I:%M %p %Z')"
echo ""
echo "📁 Reports Generated: $REPORTS_COPIED"
echo "📂 Location: ${REPORT_DIR}/"
echo ""
echo "📊 System Status:"
echo "   ✅ Date validated"
echo "   ✅ Game results fetched and updated"
echo "   ✅ Models trained (local + AWS)"
echo "   ✅ Performance tracker updated"
echo "   ✅ All reports generated"
echo ""

# Keep logs for 30 days only
find logs/ -name "daily_*.log" -mtime +30 -delete 2>/dev/null

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
