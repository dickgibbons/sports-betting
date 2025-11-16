#!/usr/bin/env python3
"""Quick backtest progress checker"""
import os
import subprocess

LOG_FILE = "backtest_sept_week1_full.log"

def check_backtest():
    """Check backtest progress"""

    if not os.path.exists(LOG_FILE):
        print(f"❌ Backtest log not found: {LOG_FILE}")
        return

    print("=" * 60)
    print("⚽ BACKTEST PROGRESS MONITOR")
    print("=" * 60)
    print()

    # Check if process is running
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'backtest_historical_2024_relaxed.py --start-date 2024-09-01'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Status: RUNNING")
        else:
            print("⚠️  Status: COMPLETED or STOPPED")
    except Exception as e:
        print(f"⚠️  Status: Unknown ({e})")

    print()

    # Read last 200 lines
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()

    recent = lines[-200:] if len(lines) > 200 else lines
    recent_text = ''.join(recent)

    # Latest date
    print("📅 Latest Date Being Processed:")
    for line in reversed(recent):
        if "Backtesting 2024" in line:
            print(f"   {line.strip()}")
            break

    print()

    # Latest daily summary
    print("📊 Latest Daily Summary:")
    for line in reversed(recent):
        if "Daily Summary" in line:
            print(f"   {line.strip()}")
            break

    print()

    # Recent bets
    print("🎯 Recent Bets (last 15):")
    bet_lines = [l.strip() for l in recent if '✅' in l or '❌' in l]
    for line in bet_lines[-15:]:
        print(f"   {line}")

    print()
    print("=" * 60)
    print(f"📝 Log file: {LOG_FILE}")
    print(f"📊 Total lines in log: {len(lines)}")
    print("=" * 60)
    print()
    print(f"To see live updates: tail -f {LOG_FILE}")

if __name__ == "__main__":
    check_backtest()
