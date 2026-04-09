#!/bin/bash
# Daily stats collection for soccer dashboard
# Runs team_stats_collector.py with merge mode to accumulate teams

cd /Users/dickgibbons/AI Projects/sports-betting/dashboards/soccer

# Log file with date
LOG_FILE="data/team_stats/collection_$(date +%Y%m%d).log"

echo "=== Stats Collection Started: $(date) ===" >> "$LOG_FILE"

# Run the collector with merge mode
python3 team_stats_collector.py --merge >> "$LOG_FILE" 2>&1

echo "=== Stats Collection Completed: $(date) ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
