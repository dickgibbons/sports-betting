#!/usr/bin/env python3
"""Collect team stats for all leagues in the soccer dashboard.
Generates Season, L10, and L5 stats files."""

import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v3.football.api-sports.io"
# Free tier is ~10 requests/minute; stay under to avoid empty responses
REQUEST_DELAY_SEC = 7
_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = str(
    Path(os.environ.get("SPORTS_BETTING_DAILY_REPORTS", _ROOT / "Daily Reports"))
)
OUTPUT_FILES = {
    'season': f"{OUTPUT_DIR}/soccer_team_complete_stats.csv",
    'L10': f"{OUTPUT_DIR}/soccer_team_stats_L10.csv",
    'L5': f"{OUTPUT_DIR}/soccer_team_stats_L5.csv",
}

# All leagues from the dashboard (52 total) - (league_name, country)
SOCCER_LEAGUES = {
    # Top Tier - 3.0+ goals per game
    384: ("Israeli Premier", "Israel"),
    91: ("Fortuna Liga", "Slovakia"),
    164: ("Úrvalsdeild", "Iceland"),
    207: ("Swiss Super League", "Switzerland"),
    238: ("Primera A", "Colombia"),
    88: ("Eredivisie", "Netherlands"),
    188: ("K League 1", "South Korea"),
    119: ("Superliga", "Denmark"),
    366: ("Botola Pro", "Morocco"),
    78: ("Bundesliga", "Germany"),
    253: ("MLS", "USA"),
    169: ("UAE Pro League", "UAE"),
    373: ("Prva Liga", "Slovenia"),
    271: ("NB I", "Hungary"),
    79: ("2. Bundesliga", "Germany"),
    89: ("Eerste Divisie", "Netherlands"),
    108: ("Premijer Liga", "Bosnia"),
    # High Tier - 2.7-3.0 goals per game
    307: ("Saudi Pro League", "Saudi Arabia"),
    117: ("Meistriliiga", "Estonia"),
    106: ("Ekstraklasa", "Poland"),
    61: ("Ligue 1", "France"),
    39: ("Premier League", "England"),
    332: ("A Lyga", "Lithuania"),
    265: ("Primera Division", "Peru"),
    383: ("Egyptian Premier", "Egypt"),
    218: ("Austrian Bundesliga", "Austria"),
    286: ("Super Liga", "Serbia"),
    262: ("Liga MX", "Mexico"),
    210: ("HNL", "Croatia"),
    # Mid-High Tier - 2.5-2.7 goals per game
    98: ("J1 League", "Japan"),
    94: ("Primeira Liga", "Portugal"),
    40: ("Championship", "England"),
    42: ("League Two", "England"),
    281: ("Primera Division PY", "Paraguay"),
    197: ("Greek Super League", "Greece"),
    318: ("Virsliga", "Latvia"),
    345: ("Czech First League", "Czech Republic"),
    292: ("A-League", "Australia"),
    68: ("Thai League 1", "Thailand"),
    203: ("Turkish Super Lig", "Turkey"),
    333: ("Premier League", "Ukraine"),
    327: ("1. Division", "Cyprus"),
    41: ("League One", "England"),
    179: ("Scottish Premiership", "Scotland"),
    62: ("Ligue 2", "France"),
    140: ("La Liga", "Spain"),
    141: ("La Liga 2", "Spain"),
    235: ("Premier League RU", "Russia"),
    266: ("Primera Division", "Chile"),
    283: ("Liga 1", "Romania"),
    144: ("Jupiler Pro League", "Belgium"),
    136: ("Serie B", "Italy"),
}


def get_season_for_date(date_str):
    """Determine the football season for a given date."""
    date = datetime.strptime(date_str, '%Y-%m-%d')
    if date.month < 8:
        return date.year - 1
    return date.year


