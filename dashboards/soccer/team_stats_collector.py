"""
Team Stats Collector for Global Soccer Schedule Dashboard
Uses FootyStats API for comprehensive team statistics
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

# FootyStats API Configuration
FOOTYSTATS_API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
BASE_URL = "https://api.footystats.org"

# Output directory for stats
STATS_DIR = os.path.join(os.path.dirname(__file__), "data", "team_stats")
os.makedirs(STATS_DIR, exist_ok=True)


def fetch_todays_matches() -> List[Dict]:
    """Fetch today's matches from FootyStats"""
    url = f"{BASE_URL}/todays-matches"
    params = {"key": FOOTYSTATS_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("data", [])
    except Exception as e:
        print(f"Error fetching today's matches: {e}")

    return []


def fetch_team_stats(team_id: int) -> Optional[Dict]:
    """Fetch detailed stats for a team from FootyStats"""
    url = f"{BASE_URL}/team"
    params = {
        "key": FOOTYSTATS_API_KEY,
        "team_id": team_id
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("data"):
                # Return most recent season data
                return data["data"][0]
    except Exception as e:
        print(f"Error fetching team {team_id}: {e}")

    return None


def format_stats_row(team_data: Dict) -> Dict:
    """Format FootyStats team data into dashboard row"""
    stats = team_data.get("stats", {})

    # Build record strings
    wins = stats.get("seasonWinsNum_overall", 0)
    draws = stats.get("seasonDrawsNum_overall", 0)
    losses = stats.get("seasonLossesNum_overall", 0)
    record = f"{wins}-{draws}-{losses}"

    home_wins = stats.get("seasonWinsNum_home", 0)
    home_draws = stats.get("seasonDrawsNum_home", 0)
    home_losses = stats.get("seasonLossesNum_home", 0)
    home_record = f"{home_wins}-{home_draws}-{home_losses}"

    away_wins = stats.get("seasonWinsNum_away", 0)
    away_draws = stats.get("seasonDrawsNum_away", 0)
    away_losses = stats.get("seasonLossesNum_away", 0)
    away_record = f"{away_wins}-{away_draws}-{away_losses}"

    # Standing
    position = team_data.get("table_position", stats.get("leaguePosition_overall", "-"))
    ppg = stats.get("seasonPPG_overall", 0)
    standing = f"{position}/{ppg:.1f}ppg" if ppg else str(position)

    # BTTS stats
    btts_overall = stats.get("seasonBTTSPercentage_overall", 0)
    btts_home = stats.get("seasonBTTSPercentage_home", 0)
    btts_away = stats.get("seasonBTTSPercentage_away", 0)
    games = stats.get("seasonMatchesPlayed_overall", 0)
    btts_count = stats.get("seasonBTTS_overall", 0)

    return {
        "team_id": team_data.get("id"),
        "team": team_data.get("name", "Unknown"),
        "league": team_data.get("competition_id", ""),
        "country": team_data.get("country", ""),
        "season": team_data.get("season", ""),
        "record": record,
        "home_record": home_record,
        "away_record": away_record,
        "standing": standing,
        "games_played": games,
        # BTTS
        "btts_l10": f"{btts_count}/{games}" if games else "-",
        "btts_l5": f"{btts_overall}%",
        "btts_home_l10": f"{btts_home}%",
        "btts_away_l10": f"{btts_away}%",
        # Over percentages (overall)
        "over_15_pct": f"{stats.get('seasonOver15Percentage_overall', 0)}%",
        "over_25_pct": f"{stats.get('seasonOver25Percentage_overall', 0)}%",
        "over_35_pct": f"{stats.get('seasonOver35Percentage_overall', 0)}%",
        # Over percentages (home)
        "over_15_home_pct": f"{stats.get('seasonOver15Percentage_home', 0)}%",
        "over_25_home_pct": f"{stats.get('seasonOver25Percentage_home', 0)}%",
        "over_35_home_pct": f"{stats.get('seasonOver35Percentage_home', 0)}%",
        # Over percentages (away)
        "over_15_away_pct": f"{stats.get('seasonOver15Percentage_away', 0)}%",
        "over_25_away_pct": f"{stats.get('seasonOver25Percentage_away', 0)}%",
        "over_35_away_pct": f"{stats.get('seasonOver35Percentage_away', 0)}%",
        # Team scoring (overall)
        "team_over_05_pct": f"{stats.get('seasonOver05Percentage_overall', 0)}%",
        "team_over_15_pct": f"{100 - stats.get('seasonFTSPercentage_overall', 0)}%",  # FTS = failed to score
        "team_over_25_pct": f"{stats.get('seasonScoredOver2Percentage_overall', 0)}%",
        # Team scoring (home)
        "team_over_15_home_pct": f"{100 - stats.get('seasonFTSPercentage_home', 0)}%",
        "team_over_25_home_pct": f"{stats.get('seasonScoredOver2Percentage_home', 0)}%",
        # Team scoring (away)
        "team_over_15_away_pct": f"{100 - stats.get('seasonFTSPercentage_away', 0)}%",
        "team_over_25_away_pct": f"{stats.get('seasonScoredOver2Percentage_away', 0)}%",
        # Half stats
        "scored_1h_pct": f"{stats.get('seasonOver05PercentageHT_overall', 0)}%",
        "scored_2h_pct": f"{stats.get('over05_2hg_percentage_overall', 0)}%",
        # First half over/under (total goals in 1H)
        "first_half_over_05_pct": f"{stats.get('seasonOver05PercentageHT_overall', 0)}%",
        "first_half_over_15_pct": f"{stats.get('seasonOver15PercentageHT_overall', 0)}%",
        # Second half over/under (total goals in 2H)
        "second_half_over_05_pct": f"{stats.get('over05_2hg_percentage_overall', 0)}%",
        "second_half_over_15_pct": f"{stats.get('over15_2hg_percentage_overall', 0)}%",
        # Goals
        "avg_goals_for": stats.get("seasonScoredAVG_overall", 0),
        "avg_goals_against": stats.get("seasonConcededAVG_overall", 0),
        # Corners
        "corners_for_avg": stats.get("cornersAVG_overall", 0),
        "corners_against_avg": stats.get("cornersAgainstAVG_overall", 0),
    }


def collect_from_todays_matches():
    """Collect stats for all teams playing today"""
    print("Fetching today's matches...")
    matches = fetch_todays_matches()
    print(f"Found {len(matches)} matches today")

    # Extract unique team IDs
    team_ids = set()
    for match in matches:
        team_ids.add(match.get("homeID"))
        team_ids.add(match.get("awayID"))

    team_ids.discard(None)
    print(f"Found {len(team_ids)} unique teams")

    all_stats = []
    for i, team_id in enumerate(team_ids):
        print(f"  [{i+1}/{len(team_ids)}] Fetching team {team_id}...")
        team_data = fetch_team_stats(team_id)

        if team_data:
            row = format_stats_row(team_data)
            all_stats.append(row)
            print(f"    -> {row['team']} ({row['country']})")

        time.sleep(0.2)  # Rate limiting

    return all_stats


def collect_all_leagues():
    """Collect stats for all teams from FootyStats league list"""
    print("Fetching league list...")
    url = f"{BASE_URL}/league-list"
    params = {"key": FOOTYSTATS_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            leagues = data.get("data", [])
            print(f"Found {len(leagues)} leagues")

            # Filter to major leagues (top tiers)
            major_leagues = [l for l in leagues if l.get("tier") in [1, 2] or "premier" in l.get("name", "").lower()]
            print(f"Filtering to {len(major_leagues)} major leagues")

            return leagues
    except Exception as e:
        print(f"Error fetching leagues: {e}")

    return []


def run_collection():
    """Run stats collection for teams playing today"""
    print("=" * 60)
    print(f"FootyStats Team Stats Collection - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    all_stats = collect_from_todays_matches()

    if all_stats:
        df = pd.DataFrame(all_stats)
        output_file = os.path.join(STATS_DIR, "team_stats_current.csv")
        df.to_csv(output_file, index=False)
        print(f"\n Saved {len(all_stats)} team stats to {output_file}")

        # Backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        backup_file = os.path.join(STATS_DIR, f"team_stats_{timestamp}.csv")
        df.to_csv(backup_file, index=False)
        print(f" Backup saved to {backup_file}")
    else:
        print("\n No stats collected!")

    return all_stats


def merge_with_existing():
    """Merge new stats with existing CSV to build up database"""
    existing_file = os.path.join(STATS_DIR, "team_stats_current.csv")

    # Load existing if present
    existing_df = pd.DataFrame()
    if os.path.exists(existing_file):
        existing_df = pd.read_csv(existing_file)
        print(f"Loaded {len(existing_df)} existing team records")

    # Collect new stats
    new_stats = collect_from_todays_matches()

    if new_stats:
        new_df = pd.DataFrame(new_stats)

        if not existing_df.empty:
            # Merge - update existing teams, add new ones
            combined = pd.concat([existing_df, new_df])
            # Keep latest entry for each team
            combined = combined.drop_duplicates(subset=["team_id"], keep="last")
            combined.to_csv(existing_file, index=False)
            print(f"\n Merged: {len(combined)} total teams (added {len(combined) - len(existing_df)} new)")
        else:
            new_df.to_csv(existing_file, index=False)
            print(f"\n Saved {len(new_df)} team stats")

    return new_stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--merge":
        merge_with_existing()
    else:
        run_collection()
