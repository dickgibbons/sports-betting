#!/usr/bin/env python3
"""
Generate NHL team scoring report showing:
1. Percent of games where team scored 1.5+ goals (i.e., 2+ goals)
2. Number of times held under 1.5 goals (0-1 goals) for 2+ games in a row
"""

import requests
from datetime import datetime
import csv
import os
import time

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v1.hockey.api-sports.io"
NHL_LEAGUE_ID = 57

def get_season():
    """Determine the current season (hockey seasons run Sept-May)."""
    now = datetime.now()
    if now.month >= 9:
        return now.year
    else:
        return now.year - 1


def fetch_nhl_games(season: int) -> list:
    """Fetch all finished NHL games for a season."""
    headers = {"x-apisports-key": API_KEY}
    params = {
        "league": NHL_LEAGUE_ID,
        "season": str(season),
        "timezone": "America/New_York"
    }

    url = f"{BASE_URL}/games"
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    games = []
    for game in data.get("response", []):
        status = game.get("status", {}).get("short", "")
        if status in ["FT", "AOT", "AP", "POST"]:  # Finished games only
            home_team = game["teams"]["home"]["name"]
            away_team = game["teams"]["away"]["name"]
            home_id = game["teams"]["home"]["id"]
            away_id = game["teams"]["away"]["id"]
            home_score = game["scores"]["home"]
            away_score = game["scores"]["away"]
            game_date = game["date"]

            games.append({
                "date": game_date,
                "home_team": home_team,
                "away_team": away_team,
                "home_id": home_id,
                "away_id": away_id,
                "home_score": home_score,
                "away_score": away_score
            })

    return games


def build_team_game_history(games: list) -> dict:
    """Build per-team game history from all games."""
    team_games = {}

    for game in games:
        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = game["home_score"]
        away_score = game["away_score"]
        game_date = game["date"]

        # Add home team's perspective
        if home_team not in team_games:
            team_games[home_team] = []
        team_games[home_team].append({
            "date": game_date,
            "team_score": home_score
        })

        # Add away team's perspective
        if away_team not in team_games:
            team_games[away_team] = []
        team_games[away_team].append({
            "date": game_date,
            "team_score": away_score
        })

    # Sort each team's games by date
    for team in team_games:
        team_games[team].sort(key=lambda x: x["date"])

    return team_games


def analyze_team_scoring(games: list) -> dict:
    """Analyze scoring patterns for a team."""
    if not games:
        return {"pct_over_1_5": 0, "streaks_under_1_5": 0, "total_games": 0, "games_over_1_5": 0}

    total_games = len(games)
    games_over_1_5 = 0  # Games with 2+ goals
    current_under_streak = 0
    streaks_under_1_5 = 0  # Times held under 2 goals for 2+ games in a row

    for game in games:
        score = game["team_score"]
        if score is None:
            continue

        if score >= 2:  # 1.5+ means 2 or more goals
            games_over_1_5 += 1
            # If we had a streak of 2+, count it
            if current_under_streak >= 2:
                streaks_under_1_5 += 1
            current_under_streak = 0
        else:  # 0 or 1 goal
            current_under_streak += 1

    # Check if we ended on a streak
    if current_under_streak >= 2:
        streaks_under_1_5 += 1

    pct_over_1_5 = (games_over_1_5 / total_games * 100) if total_games > 0 else 0

    return {
        "pct_over_1_5": round(pct_over_1_5, 1),
        "streaks_under_1_5": streaks_under_1_5,
        "total_games": total_games,
        "games_over_1_5": games_over_1_5
    }


def main():
    season = get_season()
    print(f"Fetching NHL games for {season}-{season+1} season...")

    games = fetch_nhl_games(season)
    print(f"Found {len(games)} finished games")

    if not games:
        print("No games found. Check API connection.")
        return

    # Build team game history
    team_games = build_team_game_history(games)
    print(f"Found {len(team_games)} teams")

    results = []

    for team_name, team_game_list in team_games.items():
        analysis = analyze_team_scoring(team_game_list)

        results.append({
            "Team": team_name,
            "Games": analysis["total_games"],
            "Games_Over_1.5": analysis["games_over_1_5"],
            "Pct_Over_1.5": analysis["pct_over_1_5"],
            "Streaks_Under_1.5_2+_Games": analysis["streaks_under_1_5"]
        })

    # Sort by Pct_Over_1.5 descending
    results.sort(key=lambda x: x["Pct_Over_1.5"], reverse=True)

    # Save to CSV
    output_dir = "/Users/dickgibbons/AI Projects/sports-betting/Daily Reports"
    output_file = os.path.join(output_dir, "NHL_TEAM_SCORING_STREAKS.csv")

    with open(output_file, 'w', newline='') as f:
        fieldnames = ["Team", "Games", "Games_Over_1.5", "Pct_Over_1.5", "Streaks_Under_1.5_2+_Games"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nReport saved to: {output_file}")

    # Print summary
    print("\n" + "=" * 80)
    print(f"NHL TEAM SCORING REPORT - {season}-{season+1} Season")
    print("=" * 80)
    print(f"{'Team':<30} {'Games':>6} {'O1.5%':>8} {'Streaks <1.5 (2+ games)':>25}")
    print("-" * 80)
    for r in results:
        print(f"{r['Team']:<30} {r['Games']:>6} {r['Pct_Over_1.5']:>7.1f}% {r['Streaks_Under_1.5_2+_Games']:>25}")


if __name__ == "__main__":
    main()