def fetch_fixtures_ft_paginated(headers, league_id, season):
    """Fetch all finished fixtures for a league/season.

    Uses the default request first (no ``page``), then follows ``paging`` for
    extra pages. Retries on rate-limit errors. Returns [] on plan/season errors
    so callers can try another season year.
    """
    url = f"{BASE_URL}/fixtures"
    all_games = []

    def fetch_page(page=None):
        params = {"league": league_id, "season": season, "status": "FT"}
        if page is not None:
            params["page"] = page
        for _ in range(3):
            response = requests.get(url, headers=headers, params=params, timeout=90)
            if response.status_code != 200:
                time.sleep(REQUEST_DELAY_SEC)
                continue
            data = response.json()
            err_raw = data.get("errors")
            err = str(err_raw) if err_raw else ""
            if "Too many requests" in err or "rateLimit" in err:
                time.sleep(65)
                continue
            if err_raw and "plan" in err.lower():
                return None
            return data
        return {}

    data = fetch_page(None)
    if data is None:
        return []

    batch = data.get("response", [])
    all_games.extend(batch)

    paging = data.get("paging") or {}
    total_pages = int(paging.get("total", 1) or 1)
    for page in range(2, total_pages + 1):
        time.sleep(0.35)
        data = fetch_page(page)
        if not data:
            break
        batch = data.get("response", [])
        if not batch:
            break
        all_games.extend(batch)

    if len(all_games) == 100 and total_pages <= 1:
        page = 2
        max_extra = 40
        while page <= max_extra:
            time.sleep(0.35)
            data = fetch_page(page)
            if not data:
                break
            batch = data.get("response", [])
            if not batch:
                break
            all_games.extend(batch)
            if len(batch) < 100:
                break
            page += 1

    return all_games


