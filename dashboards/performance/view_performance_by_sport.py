#!/usr/bin/env python3
"""
View Performance Trackers - Quick Dashboard
Shows cumulative performance breakdown by sport and bet type
"""

import csv
from collections import defaultdict
import os


def analyze_csv(filepath, sport_name):
    """Analyze a performance tracker CSV"""

    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print(f"⚠️  No data in {sport_name} tracker")
        return

    # Stats
    total_bets = len(rows)
    wins = sum(1 for r in rows if r['Result'] == 'WIN')
    losses = sum(1 for r in rows if r['Result'] == 'LOSS')
    pushes = sum(1 for r in rows if r['Result'] == 'PUSH')
    pending = sum(1 for r in rows if r['Result'] == 'PENDING')

    # Calculate final running total
    final_total = 0.0
    for row in rows:
        profit = row['$25 Profit/Loss']
        if profit != 'PENDING':
            final_total = float(row['Running Total'].replace('$', '').replace(',', ''))

    # By bet type
    by_type = defaultdict(lambda: {'wins': 0, 'losses': 0, 'bets': 0, 'profit': 0.0})

    for row in rows:
        bet_type = row['Bet Type']
        by_type[bet_type]['bets'] += 1

        if row['Result'] == 'WIN':
            by_type[bet_type]['wins'] += 1
        elif row['Result'] == 'LOSS':
            by_type[bet_type]['losses'] += 1

        # Get final running total for this bet type
        if row['Type Running Total'] != 'PENDING':
            by_type[bet_type]['profit'] = float(row['Type Running Total'].replace('$', '').replace(',', ''))

    # Print summary
    emoji = '🏒' if sport_name == 'NHL' else '🏀' if sport_name in ['NBA', 'NCAA'] else '⚽'

    print(f"\n{emoji} {sport_name.upper()}")
    print("=" * 80)
    print(f"Total Bets: {total_bets}")

    if wins + losses > 0:
        win_rate = wins / (wins + losses) * 100
        print(f"Record: {wins}-{losses}-{pushes} ({win_rate:.1f}% win rate)")
        print(f"Running Total (@ $25/bet): ${final_total:+.2f}")

        if pending > 0:
            print(f"Pending: {pending} bets")

        # Show ROI
        if wins + losses > 0:
            total_risked = (wins + losses) * 25
            roi = (final_total / total_risked) * 100
            print(f"ROI: {roi:+.1f}%")

        # Breakdown by bet type
        if len(by_type) > 1:
            print(f"\nBreakdown by Bet Type:")
            for bet_type, stats in sorted(by_type.items()):
                if stats['wins'] + stats['losses'] > 0:
                    type_win_rate = stats['wins'] / (stats['wins'] + stats['losses']) * 100
                    print(f"  {bet_type}: {stats['wins']}-{stats['losses']} " +
                          f"({type_win_rate:.1f}%) | ${stats['profit']:+.2f}")
    else:
        print(f"All {total_bets} bets are PENDING")

    # Show best/worst bets
    completed_bets = [r for r in rows if r['Result'] in ['WIN', 'LOSS']]
    if completed_bets and len(completed_bets) >= 3:
        print(f"\nRecent Performance (Last 5 Settled):")
        for row in completed_bets[-5:]:
            result_emoji = '✅' if row['Result'] == 'WIN' else '❌'
            print(f"  {result_emoji} {row['Date']}: {row['Bet']} ({row['Odds']}) - " +
                  f"{row['Result']} {row['$25 Profit/Loss']}")


def main():
    """Display performance dashboard for all sports"""

    print("\n" + "=" * 80)
    print("CUMULATIVE PERFORMANCE BY SPORT")
    print("Showing results if betting $25 on every recommended bet")
    print("=" * 80)

    reports_dir = '/Users/dickgibbons/sports-betting/performance_reports'

    sports = [
        ('NHL', 'nhl_cumulative_performance.csv'),
        ('NBA', 'nba_cumulative_performance.csv'),
        ('NCAA', 'ncaa_cumulative_performance.csv'),
        ('Soccer', 'soccer_cumulative_performance.csv')
    ]

    for sport_name, filename in sports:
        filepath = os.path.join(reports_dir, filename)
        analyze_csv(filepath, sport_name)

    print("\n" + "=" * 80)
    print(f"📁 Detailed CSV files located at: {reports_dir}/")
    print("=" * 80)
    print("\nOpen the CSV files in Excel or Google Sheets to see:")
    print("  - Every bet with date, game, odds, and result")
    print("  - Running totals by sport and bet type")
    print("  - Complete betting angles for each pick")
    print()


if __name__ == '__main__':
    main()
