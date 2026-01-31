"""
Data Fetcher Module for Global Soccer Schedule Dashboard
Handles API calls to Football API and The Odds API with caching
"""

import requests
import time
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from league_config import (
    FOOTBALL_API_KEY, FOOTBALL_API_BASE_URL,
    ODDS_API_KEY, ODDS_API_BASE_URL,
    ALL_LEAGUES, LEAGUE_BY_ID, get_season_year
)

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), "data", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)


class ScheduleDataFetcher:
    """Fetches and caches soccer schedule data from multiple APIs"""

    def __init__(self):
        self.football_headers = {"x-apisports-key": FOOTBALL_API_KEY}
        self.request_delay = 0.5  # Delay between API calls (seconds)
        self.fixtures_cache = {}
        self.odds_cache = {}
        self.odds_cache_time = {}

    def fetch_fixtures_for_date(self, date: datetime, leagues: List[Dict] = None) -> List[Dict]:
        """
        Fetch all fixtures for a given date across specified leagues.
        Uses The Odds API as primary source (has current data).
        """
        if leagues is None:
            leagues = ALL_LEAGUES

        date_str = date.strftime("%Y-%m-%d")
        cache_key = f"fixtures_odds_{date_str}"

        # Check memory cache first
        if cache_key in self.fixtures_cache:
            return self._filter_fixtures_by_leagues(self.fixtures_cache[cache_key], leagues)

        # Check file cache
        cache_file = os.path.join(CACHE_DIR, f"fixtures_odds_{date_str}.json")
        if os.path.exists(cache_file):
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            # Use cached data if less than 30 min old
            if cache_age < timedelta(minutes=30):
                try:
                    with open(cache_file, "r") as f:
                        self.fixtures_cache[cache_key] = json.load(f)
                        return self._filter_fixtures_by_leagues(self.fixtures_cache[cache_key], leagues)
                except Exception as e:
                    print(f"Error reading cache: {e}")

        # Fetch from The Odds API (has current fixture data)
        all_fixtures = []

        # Get unique odds_keys from leagues
        odds_keys = set()
        for league in leagues:
            if league.get("odds_key"):
                odds_keys.add(league["odds_key"])

        for odds_key in odds_keys:
            try:
                fixtures = self._fetch_fixtures_from_odds_api(odds_key, date_str)
                all_fixtures.extend(fixtures)
                time.sleep(self.request_delay)
            except Exception as e:
                print(f"Error fetching fixtures for {odds_key}: {e}")

        # Cache the results
        self.fixtures_cache[cache_key] = all_fixtures
        try:
            with open(cache_file, "w") as f:
                json.dump(all_fixtures, f)
        except Exception as e:
            print(f"Error writing cache: {e}")

        return self._filter_fixtures_by_leagues(all_fixtures, leagues)

    def _fetch_fixtures_from_odds_api(self, odds_key: str, date_str: str) -> List[Dict]:
        """Fetch fixtures from The Odds API for a specific league"""
        url = f"{ODDS_API_BASE_URL}/sports/{odds_key}/odds/"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return self._parse_odds_api_fixtures(data, odds_key, date_str)
        except Exception as e:
            print(f"Odds API error for {odds_key}: {e}")

        return []

    def _parse_odds_api_fixtures(self, events: List[Dict], odds_key: str, target_date: str) -> List[Dict]:
        """Parse fixture data from The Odds API response"""
        parsed = []

        # Find the league info by odds_key
        league_info = None
        for league in ALL_LEAGUES:
            if league.get("odds_key") == odds_key:
                league_info = league
                break

        if not league_info:
            return []

        for event in events:
            try:
                commence_time = event.get("commence_time", "")
                event_date = commence_time[:10] if commence_time else ""

                # Filter by date
                if event_date != target_date:
                    continue

                # Parse timestamp
                try:
                    dt = datetime.fromisoformat(commence_time.replace("Z", "+00:00"))
                    timestamp = int(dt.timestamp())
                except:
                    timestamp = 0

                # Get odds from first bookmaker
                home_odds = None
                draw_odds = None
                away_odds = None
                bookmakers = event.get("bookmakers", [])
                if bookmakers:
                    markets = bookmakers[0].get("markets", [])
                    for market in markets:
                        if market.get("key") == "h2h":
                            for outcome in market.get("outcomes", []):
                                name = outcome.get("name", "")
                                price = outcome.get("price")
                                if name == event.get("home_team"):
                                    home_odds = price
                                elif name == event.get("away_team"):
                                    away_odds = price
                                elif name == "Draw":
                                    draw_odds = price

                parsed_fixture = {
                    "fixture_id": event.get("id"),
                    "date": commence_time,
                    "timestamp": timestamp,
                    "status": "NS",
                    "status_long": "Not Started",
                    "elapsed": None,
                    "league_id": league_info.get("id"),
                    "league_name": league_info.get("name", "Unknown"),
                    "league_country": league_info.get("country", "Unknown"),
                    "league_flag": league_info.get("flag", ""),
                    "league_tier": league_info.get("tier", ""),
                    "odds_key": odds_key,
                    "home_team": event.get("home_team", "Unknown"),
                    "home_team_id": None,
                    "home_logo": "",
                    "away_team": event.get("away_team", "Unknown"),
                    "away_team_id": None,
                    "away_logo": "",
                    "home_score": None,
                    "away_score": None,
                    "home_odds": home_odds,
                    "draw_odds": draw_odds,
                    "away_odds": away_odds,
                    "ht_home": None,
                    "ht_away": None,
                    "ft_home": None,
                    "ft_away": None,
                }
                parsed.append(parsed_fixture)
            except Exception as e:
                print(f"Error parsing event: {e}")

        return parsed

    def _fetch_fixtures_from_api(self, date_str: str, league_id: int, season: int) -> List[Dict]:
        """Fetch fixtures from Football API for a specific league and date"""
        url = f"{FOOTBALL_API_BASE_URL}/fixtures"
        params = {
            "date": date_str,
            "league": league_id,
            "season": season
        }

        try:
            response = requests.get(url, headers=self.football_headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("response"):
                    return self._parse_fixtures(data["response"], league_id)
        except Exception as e:
            print(f"API error for league {league_id}: {e}")

        return []

    def _parse_fixtures(self, fixtures_data: List[Dict], league_id: int) -> List[Dict]:
        """Parse fixture data from Football API response"""
        parsed = []
        league_info = LEAGUE_BY_ID.get(league_id, {})

        for fixture in fixtures_data:
            try:
                fixture_info = fixture.get("fixture", {})
                teams = fixture.get("teams", {})
                goals = fixture.get("goals", {})
                score = fixture.get("score", {})

                parsed_fixture = {
                    "fixture_id": fixture_info.get("id"),
                    "date": fixture_info.get("date"),
                    "timestamp": fixture_info.get("timestamp"),
                    "status": fixture_info.get("status", {}).get("short", "NS"),
                    "status_long": fixture_info.get("status", {}).get("long", "Not Started"),
                    "elapsed": fixture_info.get("status", {}).get("elapsed"),
                    "league_id": league_id,
                    "league_name": league_info.get("name", "Unknown"),
                    "league_country": league_info.get("country", "Unknown"),
                    "league_flag": league_info.get("flag", ""),
                    "league_tier": league_info.get("tier", ""),
                    "home_team": teams.get("home", {}).get("name", "Unknown"),
                    "home_team_id": teams.get("home", {}).get("id"),
                    "home_logo": teams.get("home", {}).get("logo", ""),
                    "away_team": teams.get("away", {}).get("name", "Unknown"),
                    "away_team_id": teams.get("away", {}).get("id"),
                    "away_logo": teams.get("away", {}).get("logo", ""),
                    "home_score": goals.get("home"),
                    "away_score": goals.get("away"),
                    "ht_home": score.get("halftime", {}).get("home"),
                    "ht_away": score.get("halftime", {}).get("away"),
                    "ft_home": score.get("fulltime", {}).get("home"),
                    "ft_away": score.get("fulltime", {}).get("away"),
                }
                parsed.append(parsed_fixture)
            except Exception as e:
                print(f"Error parsing fixture: {e}")

        return parsed

    def _filter_fixtures_by_leagues(self, fixtures: List[Dict], leagues: List[Dict]) -> List[Dict]:
        """Filter fixtures to only include specified leagues"""
        league_ids = {league["id"] for league in leagues}
        odds_keys = {league.get("odds_key") for league in leagues if league.get("odds_key")}
        return [f for f in fixtures if f.get("league_id") in league_ids or f.get("odds_key") in odds_keys]

    def fetch_odds_for_fixtures(self, fixtures: List[Dict]) -> Dict[str, Dict]:
        """
        Fetch betting odds from The Odds API for fixtures.
        Returns a dict mapping fixture identifiers to odds data.
        """
        odds_by_fixture = {}

        # Group fixtures by odds_key (league)
        fixtures_by_odds_key = {}
        for fixture in fixtures:
            league_info = LEAGUE_BY_ID.get(fixture.get("league_id"), {})
            odds_key = league_info.get("odds_key")
            if odds_key:
                if odds_key not in fixtures_by_odds_key:
                    fixtures_by_odds_key[odds_key] = []
                fixtures_by_odds_key[odds_key].append(fixture)

        # Fetch odds for each league
        for odds_key, league_fixtures in fixtures_by_odds_key.items():
            try:
                # Check cache (5-minute expiry for odds)
                cache_key = f"odds_{odds_key}"
                if cache_key in self.odds_cache:
                    cache_time = self.odds_cache_time.get(cache_key, datetime.min)
                    if datetime.now() - cache_time < timedelta(minutes=5):
                        league_odds = self.odds_cache[cache_key]
                    else:
                        league_odds = self._fetch_odds_from_api(odds_key)
                        self.odds_cache[cache_key] = league_odds
                        self.odds_cache_time[cache_key] = datetime.now()
                else:
                    league_odds = self._fetch_odds_from_api(odds_key)
                    self.odds_cache[cache_key] = league_odds
                    self.odds_cache_time[cache_key] = datetime.now()

                # Match odds to fixtures
                for fixture in league_fixtures:
                    matched_odds = self._match_odds_to_fixture(fixture, league_odds)
                    if matched_odds:
                        fixture_key = f"{fixture['home_team']}_vs_{fixture['away_team']}"
                        odds_by_fixture[fixture_key] = matched_odds

                time.sleep(self.request_delay)
            except Exception as e:
                print(f"Error fetching odds for {odds_key}: {e}")

        return odds_by_fixture

    def _fetch_odds_from_api(self, sport_key: str) -> List[Dict]:
        """Fetch odds from The Odds API for a specific sport/league"""
        url = f"{ODDS_API_BASE_URL}/sports/{sport_key}/odds/"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us,uk",
            "markets": "h2h,totals",
            "oddsFormat": "decimal"
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Odds API error for {sport_key}: {e}")

        return []

    def _match_odds_to_fixture(self, fixture: Dict, odds_data: List[Dict]) -> Optional[Dict]:
        """Match odds data to a fixture based on team names"""
        home_team = fixture.get("home_team", "").lower()
        away_team = fixture.get("away_team", "").lower()

        for odds_event in odds_data:
            event_home = odds_event.get("home_team", "").lower()
            event_away = odds_event.get("away_team", "").lower()

            # Fuzzy match team names
            if self._teams_match(home_team, event_home) and self._teams_match(away_team, event_away):
                return self._parse_odds(odds_event)

        return None

    def _teams_match(self, team1: str, team2: str) -> bool:
        """Check if two team names likely refer to the same team"""
        # Simple matching - can be enhanced with fuzzy matching
        team1_parts = set(team1.split())
        team2_parts = set(team2.split())

        # Check if any significant word matches
        common = team1_parts.intersection(team2_parts)
        if common:
            return True

        # Check if one contains the other
        if team1 in team2 or team2 in team1:
            return True

        return False

    def _parse_odds(self, odds_event: Dict) -> Dict:
        """Parse odds data from The Odds API response"""
        parsed = {
            "commence_time": odds_event.get("commence_time"),
            "bookmakers": []
        }

        for bookmaker in odds_event.get("bookmakers", [])[:5]:  # Limit to 5 bookmakers
            bm_data = {
                "name": bookmaker.get("title"),
                "markets": {}
            }

            for market in bookmaker.get("markets", []):
                market_key = market.get("key")
                outcomes = {}

                for outcome in market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price")
                    point = outcome.get("point")

                    if market_key == "h2h":
                        outcomes[name] = price
                    elif market_key == "totals":
                        outcomes[f"{name}_{point}"] = price

                bm_data["markets"][market_key] = outcomes

            parsed["bookmakers"].append(bm_data)

        return parsed

    def fetch_team_stats(self, team_id: int, league_id: int, season: int) -> Optional[Dict]:
        """Fetch team statistics from Football API"""
        cache_key = f"team_stats_{team_id}_{league_id}_{season}"
        cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")

        # Check file cache (team stats don't change frequently)
        if os.path.exists(cache_file):
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age < timedelta(days=1):
                try:
                    with open(cache_file, "r") as f:
                        return json.load(f)
                except Exception:
                    pass

        # Fetch from API
        url = f"{FOOTBALL_API_BASE_URL}/teams/statistics"
        params = {
            "team": team_id,
            "league": league_id,
            "season": season
        }

        try:
            response = requests.get(url, headers=self.football_headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("response"):
                    stats = self._parse_team_stats(data["response"])
                    # Cache the results
                    with open(cache_file, "w") as f:
                        json.dump(stats, f)
                    return stats
        except Exception as e:
            print(f"Error fetching team stats for {team_id}: {e}")

        return None

    def _parse_team_stats(self, stats_data: Dict) -> Dict:
        """Parse team statistics from Football API response"""
        goals = stats_data.get("goals", {})
        fixtures = stats_data.get("fixtures", {})

        played = fixtures.get("played", {})
        total_played = (played.get("home", 0) or 0) + (played.get("away", 0) or 0)

        goals_for = goals.get("for", {}).get("total", {})
        goals_against = goals.get("against", {}).get("total", {})

        total_for = (goals_for.get("home", 0) or 0) + (goals_for.get("away", 0) or 0)
        total_against = (goals_against.get("home", 0) or 0) + (goals_against.get("away", 0) or 0)

        return {
            "games_played": total_played,
            "goals_for": total_for,
            "goals_against": total_against,
            "avg_goals_for": round(total_for / total_played, 2) if total_played > 0 else 0,
            "avg_goals_against": round(total_against / total_played, 2) if total_played > 0 else 0,
            "avg_total_goals": round((total_for + total_against) / total_played, 2) if total_played > 0 else 0,
            "clean_sheets": stats_data.get("clean_sheet", {}).get("total", 0) or 0,
            "failed_to_score": stats_data.get("failed_to_score", {}).get("total", 0) or 0,
        }

    def get_fixtures_dataframe(self, date: datetime, leagues: List[Dict] = None) -> pd.DataFrame:
        """Get fixtures as a pandas DataFrame with all data"""
        fixtures = self.fetch_fixtures_for_date(date, leagues)

        if not fixtures:
            return pd.DataFrame()

        df = pd.DataFrame(fixtures)

        # Sort by league tier, then by time
        tier_order = {
            "tier_1_major": 1,
            "tier_2_europe": 2,
            "tier_3_americas": 3,
            "tier_4_asia": 4,
            "tier_5_cups": 5
        }
        df["tier_sort"] = df["league_tier"].map(tier_order).fillna(99)
        df = df.sort_values(["tier_sort", "league_name", "timestamp"])

        return df


# Singleton instance for reuse
_fetcher_instance = None

def get_fetcher() -> ScheduleDataFetcher:
    """Get or create the singleton fetcher instance"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = ScheduleDataFetcher()
    return _fetcher_instance
