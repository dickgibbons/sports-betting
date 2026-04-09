#!/usr/bin/env python3
"""
Hockey Team Stats Collector
Fetches historical game data and calculates team statistics for all DraftKings leagues.
Uses API-Hockey to get game results with period scores.
"""

import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v1.hockey.api-sports.io"
_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = str(
    Path(os.environ.get("SPORTS_BETTING_DAILY_REPORTS", _ROOT / "Daily Reports"))
)
OUTPUT_FILES = {
    'season': f"{OUTPUT_DIR}/draftkings_hockey_team_stats_with_1p.csv",
    'L10': f"{OUTPUT_DIR}/draftkings_hockey_team_stats_L10.csv",
    'L5': f"{OUTPUT_DIR}/draftkings_hockey_team_stats_L5.csv",
}

# DraftKings leagues (ID, Name)
LEAGUES = {
    57: "NHL",
    16: "Finnish - SM Liiga",
    47: "Sweden - SHL",
    49: "Sweden - HockeyAllsvenskan",
    69: "Alps Hockey League",
    70: "Austria Ice Hockey League",
    146: "Champions Hockey League",
    11: "Czech - Chance Liga",
    12: "Denmark - Metal Ligaen",
    14: "Finnish - Mestis",
    18: "France - Ligue Magnus",
    19: "German - DEL",
    26: "Latvia - Premjer Liga",
    86: "Norway - EHL",
    30: "Norway - 1st Division",
    32: "Poland - Extraliga",
    261: "PWHL Women",
    91: "Slovakia - Extraliga",
    42: "Slovakia - Liga1",
    51: "Swiss - National League",
    52: "Switzerland - Swiss League",
}


def get_season_for_league(league_id):
    """Determine the current season for a league (most start in September)."""
    now = datetime.now()
    # Hockey seasons run Sept-May
    if now.month >= 9:
        return now.year
    else:
        return now.year - 1


