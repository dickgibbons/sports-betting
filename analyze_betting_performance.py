#!/usr/bin/env python3
"""
Betting Performance Analyzer

This script analyzes betting results to identify:
1. Calibration issues (predicted vs actual win rates)
2. Best performing confidence thresholds
3. Profitable/unprofitable bet types
4. Recommendations for improving picks

Run this as part of the daily routine AFTER results are updated.
"""

import csv
from datetime import datetime
from collections import defaultdict
from pathlib import Path

TRACKER_FILE = "/Users/dickgibbons/sports-betting/UNIFIED_BETTING_TRACKER.csv"
ANALYSIS_OUTPUT = "/Users/dickgibbons/sports-betting/BETTING_ANALYSIS_REPORT.txt"


def load_results():
    """Load only settled bets from the tracker"""
    bets = []
    with open(TRACKER_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Result'] in ['WIN', 'LOSS']:
                # Parse confidence
                conf_str = row['Confidence'].replace('%', '')
                try:
                    confidence = float(conf_str)
                except:
                    confidence = 50.0

                # Parse odds
                try:
                    odds = int(row['Odds'])
                except:
                    odds = -150

                # Parse profit
                try:
                    profit = float(row['Profit'])
                except:
                    profit = 0.0

                bets.append({
                    'date': row['Date'],
                    'sport': row['Sport'],
                    'league': row['League'],
                    'matchup': row['Matchup'],
                    'bet': row['Bet'],
                    'bet_type': row['Bet_Type'],
                    'confidence': confidence,
                    'odds': odds,
                    'result': row['Result'],
                    'won': row['Result'] == 'WIN',
                    'profit': profit
                })
    return bets


def analyze_calibration(bets):
    """
    Check if our confidence predictions are well-calibrated.
    If we predict 65% confidence, are we winning ~65% of the time?
    """
    # Group bets by confidence buckets
    buckets = defaultdict(list)

    for bet in bets:
        conf = bet['confidence']
        if conf < 55:
            bucket = '50-55%'
        elif conf < 60:
            bucket = '55-60%'
        elif conf < 65:
            bucket = '60-65%'
        elif conf < 70:
            bucket = '65-70%'
        elif conf < 75:
            bucket = '70-75%'
        elif conf < 80:
            bucket = '75-80%'
        else:
            bucket = '80%+'

        buckets[bucket].append(bet)

    results = {}
    for bucket, bucket_bets in sorted(buckets.items()):
        wins = sum(1 for b in bucket_bets if b['won'])
        total = len(bucket_bets)
        actual_pct = wins / total * 100 if total > 0 else 0
        avg_conf = sum(b['confidence'] for b in bucket_bets) / total if total > 0 else 0
        profit = sum(b['profit'] for b in bucket_bets)

        results[bucket] = {
            'count': total,
            'wins': wins,
            'losses': total - wins,
            'actual_pct': actual_pct,
            'expected_pct': avg_conf,
            'calibration_error': actual_pct - avg_conf,
            'profit': profit
        }

    return results


def analyze_by_bet_type(bets):
    """Analyze performance by bet type"""
    by_type = defaultdict(list)

    for bet in bets:
        by_type[bet['bet_type']].append(bet)

    results = {}
    for bet_type, type_bets in by_type.items():
        wins = sum(1 for b in type_bets if b['won'])
        total = len(type_bets)
        profit = sum(b['profit'] for b in type_bets)
        avg_conf = sum(b['confidence'] for b in type_bets) / total if total > 0 else 0

        # Calculate expected vs actual
        actual_pct = wins / total * 100 if total > 0 else 0

        results[bet_type] = {
            'count': total,
            'wins': wins,
            'win_pct': actual_pct,
            'avg_confidence': avg_conf,
            'profit': profit,
            'roi': (profit / total * 100) if total > 0 else 0
        }

    return results


def analyze_by_sport(bets):
    """Analyze performance by sport"""
    by_sport = defaultdict(list)

    for bet in bets:
        by_sport[bet['sport']].append(bet)

    results = {}
    for sport, sport_bets in by_sport.items():
        wins = sum(1 for b in sport_bets if b['won'])
        total = len(sport_bets)
        profit = sum(b['profit'] for b in sport_bets)

        results[sport] = {
            'count': total,
            'wins': wins,
            'win_pct': wins / total * 100 if total > 0 else 0,
            'profit': profit,
            'roi': (profit / total * 100) if total > 0 else 0
        }

    return results


def find_optimal_thresholds(bets):
    """Find the optimal confidence threshold for filtering bets"""
    thresholds = [55, 58, 60, 62, 65, 68, 70, 75]

    results = {}
    for thresh in thresholds:
        filtered = [b for b in bets if b['confidence'] >= thresh]
        if not filtered:
            continue

        wins = sum(1 for b in filtered if b['won'])
        total = len(filtered)
        profit = sum(b['profit'] for b in filtered)

        results[thresh] = {
            'count': total,
            'wins': wins,
            'win_pct': wins / total * 100 if total > 0 else 0,
            'profit': profit,
            'roi': (profit / total * 100) if total > 0 else 0
        }

    return results


def generate_recommendations(bets, calibration, by_type, by_sport, thresholds):
    """Generate actionable recommendations"""
    recommendations = []

    # 1. Check overall calibration
    total_bets = len(bets)
    total_wins = sum(1 for b in bets if b['won'])
    overall_pct = total_wins / total_bets * 100 if total_bets > 0 else 0
    overall_profit = sum(b['profit'] for b in bets)

    if overall_profit > 0:
        recommendations.append(f"POSITIVE: Overall profitable with {overall_profit:+.2f} units on {total_bets} bets")
    else:
        recommendations.append(f"NEGATIVE: Overall unprofitable with {overall_profit:+.2f} units - review selection criteria")

    # 2. Check calibration issues
    for bucket, stats in calibration.items():
        if stats['count'] >= 5:  # Need minimum sample
            error = stats['calibration_error']
            if error < -10:
                recommendations.append(f"OVERCONFIDENT: {bucket} bets win {stats['actual_pct']:.1f}% but predicted {stats['expected_pct']:.1f}%")
            elif error > 10:
                recommendations.append(f"UNDERCONFIDENT: {bucket} bets win {stats['actual_pct']:.1f}% but predicted {stats['expected_pct']:.1f}%")

    # 3. Identify best/worst bet types
    profitable_types = [(t, s) for t, s in by_type.items() if s['profit'] > 0 and s['count'] >= 3]
    unprofitable_types = [(t, s) for t, s in by_type.items() if s['profit'] < -1 and s['count'] >= 3]

    if profitable_types:
        best = max(profitable_types, key=lambda x: x[1]['profit'])
        recommendations.append(f"BEST BET TYPE: {best[0]} with {best[1]['profit']:+.2f}u profit ({best[1]['win_pct']:.1f}% win rate)")

    if unprofitable_types:
        worst = min(unprofitable_types, key=lambda x: x[1]['profit'])
        recommendations.append(f"WORST BET TYPE: {worst[0]} with {worst[1]['profit']:+.2f}u loss - consider reducing or eliminating")

    # 4. Find optimal threshold
    if thresholds:
        best_thresh = max(thresholds.items(), key=lambda x: x[1]['roi'] if x[1]['count'] >= 5 else -999)
        if best_thresh[1]['count'] >= 5:
            recommendations.append(f"OPTIMAL THRESHOLD: {best_thresh[0]}% confidence gives {best_thresh[1]['roi']:.1f}% ROI ({best_thresh[1]['profit']:+.2f}u on {best_thresh[1]['count']} bets)")

    # 5. Check if high confidence is working
    high_conf = [b for b in bets if b['confidence'] >= 70]
    if high_conf:
        hc_wins = sum(1 for b in high_conf if b['won'])
        hc_profit = sum(b['profit'] for b in high_conf)
        if hc_profit < 0:
            recommendations.append(f"WARNING: High confidence (70%+) bets are LOSING money ({hc_profit:+.2f}u) - model may be overconfident")

    return recommendations


def generate_report():
    """Generate the full analysis report"""
    bets = load_results()

    if len(bets) < 5:
        print("Not enough settled bets for analysis (need at least 5)")
        return

    calibration = analyze_calibration(bets)
    by_type = analyze_by_bet_type(bets)
    by_sport = analyze_by_sport(bets)
    thresholds = find_optimal_thresholds(bets)
    recommendations = generate_recommendations(bets, calibration, by_type, by_sport, thresholds)

    report = []
    report.append("=" * 70)
    report.append("BETTING PERFORMANCE ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"Total Settled Bets: {len(bets)}")
    report.append("=" * 70)

    # Overall Summary
    total_wins = sum(1 for b in bets if b['won'])
    total_profit = sum(b['profit'] for b in bets)
    report.append(f"\nOVERALL: {total_wins}-{len(bets)-total_wins} ({total_wins/len(bets)*100:.1f}%), {total_profit:+.2f} units")

    # By Sport
    report.append("\n" + "-" * 50)
    report.append("BY SPORT")
    report.append("-" * 50)
    for sport, stats in sorted(by_sport.items(), key=lambda x: -x[1]['profit']):
        report.append(f"{sport:12s}: {stats['wins']}-{stats['count']-stats['wins']} ({stats['win_pct']:.1f}%), {stats['profit']:+.2f}u, ROI: {stats['roi']:+.1f}%")

    # By Bet Type
    report.append("\n" + "-" * 50)
    report.append("BY BET TYPE")
    report.append("-" * 50)
    for bt, stats in sorted(by_type.items(), key=lambda x: -x[1]['profit']):
        report.append(f"{bt[:25]:25s}: {stats['wins']}-{stats['count']-stats['wins']} ({stats['win_pct']:.1f}%), {stats['profit']:+.2f}u")

    # Calibration Analysis
    report.append("\n" + "-" * 50)
    report.append("CALIBRATION (Predicted vs Actual)")
    report.append("-" * 50)
    for bucket, stats in sorted(calibration.items()):
        if stats['count'] > 0:
            cal = "GOOD" if abs(stats['calibration_error']) < 5 else ("OVER" if stats['calibration_error'] < 0 else "UNDER")
            report.append(f"{bucket:10s}: {stats['actual_pct']:.1f}% actual vs {stats['expected_pct']:.1f}% predicted ({cal}), n={stats['count']}")

    # Threshold Analysis
    report.append("\n" + "-" * 50)
    report.append("CONFIDENCE THRESHOLD ANALYSIS")
    report.append("-" * 50)
    for thresh, stats in sorted(thresholds.items()):
        report.append(f">={thresh}%: {stats['count']:3d} bets, {stats['win_pct']:.1f}% win, {stats['profit']:+.2f}u, ROI: {stats['roi']:+.1f}%")

    # Recommendations
    report.append("\n" + "=" * 70)
    report.append("RECOMMENDATIONS")
    report.append("=" * 70)
    for rec in recommendations:
        report.append(f"  - {rec}")

    report.append("\n" + "=" * 70)

    # Print and save report
    report_text = "\n".join(report)
    print(report_text)

    with open(ANALYSIS_OUTPUT, 'w') as f:
        f.write(report_text)

    print(f"\nReport saved to: {ANALYSIS_OUTPUT}")


if __name__ == "__main__":
    generate_report()
