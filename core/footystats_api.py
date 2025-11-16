#!/usr/bin/env python3
"""
FootyStats API Adapter
Provides historical match data for backtesting
"""

import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FootyStatsAPI:
    """FootyStats API client for historical soccer data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.footystats.org"
        self.session = requests.Session()

        # Season ID mapping for multiple seasons
        # European seasons run Aug-May, so 2024/2025 = Aug 2024 - May 2025
        self.seasons = {
            '2024/2025': {
                'Premier League': 12325,
                'La Liga': 12316,
                'Serie A': 12530,
                'Bundesliga': 12529,
                'Ligue 1': 12337,
                'Brazil Serie A': 11321,
            },
            '2025/2026': {
                # Season IDs for 2025/2026 (Aug 2025 - May 2026)
                # These need to be updated once FootyStats publishes them
                'Premier League': 12326,  # Estimated - increment from previous
                'La Liga': 12317,
                'Serie A': 12531,
                'Bundesliga': 12530,
                'Ligue 1': 12338,
            }
        }

        # Default to current season
        self.season_ids = self.seasons['2024/2025']

    def _get_season_for_date(self, date_str: str) -> str:
        """Determine which season a date falls into"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month

        # European seasons run Aug-May
        # If date is Aug-Dec, it's the start of a season (e.g., Aug 2025 = 2025/2026)
        # If date is Jan-Jul, it's the end of a season (e.g., Feb 2025 = 2024/2025)
        if month >= 8:  # August onwards
            return f"{year}/{year+1}"
        else:  # January-July
            return f"{year-1}/{year}"

    def get_matches_by_date(self, date_str: str) -> List[Dict]:
        """
        Get all matches for a specific date

        Args:
            date_str: Date in format 'YYYY-MM-DD'

        Returns:
            List of match dictionaries
        """
        matches = []
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')

        # Automatically select the correct season based on date
        season = self._get_season_for_date(date_str)
        if season in self.seasons:
            self.season_ids = self.seasons[season]
            print(f"\n🔍 Fetching matches for {date_str} (Season: {season})...")
        else:
            print(f"\n⚠️  Season {season} not configured, using default...")
            print(f"🔍 Fetching matches for {date_str}...")

        # Fetch matches from each league
        for league_name, season_id in self.season_ids.items():
            try:
                league_matches = self._get_league_matches(season_id, date_str, league_name)
                if league_matches:
                    print(f"  ✅ {league_name}: {len(league_matches)} matches")
                    matches.extend(league_matches)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"  ⚠️  {league_name}: {str(e)}")
                continue

        print(f"📊 Total matches found: {len(matches)}")
        return matches

    def _get_league_matches(self, season_id: int, date_str: str, league_name: str) -> List[Dict]:
        """Get matches for a specific league and date"""

        # Use league-matches endpoint with season_id
        url = f"{self.base_url}/league-matches"

        params = {
            'key': self.api_key,
            'season_id': season_id
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data:
                return []

            # Filter matches by date
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            matches = []

            for match in data['data']:
                # Parse match date from Unix timestamp
                date_unix = match.get('date_unix')
                if not date_unix:
                    continue

                try:
                    match_datetime = datetime.fromtimestamp(int(date_unix))
                    match_date = match_datetime.date()

                    if match_date == target_date:
                        # Only include completed matches for backtesting
                        if match.get('status') == 'complete':
                            matches.append(self._parse_match(match, league_name))
                except Exception as e:
                    continue

            return matches

        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {str(e)}")

    def _parse_match(self, match_data: Dict, league_name: str) -> Dict:
        """Parse FootyStats match data into standard format"""

        # Extract basic info
        home_team = match_data.get('home_name', 'Unknown')
        away_team = match_data.get('away_name', 'Unknown')

        # Extract scores
        home_score = match_data.get('homeGoalCount', 0)
        away_score = match_data.get('awayGoalCount', 0)

        # Determine outcome
        if home_score > away_score:
            outcome = 'home'
        elif away_score > home_score:
            outcome = 'away'
        else:
            outcome = 'draw'

        # Extract odds (pre-match odds)
        home_odds = float(match_data.get('odds_ft_1', 0)) or 2.0
        draw_odds = float(match_data.get('odds_ft_x', 0)) or 3.2
        away_odds = float(match_data.get('odds_ft_2', 0)) or 3.5

        # Extract totals
        total_goals = home_score + away_score
        over_2_5 = total_goals > 2.5
        btts = home_score > 0 and away_score > 0

        # Extract BTTS odds if available
        btts_yes_odds = float(match_data.get('odds_btts_yes', 0)) or 1.8
        btts_no_odds = float(match_data.get('odds_btts_no', 0)) or 1.9

        # Extract corners data
        home_corners = match_data.get('homeCorners', 0) or 0
        away_corners = match_data.get('awayCorners', 0) or 0
        total_corners = home_corners + away_corners
        over_9_5_corners = total_corners > 9.5

        # Extract corners odds if available
        corners_over_9_5_odds = float(match_data.get('odds_corners_over_9_5', 0)) or 1.9
        corners_under_9_5_odds = float(match_data.get('odds_corners_under_9_5', 0)) or 1.9

        # Parse date and time from Unix timestamp
        date_unix = match_data.get('date_unix')
        if date_unix:
            match_datetime = datetime.fromtimestamp(int(date_unix))
            match_date = match_datetime.strftime('%Y-%m-%d')
            match_time = match_datetime.strftime('%H:%M')
        else:
            match_date = ''
            match_time = '15:00'

        # Get country from league name
        country = self._get_country_from_league(league_name)

        return {
            'country': country,
            'league': league_name,
            'date': match_date,
            'time': match_time,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'outcome': outcome,
            'over_2_5': over_2_5,
            'btts': btts,
            'home_corners': home_corners,
            'away_corners': away_corners,
            'total_corners': total_corners,
            'over_9_5_corners': over_9_5_corners,
            'odds': {
                'home_odds': home_odds,
                'draw_odds': draw_odds,
                'away_odds': away_odds,
                'over_2_5_odds': float(match_data.get('odds_ft_over25', 0)) or 1.9,
                'under_2_5_odds': float(match_data.get('odds_ft_under25', 0)) or 1.9,
                'btts_yes_odds': btts_yes_odds,
                'btts_no_odds': btts_no_odds,
                'corners_over_9_5_odds': corners_over_9_5_odds,
                'corners_under_9_5_odds': corners_under_9_5_odds,
            }
        }

    def _get_country_from_league(self, league_name: str) -> str:
        """Get country from league name"""
        country_map = {
            'Premier League': 'England',
            'La Liga': 'Spain',
            'Serie A': 'Italy',
            'Bundesliga': 'Germany',
            'Ligue 1': 'France',
            'Brazil Serie A': 'Brazil',
        }
        return country_map.get(league_name, 'Unknown')


def test_api():
    """Test FootyStats API connection"""
    api_key = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    api = FootyStatsAPI(api_key)

    # Test with date in 2024/2025 season
    test_date = "2024-09-01"  # September 1, 2024 - early in season
    print(f"\n🧪 Testing FootyStats API with date: {test_date}")

    matches = api.get_matches_by_date(test_date)

    if matches:
        print(f"\n✅ SUCCESS! Found {len(matches)} matches")
        print("\nSample match:")
        match = matches[0]
        print(f"  {match['home_team']} vs {match['away_team']}")
        print(f"  Score: {match['home_score']}-{match['away_score']}")
        print(f"  Outcome: {match['outcome']}")
        print(f"  Odds: {match['odds']['home_odds']:.2f} / {match['odds']['draw_odds']:.2f} / {match['odds']['away_odds']:.2f}")
    else:
        print("\n⚠️  No matches found")

    return matches


if __name__ == '__main__':
    test_api()
