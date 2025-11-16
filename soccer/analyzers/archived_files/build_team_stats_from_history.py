#!/usr/bin/env python3
"""
Build Team Statistics from Historical Match Data
Uses the training_history.csv to calculate team-specific statistics
More reliable than API since we already have the historical data
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def build_team_stats_from_history():
    """Calculate team statistics from historical match data"""

    print("=" * 70)
    print("📊 BUILDING TEAM STATISTICS FROM HISTORICAL DATA")
    print("=" * 70)

    # Load historical match data
    history_file = Path('training_history.csv')

    if not history_file.exists():
        print("❌ No training_history.csv found")
        return

    df = pd.read_csv(history_file)
    print(f"\n✅ Loaded {len(df)} historical matches")

    # Calculate statistics for each team
    team_stats = {}

    # Get unique teams
    home_teams = df[['home_team_id', 'home_team_name']].rename(
        columns={'home_team_id': 'team_id', 'home_team_name': 'team_name'}
    )
    away_teams = df[['away_team_id', 'away_team_name']].rename(
        columns={'away_team_id': 'team_id', 'away_team_name': 'team_name'}
    )
    all_teams = pd.concat([home_teams, away_teams]).drop_duplicates('team_id')

    print(f"📊 Analyzing {len(all_teams)} unique teams...\n")

    for idx, row in all_teams.iterrows():
        team_id = int(row['team_id'])
        team_name = row['team_name']

        # Get home matches for this team
        home_matches = df[df['home_team_id'] == team_id].copy()

        # Get away matches for this team
        away_matches = df[df['away_team_id'] == team_id].copy()

        # Calculate home statistics
        if len(home_matches) > 0:
            wins_home = len(home_matches[home_matches['winner'] == 'home'])
            draws_home = len(home_matches[home_matches['winner'] == 'draw'])
            loses_home = len(home_matches[home_matches['winner'] == 'away'])
            goals_for_avg_home = home_matches['home_goals'].mean()
            goals_against_avg_home = home_matches['away_goals'].mean()
            clean_sheets_home = len(home_matches[home_matches['away_goals'] == 0])
            failed_to_score_home = len(home_matches[home_matches['home_goals'] == 0])
        else:
            wins_home = draws_home = loses_home = 0
            goals_for_avg_home = goals_against_avg_home = 0.0
            clean_sheets_home = failed_to_score_home = 0

        # Calculate away statistics
        if len(away_matches) > 0:
            wins_away = len(away_matches[away_matches['winner'] == 'away'])
            draws_away = len(away_matches[away_matches['winner'] == 'draw'])
            loses_away = len(away_matches[away_matches['winner'] == 'home'])
            goals_for_avg_away = away_matches['away_goals'].mean()
            goals_against_avg_away = away_matches['home_goals'].mean()
            clean_sheets_away = len(away_matches[away_matches['home_goals'] == 0])
            failed_to_score_away = len(away_matches[away_matches['away_goals'] == 0])
        else:
            wins_away = draws_away = loses_away = 0
            goals_for_avg_away = goals_against_avg_away = 0.0
            clean_sheets_away = failed_to_score_away = 0

        # Build stats entry
        team_key = f"{team_id}_2024"
        team_stats[team_key] = {
            'team_id': team_id,
            'team_name': team_name,
            'season': 2024,
            'last_updated': datetime.now().isoformat(),

            # Match counts
            'played': len(home_matches) + len(away_matches),
            'played_home': len(home_matches),
            'played_away': len(away_matches),

            # Results
            'wins_home': wins_home,
            'wins_away': wins_away,
            'draws_home': draws_home,
            'draws_away': draws_away,
            'loses_home': loses_home,
            'loses_away': loses_away,

            # Goals
            'goals_for_avg_home': round(goals_for_avg_home, 2),
            'goals_for_avg_away': round(goals_for_avg_away, 2),
            'goals_against_avg_home': round(goals_against_avg_home, 2),
            'goals_against_avg_away': round(goals_against_avg_away, 2),

            # Clean sheets
            'clean_sheets_home': clean_sheets_home,
            'clean_sheets_away': clean_sheets_away,
            'failed_to_score_home': failed_to_score_home,
            'failed_to_score_away': failed_to_score_away,
        }

        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1} teams...")

    # Save to file
    output_file = Path('team_statistics.json')
    with open(output_file, 'w') as f:
        json.dump(team_stats, f, indent=2)

    print(f"\n✅ COMPLETE")
    print(f"=" * 70)
    print(f"   Teams processed: {len(team_stats)}")
    print(f"   Output file: {output_file}")

    # Print sample statistics
    print(f"\n📊 Sample Team Statistics:")
    for team_key in list(team_stats.keys())[:5]:
        stats = team_stats[team_key]
        print(f"\n   {stats['team_name']} (ID: {stats['team_id']})")
        print(f"      Played: {stats['played']} ({stats['played_home']} home, {stats['played_away']} away)")
        print(f"      Home: W{stats['wins_home']}-D{stats['draws_home']}-L{stats['loses_home']}")
        print(f"      Away: W{stats['wins_away']}-D{stats['draws_away']}-L{stats['loses_away']}")
        print(f"      Goals/game (H): {stats['goals_for_avg_home']:.2f} for, {stats['goals_against_avg_home']:.2f} against")
        print(f"      Goals/game (A): {stats['goals_for_avg_away']:.2f} for, {stats['goals_against_avg_away']:.2f} against")

    print(f"\n{'=' * 70}\n")


if __name__ == "__main__":
    build_team_stats_from_history()