def calculate_team_stats(games, league_name, country, game_limit=None):
    """Calculate team stats from a list of games.

    Args:
        games: List of game data from API
        league_name: Name of the league
        country: Country of the league
        game_limit: If set, only use the last N games per team (5 or 10)

    Returns:
        List of team stat records
    """
    # Sort games by date (most recent first) to support game_limit
    sorted_games = sorted(games, key=lambda g: g.get('fixture', {}).get('date', ''), reverse=True)

    # Track games per team to apply limit
    team_game_counts = {}
    team_stats = {}

    for game in sorted_games:
        try:
            teams = game.get("teams", {})
            goals = game.get("goals", {})
            score = game.get("score", {})

            home_team = teams.get("home", {}).get("name", "")
            away_team = teams.get("away", {}).get("name", "")

            # Check if we've hit the game limit for either team
            if game_limit:
                home_count = team_game_counts.get(home_team, 0)
                away_count = team_game_counts.get(away_team, 0)
                process_home = home_count < game_limit
                process_away = away_count < game_limit
                if not process_home and not process_away:
                    continue
            else:
                process_home = True
                process_away = True

            home_goals = goals.get("home") or 0
            away_goals = goals.get("away") or 0

            # Get halftime scores
            ht = score.get("halftime", {})
            ht_home = ht.get("home") or 0
            ht_away = ht.get("away") or 0

            # Second half goals
            h2_home = home_goals - ht_home
            h2_away = away_goals - ht_away

            total = home_goals + away_goals
            h1_total = ht_home + ht_away
            h2_total = h2_home + h2_away

            # Initialize team stats if needed
            for team in [home_team, away_team]:
                if team not in team_stats:
                    team_stats[team] = {
                        'games': 0, 'total_goals': 0,
                        'goals_for': 0, 'goals_against': 0,
                        'h1_over_05': 0, 'over_15': 0, 'over_25': 0, 'over_35': 0,
                        'h1_over_15': 0, 'h2_over_15': 0,
                        'h1_scored': 0, 'h2_scored': 0,
                        'h1_total': 0, 'h2_total': 0,
                    }

            # Home team stats
            if process_home:
                ts = team_stats[home_team]
                ts['games'] += 1
                ts['total_goals'] += total
                ts['goals_for'] += home_goals
                ts['goals_against'] += away_goals
                ts['h1_over_05'] += 1 if h1_total > 0.5 else 0
                ts['over_15'] += 1 if total > 1.5 else 0
                ts['over_25'] += 1 if total > 2.5 else 0
                ts['over_35'] += 1 if total > 3.5 else 0
                ts['h1_over_15'] += 1 if h1_total > 1.5 else 0
                ts['h2_over_15'] += 1 if h2_total > 1.5 else 0
                ts['h1_scored'] += 1 if ht_home > 0 else 0
                ts['h2_scored'] += 1 if h2_home > 0 else 0
                ts['h1_total'] += h1_total
                ts['h2_total'] += h2_total
                team_game_counts[home_team] = team_game_counts.get(home_team, 0) + 1

            # Away team stats
            if process_away:
                ts = team_stats[away_team]
                ts['games'] += 1
                ts['total_goals'] += total
                ts['goals_for'] += away_goals
                ts['goals_against'] += home_goals
                ts['h1_over_05'] += 1 if h1_total > 0.5 else 0
                ts['over_15'] += 1 if total > 1.5 else 0
                ts['over_25'] += 1 if total > 2.5 else 0
                ts['over_35'] += 1 if total > 3.5 else 0
                ts['h1_over_15'] += 1 if h1_total > 1.5 else 0
                ts['h2_over_15'] += 1 if h2_total > 1.5 else 0
                ts['h1_scored'] += 1 if ht_away > 0 else 0
                ts['h2_scored'] += 1 if h2_away > 0 else 0
                ts['h1_total'] += h1_total
                ts['h2_total'] += h2_total
                team_game_counts[away_team] = team_game_counts.get(away_team, 0) + 1

        except Exception:
            continue

    # Convert to records with percentages
    # Minimum games: L5 needs 3, L10 needs 5, season needs 5
    min_games = 3 if game_limit == 5 else 5
    results = []
    for team, stats in team_stats.items():
        if stats['games'] >= min_games:
            g = stats['games']
            results.append({
                'league': league_name,
                'country': country,
                'team': team,
                'games': g,
                'avg_total': round(stats['total_goals'] / g, 2),
                'avg_scored': round(stats['goals_for'] / g, 2),
                'avg_conceded': round(stats['goals_against'] / g, 2),
                'h1_over_05_pct': round(100 * stats['h1_over_05'] / g, 1),
                'over_15_pct': round(100 * stats['over_15'] / g, 1),
                'over_25_pct': round(100 * stats['over_25'] / g, 1),
                'over_35_pct': round(100 * stats['over_35'] / g, 1),
                'h1_over_15_pct': round(100 * stats['h1_over_15'] / g, 1),
                'h2_over_15_pct': round(100 * stats['h2_over_15'] / g, 1),
                'h1_scored_pct': round(100 * stats['h1_scored'] / g, 1),
                'h2_scored_pct': round(100 * stats['h2_scored'] / g, 1),
                'h1_avg_total': round(stats['h1_total'] / g, 2),
                'h2_avg_total': round(stats['h2_total'] / g, 2),
            })

    return results


def collect_team_stats():
    """Collect team stats for all leagues and generate Season/L10/L5 files."""
    headers = {"x-apisports-key": API_KEY}

    today = datetime.now().strftime('%Y-%m-%d')
    season = get_season_for_date(today)

    print("=" * 60)
    print("SOCCER TEAM STATS COLLECTOR")
    print(f"Collecting data for {len(SOCCER_LEAGUES)} leagues (season {season})")
    print("=" * 60)

    # Store raw games data per league for reprocessing (league_name, country, games)
    all_games_by_league = {}

    for league_id, (league_name, country) in SOCCER_LEAGUES.items():
        print(f"  {league_name} ({country})...", end=" ", flush=True)

        try:
            games = []
            for try_season in (season, season - 1, season - 2, season - 3):
                games = fetch_fixtures_ft_paginated(headers, league_id, try_season)
                if games:
                    break

            if games:
                # Use (league_name, country) as key to handle duplicate league names
                all_games_by_league[(league_name, country)] = games
                print(f"{len(games)} games")
            else:
                print("no games")

            time.sleep(REQUEST_DELAY_SEC)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(REQUEST_DELAY_SEC)
            continue

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
        for (league_name, country), games in all_games_by_league.items():
            stats = calculate_team_stats(games, league_name, country, game_limit=game_limit)
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
    collect_team_stats()
