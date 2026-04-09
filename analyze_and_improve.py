"""
Autonomous Performance Analysis & Model Improvement System
===========================================================
Analyzes betting results daily and proactively identifies improvement opportunities.
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

DB_PATH = "/Users/dickgibbons/AI Projects/sports-betting/betting_tracker.db"
EXPERIMENTS_FILE = "/Users/dickgibbons/AI Projects/sports-betting/experiments.json"
IMPROVEMENTS_LOG = "/Users/dickgibbons/AI Projects/sports-betting/improvements_log.txt"

def log_improvement(message):
    """Log improvement suggestions to file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(IMPROVEMENTS_LOG, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"💡 {message}")

def load_experiments():
    """Load experiment tracking"""
    if os.path.exists(EXPERIMENTS_FILE):
        with open(EXPERIMENTS_FILE, 'r') as f:
            return json.load(f)
    return {"experiments": [], "last_analysis": None}

def save_experiment(experiment):
    """Save new experiment"""
    data = load_experiments()
    data["experiments"].append(experiment)
    data["last_analysis"] = datetime.now().isoformat()
    with open(EXPERIMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def analyze_performance():
    """Comprehensive performance analysis"""
    print("\n" + "="*80)
    print("🔍 AUTONOMOUS PERFORMANCE ANALYSIS")
    print("="*80)

    conn = sqlite3.connect(DB_PATH)

    # Get all completed predictions
    df = pd.read_sql_query("""
        SELECT * FROM predictions
        WHERE status IN ('won', 'lost')
        ORDER BY date DESC
    """, conn)

    if len(df) == 0:
        print("\n⏳ No completed predictions yet. Need more data to analyze.")
        conn.close()
        return []

    print(f"\n📊 Analyzing {len(df)} completed predictions...")

    issues = []

    # ANALYSIS 1: Overall Win Rate by Sport
    print("\n" + "-"*80)
    print("1️⃣  WIN RATE ANALYSIS BY SPORT")
    print("-"*80)

    for sport in df['sport'].unique():
        sport_df = df[df['sport'] == sport]
        wins = (sport_df['status'] == 'won').sum()
        total = len(sport_df)
        win_rate = wins / total * 100
        profit = sport_df['profit'].sum()
        roi = profit / (total * 100) * 100

        print(f"\n{sport}:")
        print(f"  Win Rate: {win_rate:.1f}% ({wins}/{total})")
        print(f"  Profit: ${profit:+.2f}")
        print(f"  ROI: {roi:+.2f}%")

        # Flag issues
        if win_rate < 50:
            issue = f"{sport} win rate below 50% ({win_rate:.1f}%) - NEEDS IMPROVEMENT"
            issues.append(issue)
            log_improvement(issue)

        if roi < 0:
            issue = f"{sport} has negative ROI ({roi:.2f}%) - LOSING MONEY"
            issues.append(issue)
            log_improvement(issue)

        if win_rate < 52.4 and roi > 0:
            issue = f"{sport} win rate ({win_rate:.1f}%) barely profitable - need 52.4% to beat -110 odds consistently"
            issues.append(issue)
            log_improvement(issue)

    # ANALYSIS 2: Win Rate by Bet Type
    print("\n" + "-"*80)
    print("2️⃣  WIN RATE ANALYSIS BY BET TYPE")
    print("-"*80)

    for sport in df['sport'].unique():
        sport_df = df[df['sport'] == sport]
        print(f"\n{sport}:")

        for bet_type in sport_df['bet_type'].unique():
            type_df = sport_df[sport_df['bet_type'] == bet_type]
            wins = (type_df['status'] == 'won').sum()
            total = len(type_df)
            win_rate = wins / total * 100
            profit = type_df['profit'].sum()
            roi = profit / (total * 100) * 100

            print(f"  {bet_type}: {win_rate:.1f}% ({wins}/{total}), ROI: {roi:+.2f}%")

            if roi < -5 and total >= 5:
                issue = f"{sport} {bet_type} losing money ({roi:.2f}% ROI) - CONSIDER STOPPING THIS BET TYPE"
                issues.append(issue)
                log_improvement(issue)

    # ANALYSIS 3: Confidence Calibration
    print("\n" + "-"*80)
    print("3️⃣  CONFIDENCE CALIBRATION ANALYSIS")
    print("-"*80)

    # Group by confidence ranges
    df['conf_bucket'] = pd.cut(df['confidence'], bins=[0, 0.70, 0.80, 0.90, 1.0],
                                labels=['60-70%', '70-80%', '80-90%', '90-100%'])

    for bucket in df['conf_bucket'].unique():
        if pd.isna(bucket):
            continue
        bucket_df = df[df['conf_bucket'] == bucket]
        wins = (bucket_df['status'] == 'won').sum()
        total = len(bucket_df)
        actual_win_rate = wins / total * 100

        print(f"\n{bucket} confidence predictions:")
        print(f"  Actual Win Rate: {actual_win_rate:.1f}% ({wins}/{total})")

        # Check calibration
        if bucket == '90-100%' and actual_win_rate < 80:
            issue = f"High confidence (90%+) bets only winning {actual_win_rate:.1f}% - MODEL OVERCONFIDENT"
            issues.append(issue)
            log_improvement(issue)

    # ANALYSIS 4: Recent Performance Trend
    print("\n" + "-"*80)
    print("4️⃣  RECENT PERFORMANCE TREND (Last 7 Days)")
    print("-"*80)

    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    recent_df = df[df['date'] >= seven_days_ago]

    if len(recent_df) > 0:
        wins = (recent_df['status'] == 'won').sum()
        total = len(recent_df)
        win_rate = wins / total * 100
        profit = recent_df['profit'].sum()

        print(f"\nLast 7 days: {win_rate:.1f}% ({wins}/{total}), Profit: ${profit:+.2f}")

        # Compare to overall
        overall_win_rate = (df['status'] == 'won').sum() / len(df) * 100

        if win_rate < overall_win_rate - 10:
            issue = f"Recent performance declining ({win_rate:.1f}% vs {overall_win_rate:.1f}% overall) - CHECK FOR CHANGES"
            issues.append(issue)
            log_improvement(issue)

    # ANALYSIS 5: Odds Analysis
    print("\n" + "-"*80)
    print("5️⃣  ODDS RANGE ANALYSIS")
    print("-"*80)

    # Favorites vs Underdogs
    favorites = df[df['odds'] < 0]
    underdogs = df[df['odds'] > 0]

    if len(favorites) > 0:
        fav_wins = (favorites['status'] == 'won').sum()
        fav_rate = fav_wins / len(favorites) * 100
        fav_profit = favorites['profit'].sum()
        print(f"\nFavorites (negative odds): {fav_rate:.1f}% ({fav_wins}/{len(favorites)}), Profit: ${fav_profit:+.2f}")

        if fav_rate < 60 and len(favorites) >= 10:
            issue = f"Favorites only winning {fav_rate:.1f}% - may be overestimating favorites"
            issues.append(issue)
            log_improvement(issue)

    if len(underdogs) > 0:
        dog_wins = (underdogs['status'] == 'won').sum()
        dog_rate = dog_wins / len(underdogs) * 100
        dog_profit = underdogs['profit'].sum()
        print(f"Underdogs (positive odds): {dog_rate:.1f}% ({dog_wins}/{len(underdogs)}), Profit: ${dog_profit:+.2f}")

    conn.close()
    return issues

def suggest_improvements(issues):
    """Generate specific improvement suggestions based on issues"""
    print("\n" + "="*80)
    print("💡 PROACTIVE IMPROVEMENT SUGGESTIONS")
    print("="*80)

    if len(issues) == 0:
        print("\n✅ No major issues detected! Models are performing well.")
        return

    suggestions = []

    for issue in issues:
        if "NHL" in issue and "win rate below 50%" in issue:
            suggestions.append({
                "sport": "NHL",
                "problem": "Low win rate",
                "experiments": [
                    "Increase confidence threshold from 90% to 93%",
                    "Add recent form weighting (last 5 games)",
                    "Add rest days as a feature",
                    "Filter out back-to-back games",
                    "Add goalie matchup analysis"
                ]
            })

        elif "NBA" in issue and "negative ROI" in issue:
            suggestions.append({
                "sport": "NBA",
                "problem": "Negative ROI",
                "experiments": [
                    "Only bet when EV > 10 (currently using EV > 0)",
                    "Add injury impact scoring",
                    "Filter out second night of back-to-backs",
                    "Add pace of play features",
                    "Check if model needs retraining with current season data"
                ]
            })

        elif "NCAA" in issue:
            suggestions.append({
                "sport": "NCAA",
                "problem": "Underperforming",
                "experiments": [
                    "Only bet back-to-backs with 2+ days rest advantage",
                    "Add home court advantage weighting",
                    "Filter out neutral site games",
                    "Add strength of schedule adjustment",
                    "Track which specific angles work best"
                ]
            })

        elif "Soccer" in issue:
            suggestions.append({
                "sport": "Soccer",
                "problem": "Underperforming",
                "experiments": [
                    "Increase confidence threshold to 95%",
                    "Add form streak analysis (5+ game trends)",
                    "Filter by league (some leagues may be more predictable)",
                    "Add head-to-head history",
                    "Check data quality - may have wrong league labels"
                ]
            })

        elif "OVERCONFIDENT" in issue:
            suggestions.append({
                "sport": "All",
                "problem": "Model calibration",
                "experiments": [
                    "Apply confidence calibration (temperature scaling)",
                    "Retrain with Platt scaling",
                    "Increase minimum confidence thresholds by 5%",
                    "Add uncertainty quantification"
                ]
            })

        elif "declining" in issue:
            suggestions.append({
                "sport": "All",
                "problem": "Recent performance drop",
                "experiments": [
                    "Check if league dynamics changed (rule changes, etc)",
                    "Verify data freshness - may need retraining",
                    "Analyze which teams/situations are losing",
                    "Check if variance or actual model degradation"
                ]
            })

    # Print suggestions
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion['sport']} - {suggestion['problem']}")
        print("   Recommended experiments:")
        for exp in suggestion['experiments']:
            print(f"   • {exp}")

        # Save as experiment to try
        save_experiment({
            "date": datetime.now().isoformat(),
            "sport": suggestion['sport'],
            "problem": suggestion['problem'],
            "status": "suggested",
            "experiments": suggestion['experiments']
        })

    print("\n" + "="*80)
    print("📝 Experiments saved to:", EXPERIMENTS_FILE)
    print("💾 Analysis logged to:", IMPROVEMENTS_LOG)
    print("="*80)

def check_minimum_bets():
    """Check if we have enough data to analyze"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE status IN ('won', 'lost')")
    completed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE status = 'pending'")
    pending = cursor.fetchone()[0]

    conn.close()

    print(f"\n📈 Current Status:")
    print(f"   Completed predictions: {completed}")
    print(f"   Pending predictions: {pending}")

    if completed < 10:
        print(f"\n⏳ Need at least 10 completed predictions for meaningful analysis.")
        print(f"   Currently have {completed}. Come back after more games complete!")
        return False

    return True

def main():
    print("\n" + "="*80)
    print("🤖 AUTONOMOUS BETTING MODEL IMPROVEMENT SYSTEM")
    print("="*80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not os.path.exists(DB_PATH):
        print("\n❌ No tracking database found. Run predictions first!")
        return

    # Check if we have enough data
    if not check_minimum_bets():
        return

    # Run analysis
    issues = analyze_performance()

    # Generate improvement suggestions
    suggest_improvements(issues)

    print("\n✅ Analysis complete! Check improvements_log.txt for full history.")

if __name__ == "__main__":
    main()
