#!/usr/bin/env python3
"""
Generate Cumulative Performance Trackers by Sport
Creates detailed CSV reports showing every bet with $25 stake calculations
"""

import json
import csv
from collections import defaultdict
from datetime import datetime


def calculate_profit(odds, stake=25.0):
    """Calculate profit for a winning bet with given odds"""
    if odds > 0:  # Underdog (e.g., +180)
        return stake * (odds / 100)
    else:  # Favorite (e.g., -125)
        return stake / (abs(odds) / 100)


def load_bet_history():
    """Load bet history from JSON file"""
    with open('/Users/dickgibbons/sports-betting/data/bet_history.json', 'r') as f:
        return json.load(f)


def generate_sport_tracker(sport_name, bets, output_file):
    """Generate cumulative performance tracker for a specific sport"""

    if not bets:
        print(f"⚠️  No bets found for {sport_name}")
        return

    # Prepare CSV data
    rows = []
    running_total = 0.0
    running_totals_by_type = defaultdict(float)

    # Stats tracking
    stats = {
        'total_bets': 0,
        'wins': 0,
        'losses': 0,
        'pushes': 0,
        'pending': 0,
        'by_bet_type': defaultdict(lambda: {'bets': 0, 'wins': 0, 'losses': 0, 'profit': 0.0})
    }

    for bet in bets:
        result = bet.get('result', 'PENDING')
        odds = bet.get('odds')
        bet_type = bet.get('bet_type', 'Unknown')

        # Calculate $25 bet result
        if result == 'WIN' and odds:
            profit_25 = calculate_profit(odds, 25.0)
        elif result == 'LOSS':
            profit_25 = -25.0
        elif result == 'PUSH':
            profit_25 = 0.0
        else:  # PENDING or no odds
            profit_25 = None

        # Update running totals
        if profit_25 is not None:
            running_total += profit_25
            running_totals_by_type[bet_type] += profit_25

        # Update stats
        stats['total_bets'] += 1
        if result == 'WIN':
            stats['wins'] += 1
            stats['by_bet_type'][bet_type]['wins'] += 1
        elif result == 'LOSS':
            stats['losses'] += 1
            stats['by_bet_type'][bet_type]['losses'] += 1
        elif result == 'PUSH':
            stats['pushes'] += 1
        else:
            stats['pending'] += 1

        stats['by_bet_type'][bet_type]['bets'] += 1
        if profit_25 is not None:
            stats['by_bet_type'][bet_type]['profit'] += profit_25

        # Format odds display
        odds_display = f"{odds:+d}" if odds else "N/A"

        # Format profit display
        if profit_25 is not None:
            profit_display = f"${profit_25:+.2f}"
            running_display = f"${running_total:.2f}"
            type_running_display = f"${running_totals_by_type[bet_type]:.2f}"
        else:
            profit_display = "PENDING"
            running_display = f"${running_total:.2f}"
            type_running_display = f"${running_totals_by_type[bet_type]:.2f}"

        # Get angles summary
        angles_summary = " | ".join([a.get('reason', '') for a in bet.get('angles', [])])

        row = {
            'Date': bet.get('date', ''),
            'Game': bet.get('game', ''),
            'Bet': bet.get('bet', ''),
            'Bet Type': bet_type,
            'Odds': odds_display,
            'Confidence': bet.get('confidence', ''),
            'Expected Edge': f"{bet.get('expected_edge', 0):.1f}%",
            'Result': result,
            '$25 Profit/Loss': profit_display,
            'Running Total': running_display,
            'Type Running Total': type_running_display,
            'Angles': angles_summary
        }

        rows.append(row)

    # Write CSV
    if rows:
        fieldnames = ['Date', 'Game', 'Bet', 'Bet Type', 'Odds', 'Confidence',
                     'Expected Edge', 'Result', '$25 Profit/Loss', 'Running Total',
                     'Type Running Total', 'Angles']

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        print(f"✅ {sport_name} tracker saved: {output_file}")
        print(f"   Total bets: {stats['total_bets']}")
        print(f"   Record: {stats['wins']}-{stats['losses']}-{stats['pushes']} " +
              f"({stats['wins']/(stats['wins']+stats['losses'])*100:.1f}% win rate)" if stats['wins']+stats['losses'] > 0 else "")
        print(f"   Final running total (if all $25 bets): ${running_total:.2f}")
        print(f"   Pending: {stats['pending']}")

        # Print breakdown by bet type
        if len(stats['by_bet_type']) > 1:
            print(f"\n   Breakdown by bet type:")
            for bet_type, type_stats in sorted(stats['by_bet_type'].items()):
                if type_stats['wins'] + type_stats['losses'] > 0:
                    win_rate = type_stats['wins'] / (type_stats['wins'] + type_stats['losses']) * 100
                    print(f"   - {bet_type}: {type_stats['wins']}-{type_stats['losses']} " +
                          f"({win_rate:.1f}%) | ${type_stats['profit']:+.2f}")
        print()

    return stats


def main():
    """Generate all sport-specific performance trackers"""

    print("=" * 80)
    print("GENERATING CUMULATIVE PERFORMANCE TRACKERS BY SPORT")
    print("=" * 80)
    print()

    # Load all bets
    all_bets = load_bet_history()
    print(f"📊 Loaded {len(all_bets)} total bets from history\n")

    # Group by sport
    bets_by_sport = defaultdict(list)
    for bet in all_bets:
        sport = bet.get('sport', 'Unknown')
        bets_by_sport[sport].append(bet)

    # Create reports directory
    import os
    reports_dir = '/Users/dickgibbons/sports-betting/performance_reports'
    os.makedirs(reports_dir, exist_ok=True)

    # Generate tracker for each sport
    all_stats = {}

    for sport in ['NHL', 'NBA', 'NCAA', 'SOCCER']:
        if sport in bets_by_sport:
            output_file = f"{reports_dir}/{sport.lower()}_cumulative_performance.csv"
            stats = generate_sport_tracker(sport, bets_by_sport[sport], output_file)
            all_stats[sport] = stats

    # Generate summary report
    print("=" * 80)
    print("SUMMARY BY SPORT")
    print("=" * 80)
    print()

    for sport in ['NHL', 'NBA', 'NCAA', 'SOCCER']:
        if sport in all_stats:
            stats = all_stats[sport]
            settled = stats['wins'] + stats['losses']
            if settled > 0:
                win_rate = stats['wins'] / settled * 100
                print(f"🏒 {sport}:" if sport == 'NHL' else
                      f"🏀 {sport}:" if sport in ['NBA', 'NCAA'] else
                      f"⚽ {sport}:")
                print(f"   Record: {stats['wins']}-{stats['losses']}-{stats['pushes']} ({win_rate:.1f}%)")

                # Calculate total profit
                total_profit = sum(s['profit'] for s in stats['by_bet_type'].values())
                print(f"   Total Profit (@ $25/bet): ${total_profit:+.2f}")
                print()

    print("=" * 80)
    print(f"✅ All performance trackers saved to: {reports_dir}/")
    print("=" * 80)
    print()
    print("Files created:")
    for sport in ['NHL', 'NBA', 'NCAA', 'SOCCER']:
        if sport in bets_by_sport:
            print(f"  - {sport.lower()}_cumulative_performance.csv")


if __name__ == '__main__':
    main()