def fetch_games_for_league(league_id, league_name, season):
    """Fetch all finished games for a league/season."""
    headers = {"x-apisports-key": API_KEY}

    url = f"{BASE_URL}/games"
    params = {
        "league": league_id,
        "season": season,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        if response.status_code == 200:
            data = response.json()
            all_games = data.get("response", [])
            # Filter to finished games only
            finished_games = [g for g in all_games if g.get('status', {}).get('short') in ['FT', 'AOT', 'AP']]
            return finished_games
        else:
            print(f"  Error {response.status_code} for {league_name}")
            return []
    except Exception as e:
        print(f"  Exception for {league_name}: {e}")
        return []


def calculate_team_stats(games, league_name, game_limit=None):
    """Calculate statistics per team from games.

    Args:
        games: List of game data
        league_name: Name of the league
        game_limit: If set, only use the last N games per team (e.g., 5 or 10)
    """
    # Sort games by date (most recent first) to support game_limit
    sorted_games = sorted(games, key=lambda g: g.get('date', ''), reverse=True)

    # Track games per team to apply limit
    team_game_counts = {}
    team_stats = {}

    for game in sorted_games:
        try:
            home_team = game['teams']['home']['name']
            away_team = game['teams']['away']['name']

            # Check if we've hit the game limit for either team
            if game_limit:
                home_count = team_game_counts.get(home_team, 0)
                away_count = team_game_counts.get(away_team, 0)
                # Skip this game for a team if they've hit the limit
                process_home = home_count < game_limit
                process_away = away_count < game_limit
                if not process_home and not process_away:
                    continue
            else:
                process_home = True
                process_away = True

            # Full-time score
            home_goals = game['scores']['home'] or 0
            away_goals = game['scores']['away'] or 0
            total_goals = home_goals + away_goals

            # First period score (from periods)
            # API returns periods as strings like "1-2" (away-home format)
            periods = game.get('periods', {})
            p1_str = periods.get('first', '0-0') or '0-0'
            try:
                parts = p1_str.split('-')
                p1_away = int(parts[0]) if parts[0] else 0
                p1_home = int(parts[1]) if len(parts) > 1 and parts[1] else 0
            except (ValueError, IndexError):
                p1_home = 0
                p1_away = 0
            p1_total = p1_home + p1_away

            # Initialize team stats if needed
            for team in [home_team, away_team]:
                if team not in team_stats:
                    team_stats[team] = {
                        'games': 0,
                        'goals_for': 0,
                        'goals_against': 0,
                        'total_goals': 0,
                        'p1_total_goals': 0,
                        'p1_over_1_5': 0,
                        'p1_scored': 0,
                        # Team scoring overs
                        'team_over_1_5': 0,
                        'team_over_2_5': 0,
                        'team_over_3_5': 0,
                        # Team 1P scoring
                        'team_1p_goals': 0,
                        # Game total overs
                        'game_over_5_5': 0,
                        'game_over_6_5': 0,
                        'game_over_7_5': 0,
                    }

            # Update home team stats (if not at limit)
            if process_home:
                team_stats[home_team]['games'] += 1
                team_stats[home_team]['goals_for'] += home_goals
                team_stats[home_team]['goals_against'] += away_goals
                team_stats[home_team]['total_goals'] += total_goals
                team_stats[home_team]['p1_total_goals'] += p1_total
                team_stats[home_team]['p1_over_1_5'] += 1 if p1_total >= 2 else 0
                team_stats[home_team]['p1_scored'] += 1 if p1_home >= 1 else 0
                team_stats[home_team]['team_1p_goals'] += p1_home
                # Team scoring thresholds
                team_stats[home_team]['team_over_1_5'] += 1 if home_goals >= 2 else 0
                team_stats[home_team]['team_over_2_5'] += 1 if home_goals >= 3 else 0
                team_stats[home_team]['team_over_3_5'] += 1 if home_goals >= 4 else 0
                # Game total thresholds
                team_stats[home_team]['game_over_5_5'] += 1 if total_goals >= 6 else 0
                team_stats[home_team]['game_over_6_5'] += 1 if total_goals >= 7 else 0
                team_stats[home_team]['game_over_7_5'] += 1 if total_goals >= 8 else 0
                # Update game count for limit tracking
                team_game_counts[home_team] = team_game_counts.get(home_team, 0) + 1

            # Update away team stats (if not at limit)
            if process_away:
                team_stats[away_team]['games'] += 1
                team_stats[away_team]['goals_for'] += away_goals
                team_stats[away_team]['goals_against'] += home_goals
                team_stats[away_team]['total_goals'] += total_goals
                team_stats[away_team]['p1_total_goals'] += p1_total
                team_stats[away_team]['p1_over_1_5'] += 1 if p1_total >= 2 else 0
                team_stats[away_team]['p1_scored'] += 1 if p1_away >= 1 else 0
                team_stats[away_team]['team_1p_goals'] += p1_away
                # Team scoring thresholds
                team_stats[away_team]['team_over_1_5'] += 1 if away_goals >= 2 else 0
                team_stats[away_team]['team_over_2_5'] += 1 if away_goals >= 3 else 0
                team_stats[away_team]['team_over_3_5'] += 1 if away_goals >= 4 else 0
                # Game total thresholds
                team_stats[away_team]['game_over_5_5'] += 1 if total_goals >= 6 else 0
                team_stats[away_team]['game_over_6_5'] += 1 if total_goals >= 7 else 0
                team_stats[away_team]['game_over_7_5'] += 1 if total_goals >= 8 else 0
                # Update game count for limit tracking
                team_game_counts[away_team] = team_game_counts.get(away_team, 0) + 1

        except Exception as e:
            continue

    # Convert to results with percentages
    # Minimum games depends on the limit: L5 needs at least 3, L10 needs at least 5, season needs 5
    min_games = 3 if game_limit == 5 else 5
    results = []
    for team, stats in team_stats.items():
        if stats['games'] >= min_games:
            results.append({
                'league': league_name,
                'team': team,
                'games': stats['games'],
                'goals_for': stats['goals_for'],
                'goals_against': stats['goals_against'],
                'total_goals': stats['total_goals'],
                'avg_total': round(stats['total_goals'] / stats['games'], 2),
                'avg_scored': round(stats['goals_for'] / stats['games'], 2),
                'avg_conceded': round(stats['goals_against'] / stats['games'], 2),
                'avg_1p_total': round(stats['p1_total_goals'] / stats['games'], 2),
                'pct_1p_over_1_5': round(stats['p1_over_1_5'] / stats['games'] * 100, 1),
                'avg_1p_scored': round(stats['team_1p_goals'] / stats['games'], 2),
                'pct_1p_scored': round(stats['p1_scored'] / stats['games'] * 100, 1),
                # New team scoring percentages
                'pct_scored_over_1_5': round(stats['team_over_1_5'] / stats['games'] * 100, 1),
                'pct_scored_over_2_5': round(stats['team_over_2_5'] / stats['games'] * 100, 1),
                'pct_scored_over_3_5': round(stats['team_over_3_5'] / stats['games'] * 100, 1),
                # Game total percentages
                'pct_over_5_5': round(stats['game_over_5_5'] / stats['games'] * 100, 1),
                'pct_over_6_5': round(stats['game_over_6_5'] / stats['games'] * 100, 1),
                'pct_over_7_5': round(stats['game_over_7_5'] / stats['games'] * 100, 1),
            })

    return results


def main():
    """Main function to collect stats for all leagues."""
    print("=" * 60)
    print("HOCKEY TEAM STATS COLLECTOR")
    print(f"Collecting data for {len(LEAGUES)} leagues")
    print("=" * 60)

    # Store raw games data per league for reprocessing
    all_games_by_league = {}

    for league_id, league_name in LEAGUES.items():
        season = get_season_for_league(league_id)
        print(f"\n{league_name} (ID: {league_id}, Season: {season})...")

        games = fetch_games_for_league(league_id, league_name, season)
        print(f"  Found {len(games)} finished games")

        if games:
            all_games_by_league[league_name] = games

        # Rate limiting
        time.sleep(7)

    # Generate stats for each period type: season, L10, L5
    periods = [
        ('season', None, OUTPUT_FILES['season']),
        ('L10', 10, OUTPUT_FILES['L10']),
        ('L5', 5, OUTPUT_FILES['L5']),
    ]

    for period_name, game_limit, output_file in periods:
        print(f"\n{'=' * 60}")
        print(f"Generating {period_name.upper()} stats...")
        print("=" * 60)

        all_stats = []
        for league_name, games in all_games_by_league.items():
            stats = calculate_team_stats(games, league_name, game_limit=game_limit)
            all_stats.extend(stats)
            print(f"  {league_name}: {len(stats)} teams")

        if all_stats:
            df = pd.DataFrame(all_stats)
            df = df.sort_values('avg_total', ascending=False)
            df.to_csv(output_file, index=False)
            print(f"Saved {len(df)} team records to {output_file}")
        else:
            print(f"No stats for {period_name}!")

    print("\n" + "=" * 60)
    print("COMPLETE: Generated all three stat files")
    print("=" * 60)


if __name__ == "__main__":
    main()
