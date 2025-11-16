#!/bin/bash
################################################################################
# AWS Soccer Backtest Runner
#
# Run this script on AWS EC2 to backtest the enhanced soccer betting system
# from August 1, 2025 to present.
#
# Usage:
#   chmod +x aws_run_backtest.sh
#   ./aws_run_backtest.sh
################################################################################

set -e  # Exit on error

# Configuration
START_DATE="2025-08-01"
END_DATE="2025-10-16"  # Use date with completed matches (not today)
LOG_FILE="backtest_$(date +%Y%m%d_%H%M%S).log"
S3_BUCKET="s3://your-bucket-name/soccer-backtests"  # Update with your bucket

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "⚽ AWS SOCCER BACKTEST RUNNER"
echo "=================================="
echo ""
echo "Start Date: $START_DATE"
echo "End Date: $END_DATE"
echo "Log File: $LOG_FILE"
echo ""

# Check if running on EC2 (optional)
if command -v ec2-metadata &> /dev/null; then
    INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
    INSTANCE_TYPE=$(ec2-metadata --instance-type | cut -d " " -f 2)
    echo -e "${GREEN}Running on EC2 Instance:${NC} $INSTANCE_ID ($INSTANCE_TYPE)"
else
    echo -e "${YELLOW}Not running on EC2 (or ec2-metadata not installed)${NC}"
fi

# Install dependencies
echo ""
echo "=================================="
echo "📦 Installing Dependencies"
echo "=================================="

# Check Python version
python3 --version

# Install required packages
pip3 install --user -q requests pandas numpy scikit-learn joblib matplotlib || {
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
}

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Verify model file exists
echo ""
echo "=================================="
echo "🔍 Checking Model Files"
echo "=================================="

MODEL_FILE="models/soccer_ml_models_enhanced.pkl"

if [ -f "$MODEL_FILE" ]; then
    MODEL_SIZE=$(du -h "$MODEL_FILE" | cut -f1)
    echo -e "${GREEN}✅ Enhanced model found:${NC} $MODEL_FILE ($MODEL_SIZE)"
else
    echo -e "${RED}❌ Enhanced model not found: $MODEL_FILE${NC}"
    echo ""
    echo "Please ensure the enhanced model is trained first:"
    echo "  python3 soccer_trainer_enhanced.py"
    exit 1
fi

# Create backup of current results (if any)
echo ""
echo "=================================="
echo "💾 Backing Up Previous Results"
echo "=================================="

if [ -f "backtest_results_detailed.csv" ]; then
    BACKUP_FILE="backtest_results_detailed_backup_$(date +%Y%m%d_%H%M%S).csv"
    cp backtest_results_detailed.csv "$BACKUP_FILE"
    echo -e "${GREEN}✅ Previous results backed up to:${NC} $BACKUP_FILE"
else
    echo "No previous results to backup"
fi

# Run the backtest
echo ""
echo "=================================="
echo "🚀 Running Backtest"
echo "=================================="
echo "This may take 10-30 minutes depending on the date range..."
echo ""

START_TIME=$(date +%s)

python3 aws_backtest_soccer.py \
    --start-date "$START_DATE" \
    --end-date "$END_DATE" \
    2>&1 | tee "$LOG_FILE"

BACKTEST_STATUS=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
DURATION_MIN=$((DURATION / 60))

echo ""
echo "=================================="
if [ $BACKTEST_STATUS -eq 0 ]; then
    echo -e "${GREEN}✅ Backtest Completed Successfully${NC}"
else
    echo -e "${RED}❌ Backtest Failed${NC}"
fi
echo "=================================="
echo "Duration: ${DURATION_MIN} minutes ($DURATION seconds)"

# Display results summary
if [ -f "backtest_results_daily.csv" ]; then
    echo ""
    echo "=================================="
    echo "📊 Quick Results Summary"
    echo "=================================="

    # Use Python to quickly summarize the results
    python3 << 'EOF'
import pandas as pd

try:
    df = pd.read_csv('backtest_results_daily.csv')

    total_bets = df['bets'].sum()
    total_wins = df['wins'].sum()
    total_losses = df['losses'].sum()

    if total_bets > 0:
        win_rate = (total_wins / total_bets) * 100
    else:
        win_rate = 0

    initial_bankroll = df['bankroll'].iloc[0] - df['profit'].iloc[0]
    final_bankroll = df['bankroll'].iloc[-1]
    total_profit = final_bankroll - initial_bankroll
    roi = (total_profit / initial_bankroll) * 100 if initial_bankroll > 0 else 0

    print(f"Total Bets: {int(total_bets)}")
    print(f"Wins: {int(total_wins)} | Losses: {int(total_losses)}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Total Profit: ${total_profit:.2f}")
    print(f"ROI: {roi:.1f}%")
    print(f"Final Bankroll: ${final_bankroll:.2f}")
    print(f"Growth: {((final_bankroll / initial_bankroll - 1) * 100):.1f}%")

except Exception as e:
    print(f"Could not generate summary: {e}")
EOF

fi

# List generated files
echo ""
echo "=================================="
echo "📁 Generated Files"
echo "=================================="

for file in backtest_results_*.csv backtest_bankroll_chart.png "$LOG_FILE"; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        echo "  ✅ $file ($SIZE)"
    fi
done

# Optional: Upload to S3
echo ""
echo "=================================="
echo "☁️  S3 Upload"
echo "=================================="

if command -v aws &> /dev/null; then
    read -p "Upload results to S3? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Updating S3_BUCKET in script first if needed..."
        echo "Current bucket: $S3_BUCKET"

        # Create dated folder in S3
        S3_DATE_PATH="$S3_BUCKET/$(date +%Y%m%d)"

        echo "Uploading to: $S3_DATE_PATH"

        aws s3 cp backtest_results_detailed.csv "$S3_DATE_PATH/" 2>/dev/null && \
            echo -e "${GREEN}✅ Uploaded detailed results${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to upload detailed results${NC}"

        aws s3 cp backtest_results_daily.csv "$S3_DATE_PATH/" 2>/dev/null && \
            echo -e "${GREEN}✅ Uploaded daily summary${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to upload daily summary${NC}"

        aws s3 cp backtest_bankroll_chart.png "$S3_DATE_PATH/" 2>/dev/null && \
            echo -e "${GREEN}✅ Uploaded chart${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to upload chart${NC}"

        aws s3 cp "$LOG_FILE" "$S3_DATE_PATH/" 2>/dev/null && \
            echo -e "${GREEN}✅ Uploaded log${NC}" || \
            echo -e "${YELLOW}⚠️  Failed to upload log${NC}"
    else
        echo "Skipping S3 upload"
    fi
else
    echo -e "${YELLOW}⚠️  AWS CLI not available - skipping S3 upload${NC}"
fi

# Final message
echo ""
echo "=================================="
echo "🎉 Backtest Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Review backtest_results_detailed.csv for all bets"
echo "  2. Review backtest_results_daily.csv for daily performance"
echo "  3. View backtest_bankroll_chart.png for visual growth"
echo "  4. Check $LOG_FILE for full execution log"
echo ""

exit $BACKTEST_STATUS
