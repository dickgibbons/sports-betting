#!/usr/bin/env python3
"""
NHL Game Data Cache

SQLite-based caching layer for NHL game data to dramatically improve performance.
- First run: Fetches all games and caches them (~28 minutes)
- Subsequent runs: Only fetches new games (~30 seconds)

Database size: ~2-5 MB for a full season
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

# Default database location
DEFAULT_DB_PATH = "/Users/dickgibbons/AI Projects/sports-betting/data/nhl_game_cache.db"


class NHLGameCache:
    """SQLite cache for NHL game data"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self.nhl_api_base = "https://api-web.nhle.com/v1"

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main games table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                game_id INTEGER PRIMARY KEY,
                game_date TEXT NOT NULL,
                season TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                period_1_home INTEGER DEFAULT 0,
                period_1_away INTEGER DEFAULT 0,
                period_2_home INTEGER DEFAULT 0,
                period_2_away INTEGER DEFAULT 0,
                period_3_home INTEGER DEFAULT 0,
                period_3_away INTEGER DEFAULT 0,
                ot_home INTEGER DEFAULT 0,
                ot_away INTEGER DEFAULT 0,
                home_shots INTEGER DEFAULT 0,
                away_shots INTEGER DEFAULT 0,
                venue TEXT,
                game_state TEXT,
                landing_data TEXT,
                fetched_at TEXT,
                UNIQUE(game_id)
            )
        """)

        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_team_date
            ON games(home_team, away_team, game_date)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_season
            ON games(season, game_date)
        """)

        # Cache metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_meta (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)

        conn.commit()
        conn.close()

    def get_cached_game(self, game_id: int) -> Optional[Dict]:
        """Get a single game from cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM games WHERE game_id = ?", (game_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return self._row_to_dict(row, cursor.description)
        return None

    def get_team_games(self, team_abbrev: str, season: str = "20252026") -> List[Dict]:
        """Get all cached games for a team in a season"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM games
            WHERE (home_team = ? OR away_team = ?)
            AND season = ?
            AND game_state = 'OFF'
            ORDER BY game_date ASC
        """, (team_abbrev, team_abbrev, season))

        rows = cursor.fetchall()
        description = cursor.description
        conn.close()

        return [self._row_to_dict(row, description) for row in rows]

    def _row_to_dict(self, row, description) -> Dict:
        """Convert a database row to a dictionary"""
        return {description[i][0]: row[i] for i in range(len(row))}

    def cache_game(self, game_data: Dict, landing_data: Dict = None):
        """Cache a single game with its landing data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        game_id = game_data.get("id")
        game_date = game_data.get("gameDate", "")
        season = game_data.get("season", self._get_season_from_date(game_date))

        home_team = game_data.get("homeTeam", {}).get("abbrev", "")
        away_team = game_data.get("awayTeam", {}).get("abbrev", "")
        home_score = game_data.get("homeTeam", {}).get("score", 0)
        away_score = game_data.get("awayTeam", {}).get("score", 0)
        venue = game_data.get("venue", {}).get("default", "")
        game_state = game_data.get("gameState", "")

        # Extract period scores from landing data
        period_scores = self._extract_period_scores(landing_data, home_team, away_team)

        # Extract shots
        home_shots = 0
        away_shots = 0
        if landing_data:
            home_shots = landing_data.get("homeTeam", {}).get("sog", 0) or 0
            away_shots = landing_data.get("awayTeam", {}).get("sog", 0) or 0

        cursor.execute("""
            INSERT OR REPLACE INTO games (
                game_id, game_date, season, home_team, away_team,
                home_score, away_score,
                period_1_home, period_1_away,
                period_2_home, period_2_away,
                period_3_home, period_3_away,
                ot_home, ot_away,
                home_shots, away_shots,
                venue, game_state, landing_data, fetched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            game_id, game_date, season, home_team, away_team,
            home_score, away_score,
            period_scores.get("p1_home", 0), period_scores.get("p1_away", 0),
            period_scores.get("p2_home", 0), period_scores.get("p2_away", 0),
            period_scores.get("p3_home", 0), period_scores.get("p3_away", 0),
            period_scores.get("ot_home", 0), period_scores.get("ot_away", 0),
            home_shots, away_shots,
            venue, game_state,
            json.dumps(landing_data) if landing_data else None,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

    def _extract_period_scores(self, landing_data: Dict, home_team: str, away_team: str) -> Dict:
        """Extract period-by-period scores from landing data"""
        scores = {
            "p1_home": 0, "p1_away": 0,
            "p2_home": 0, "p2_away": 0,
            "p3_home": 0, "p3_away": 0,
            "ot_home": 0, "ot_away": 0,
        }

        if not landing_data:
            return scores

        try:
            summary = landing_data.get("summary", {})
            scoring = summary.get("scoring", [])

            for period in scoring:
                period_num = period.get("periodDescriptor", {}).get("number", 0)
                period_type = period.get("periodDescriptor", {}).get("periodType", "")

                home_goals = 0
                away_goals = 0

                for goal in period.get("goals", []):
                    goal_team = goal.get("teamAbbrev", {}).get("default", "")
                    if goal_team == home_team:
                        home_goals += 1
                    elif goal_team == away_team:
                        away_goals += 1

                if period_num == 1:
                    scores["p1_home"] = home_goals
                    scores["p1_away"] = away_goals
                elif period_num == 2:
                    scores["p2_home"] = home_goals
                    scores["p2_away"] = away_goals
                elif period_num == 3:
                    scores["p3_home"] = home_goals
                    scores["p3_away"] = away_goals
                elif period_type == "OT" or period_num > 3:
                    scores["ot_home"] += home_goals
                    scores["ot_away"] += away_goals

        except Exception as e:
            pass

        return scores

    def _get_season_from_date(self, date_str: str) -> str:
        """Determine season from game date"""
        try:
            date = datetime.strptime(date_str[:10], "%Y-%m-%d")
            year = date.year
            month = date.month

            # NHL season starts in October
            if month >= 10:
                return f"{year}{year+1}"
            else:
                return f"{year-1}{year}"
        except:
            return "20242025"

    def get_cached_game_ids(self, season: str = "20252026") -> set:
        """Get all cached game IDs for a season"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT game_id FROM games WHERE season = ? AND game_state = 'OFF'",
            (season,)
        )

        ids = {row[0] for row in cursor.fetchall()}
        conn.close()

        return ids

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM games")
        total_games = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT home_team) FROM games")
        teams = cursor.fetchone()[0]

        cursor.execute("SELECT MIN(game_date), MAX(game_date) FROM games")
        date_range = cursor.fetchone()

        cursor.execute("SELECT season, COUNT(*) FROM games GROUP BY season")
        by_season = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        # Get file size
        file_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        return {
            "total_games": total_games,
            "teams": teams,
            "date_range": date_range,
            "by_season": by_season,
            "file_size_mb": file_size / (1024 * 1024),
            "db_path": self.db_path
        }

    def fetch_and_cache_team_season(self, team_abbrev: str, season: str = "20252026",
                                     force_refresh: bool = False) -> List[Dict]:
        """
        Fetch all games for a team, caching new ones.
        Returns all games from cache.
        """
        # Get existing cached game IDs
        cached_ids = self.get_cached_game_ids(season) if not force_refresh else set()

        # Fetch schedule from API
        url = f"{self.nhl_api_base}/club-schedule-season/{team_abbrev}/{season}"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Error fetching {team_abbrev}: {response.status_code}")
                return self.get_team_games(team_abbrev, season)

            data = response.json()
            games = data.get("games", [])

            # Filter to completed games
            completed = [g for g in games if g.get("gameState") == "OFF"]

            # Find games we need to fetch
            new_games = [g for g in completed if g.get("id") not in cached_ids]

            if new_games:
                print(f"   Fetching {len(new_games)} new games for {team_abbrev}...")

                for i, game in enumerate(new_games):
                    game_id = game.get("id")

                    # Fetch landing data for period scores
                    landing = self._fetch_landing(game_id)

                    # Cache the game
                    self.cache_game(game, landing)

                    if (i + 1) % 10 == 0:
                        print(f"      Cached {i + 1}/{len(new_games)} games...")
            else:
                print(f"   All {len(completed)} games already cached for {team_abbrev}")

        except Exception as e:
            print(f"Error fetching {team_abbrev}: {e}")

        # Return all games from cache
        return self.get_team_games(team_abbrev, season)

    def _fetch_landing(self, game_id: int) -> Optional[Dict]:
        """Fetch landing data for a game"""
        url = f"{self.nhl_api_base}/gamecenter/{game_id}/landing"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass

        return None

    def build_team_dataframe(self, team_abbrev: str, season: str = "20252026") -> 'pd.DataFrame':
        """
        Build a pandas DataFrame from cached data in the format expected by the MA analyzer.
        This is the main interface for the moving average scripts.
        """
        import pandas as pd

        # First ensure we have the latest data
        games = self.fetch_and_cache_team_season(team_abbrev, season)

        if not games:
            return pd.DataFrame()

        game_data = []

        for game in games:
            is_home = (game["home_team"] == team_abbrev)

            if is_home:
                goals_for = game["home_score"] or 0
                goals_against = game["away_score"] or 0
                opponent = game["away_team"]
                period_1_for = game["period_1_home"] or 0
                period_1_against = game["period_1_away"] or 0
                shots_for = game["home_shots"] or 0
                shots_against = game["away_shots"] or 0
            else:
                goals_for = game["away_score"] or 0
                goals_against = game["home_score"] or 0
                opponent = game["home_team"]
                period_1_for = game["period_1_away"] or 0
                period_1_against = game["period_1_home"] or 0
                shots_for = game["away_shots"] or 0
                shots_against = game["home_shots"] or 0

            game_data.append({
                "date": game["game_date"],
                "game_id": game["game_id"],
                "opponent": opponent,
                "is_home": is_home,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "total_goals": goals_for + goals_against,
                "period_1_for": period_1_for,
                "period_1_against": period_1_against,
                "period_1_total": period_1_for + period_1_against,
                "shots_for": shots_for,
                "shots_against": shots_against,
                "won": 1 if goals_for > goals_against else 0,
            })

        df = pd.DataFrame(game_data)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            df["game_num"] = range(1, len(df) + 1)

        return df


