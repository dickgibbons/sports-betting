#!/bin/bash
################################################################################
# Quick Backtest Test - 5 days only
#
# Test the backtest system on a short date range before running full backtest
################################################################################

set -e

echo "🧪 Testing backtest system on October 14-18, 2025 (5 days)"
echo ""

python3 aws_backtest_soccer.py \
    --start-date 2025-10-14 \
    --end-date 2025-10-18

echo ""
echo "✅ Short backtest test complete!"
echo ""
echo "If this worked, run the full backtest with:"
echo "  ./aws_run_backtest.sh"
echo ""
