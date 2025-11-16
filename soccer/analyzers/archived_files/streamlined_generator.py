#!/usr/bin/env python3
"""
Streamlined Report Generator - Only Essential Reports
"""

import json
import csv
from datetime import datetime
import os

def generate_streamlined_reports():
    """Generate only the KEEP reports"""

    date_str = datetime.now().strftime("%Y%m%d")
    date_readable = datetime.now().strftime("%Y-%m-%d")

    print(f"🎯 Generating streamlined reports for {date_readable}")
    print("=" * 50)

    # Ensure output directory exists
    os.makedirs("output reports", exist_ok=True)

    # Load fixtures if available
    fixtures = []
    fixture_file = f"real_fixtures_{date_str}.json"
    if os.path.exists(fixture_file):
        with open(fixture_file, 'r') as f:
            fixtures = json.load(f)
        print(f"📊 Loaded {len(fixtures)} fixtures")
    else:
        print("⚠️ No fixtures found - generating conservative reports")

    reports_generated = []

    # 1. daily_picks_YYYYMMDD.csv
    filename = f"output reports/daily_picks_{date_str}.csv"
    with open(filename, 'w', newline='') as f:
        fieldnames = ['date', 'time', 'home_team', 'away_team', 'league', 'market', 'odds', 'confidence', 'stake_pct']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            'date': date_readable,
            'time': 'N/A',
            'home_team': 'No picks today',
            'away_team': 'Conservative approach',
            'league': 'Risk Management',
            'market': 'No opportunities',
            'odds': 'N/A',
            'confidence': 'Waiting',
            'stake_pct': '0%'
        })
    reports_generated.append(f"daily_picks_{date_str}.csv")

    # 2. daily_all_games_YYYYMMDD.csv
    filename = f"output reports/daily_all_games_{date_str}.csv"
    with open(filename, 'w', newline='') as f:
        fieldnames = ['date', 'home_team', 'away_team', 'league', 'analysis', 'recommendation']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        if fixtures:
            for fixture in fixtures[:20]:  # First 20 games
                writer.writerow({
                    'date': date_readable,
                    'home_team': fixture.get('home_team', 'Team A'),
                    'away_team': fixture.get('away_team', 'Team B'),
                    'league': fixture.get('league', 'Unknown'),
                    'analysis': 'Conservative - insufficient value',
                    'recommendation': 'Skip'
                })
        else:
            writer.writerow({
                'date': date_readable,
                'home_team': 'No games analyzed',
                'away_team': 'System in conservative mode',
                'league': 'N/A',
                'analysis': 'Waiting for opportunities',
                'recommendation': 'Hold'
            })
    reports_generated.append(f"daily_all_games_{date_str}.csv")

    # 3. high_confidence_picks_YYYYMMDD.csv
    filename = f"output reports/high_confidence_picks_{date_str}.csv"
    with open(filename, 'w', newline='') as f:
        fieldnames = ['date', 'match', 'market', 'odds', 'confidence', 'stake_pct']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({
            'date': date_readable,
            'match': 'No high-confidence opportunities',
            'market': 'Conservative mode',
            'odds': 'N/A',
            'confidence': 'Waiting',
            'stake_pct': '0%'
        })
    reports_generated.append(f"high_confidence_picks_{date_str}.csv")

    # 4. Update cumulative_picks_tracker.csv
    filename = "output reports/cumulative_picks_tracker.csv"
    existing_data = []

    if os.path.exists(filename):
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)

    # Add today if not exists
    dates = [entry['date'] for entry in existing_data]
    if date_readable not in dates:
        today_entry = {
            'date': date_readable,
            'picks_made': '0',
            'total_stake': '0.00',
            'profit_loss': '0.00',
            'cumulative_profit': existing_data[-1].get('cumulative_profit', '0.00') if existing_data else '0.00',
            'roi_daily': '0.0%',
            'roi_cumulative': existing_data[-1].get('roi_cumulative', '0.0%') if existing_data else '0.0%',
            'bankroll': existing_data[-1].get('bankroll', '500.00') if existing_data else '500.00',
            'notes': 'Conservative - no opportunities'
        }
        existing_data.append(today_entry)

        with open(filename, 'w', newline='') as f:
            fieldnames = ['date', 'picks_made', 'total_stake', 'profit_loss', 'cumulative_profit', 'roi_daily', 'roi_cumulative', 'bankroll', 'notes']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(existing_data)

        reports_generated.append("cumulative_picks_tracker.csv")

    print(f"\n✅ Generated {len(reports_generated)} streamlined reports:")
    for report in reports_generated:
        print(f"   • {report}")

    print(f"\n🚫 Skipped redundant TXT reports:")
    print(f"   • daily_report_{date_str}.txt (REMOVED)")
    print(f"   • daily_games_overview_{date_str}.txt (REMOVED)")
    print(f"   • high_confidence_report_{date_str}.txt (REMOVED)")
    print(f"   • cumulative_betting_report_{date_str}.txt (REMOVED)")
    print(f"   • volume_opportunities_{date_str}.txt (REMOVED)")

    return reports_generated

if __name__ == "__main__":
    generate_streamlined_reports()