def print_cache_stats():
    """Print cache statistics"""
    cache = NHLGameCache()
    stats = cache.get_cache_stats()

    print("\n" + "=" * 50)
    print("NHL GAME CACHE STATISTICS")
    print("=" * 50)
    print(f"Database: {stats['db_path']}")
    print(f"File Size: {stats['file_size_mb']:.2f} MB")
    print(f"Total Games: {stats['total_games']}")
    print(f"Teams: {stats['teams']}")

    if stats['date_range'][0]:
        print(f"Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")

    print("\nGames by Season:")
    for season, count in stats.get('by_season', {}).items():
        print(f"  {season}: {count} games")

    print("=" * 50)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="NHL Game Cache Management")
    parser.add_argument("--stats", action="store_true", help="Show cache statistics")
    parser.add_argument("--team", type=str, help="Cache games for a specific team")
    parser.add_argument("--all", action="store_true", help="Cache games for all teams")
    parser.add_argument("--season", type=str, default="20242025", help="Season to cache")

    args = parser.parse_args()

    if args.stats:
        print_cache_stats()
    elif args.team:
        cache = NHLGameCache()
        print(f"Caching games for {args.team.upper()}...")
        games = cache.fetch_and_cache_team_season(args.team.upper(), args.season)
        print(f"Cached {len(games)} games")
        print_cache_stats()
    elif args.all:
        from nhl_goals_moving_average import NHLGoalsMovingAverage
        cache = NHLGameCache()

        teams = list(set(NHLGoalsMovingAverage.TEAM_ABBREVS.values()))
        print(f"Caching games for {len(teams)} teams...")

        for i, team in enumerate(sorted(teams)):
            print(f"[{i+1}/{len(teams)}] {team}")
            cache.fetch_and_cache_team_season(team, args.season)

        print_cache_stats()
    else:
        print_cache_stats()
