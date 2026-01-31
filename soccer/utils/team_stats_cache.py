#!/usr/bin/env python3
"""
Team Statistics Cache
Caches team form and season statistics to minimize API calls
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List

class TeamStatsCache:
    """Cache team statistics with SQLite backend"""

    def __init__(self, db_path: str = None):
        """Initialize cache with SQLite database"""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), 'data', 'team_stats_cache.db')

        self.db_path = db_path

        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for team form (last N games)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_form (
                team_id INTEGER,
                league_id INTEGER,
                season INTEGER,
                last_updated TEXT,
                form_data TEXT,
                PRIMARY KEY (team_id, league_id, season)
            )
        """)

        # Table for team season statistics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_season_stats (
                team_id INTEGER,
                league_id INTEGER,
                season INTEGER,
                last_updated TEXT,
                stats_data TEXT,
                PRIMARY KEY (team_id, league_id, season)
            )
        """)

        # Table for head-to-head history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS h2h_history (
                team_a_id INTEGER,
                team_b_id INTEGER,
                last_updated TEXT,
                h2h_data TEXT,
                PRIMARY KEY (team_a_id, team_b_id)
            )
        """)

        conn.commit()
        conn.close()

    def get_team_form(self, team_id: int, league_id: int, season: int,
                     max_age_hours: int = 24) -> Optional[Dict]:
        """
        Get cached team form data

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
            max_age_hours: Maximum age of cached data in hours

        Returns:
            Form data dict or None if not cached or expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT form_data, last_updated
            FROM team_form
            WHERE team_id = ? AND league_id = ? AND season = ?
        """, (team_id, league_id, season))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return None

        form_data, last_updated = result

        # Check if cache is expired
        last_updated_dt = datetime.fromisoformat(last_updated)
        age = datetime.now() - last_updated_dt

        if age > timedelta(hours=max_age_hours):
            return None  # Cache expired

        return json.loads(form_data)

    def set_team_form(self, team_id: int, league_id: int, season: int,
                     form_data: Dict):
        """
        Cache team form data

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
            form_data: Dictionary of form statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO team_form
            (team_id, league_id, season, last_updated, form_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            team_id,
            league_id,
            season,
            datetime.now().isoformat(),
            json.dumps(form_data)
        ))

        conn.commit()
        conn.close()

    def get_team_season_stats(self, team_id: int, league_id: int, season: int,
                             max_age_hours: int = 24) -> Optional[Dict]:
        """
        Get cached team season statistics

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
            max_age_hours: Maximum age of cached data in hours

        Returns:
            Season stats dict or None if not cached or expired
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT stats_data, last_updated
            FROM team_season_stats
            WHERE team_id = ? AND league_id = ? AND season = ?
        """, (team_id, league_id, season))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return None

        stats_data, last_updated = result

        # Check if cache is expired
        last_updated_dt = datetime.fromisoformat(last_updated)
        age = datetime.now() - last_updated_dt

        if age > timedelta(hours=max_age_hours):
            return None  # Cache expired

        return json.loads(stats_data)

    def set_team_season_stats(self, team_id: int, league_id: int, season: int,
                             stats_data: Dict):
        """
        Cache team season statistics

        Args:
            team_id: Team ID
            league_id: League ID
            season: Season year
            stats_data: Dictionary of season statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO team_season_stats
            (team_id, league_id, season, last_updated, stats_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            team_id,
            league_id,
            season,
            datetime.now().isoformat(),
            json.dumps(stats_data)
        ))

        conn.commit()
        conn.close()

    def get_h2h_history(self, team_a_id: int, team_b_id: int,
                       max_age_hours: int = 168) -> Optional[Dict]:
        """
        Get cached head-to-head history

        Args:
            team_a_id: First team ID
            team_b_id: Second team ID
            max_age_hours: Maximum age of cached data in hours (default 1 week)

        Returns:
            H2H data dict or None if not cached or expired
        """
        # Normalize team order (smaller ID first)
        if team_a_id > team_b_id:
            team_a_id, team_b_id = team_b_id, team_a_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT h2h_data, last_updated
            FROM h2h_history
            WHERE team_a_id = ? AND team_b_id = ?
        """, (team_a_id, team_b_id))

        result = cursor.fetchone()
        conn.close()

        if result is None:
            return None

        h2h_data, last_updated = result

        # Check if cache is expired
        last_updated_dt = datetime.fromisoformat(last_updated)
        age = datetime.now() - last_updated_dt

        if age > timedelta(hours=max_age_hours):
            return None  # Cache expired

        return json.loads(h2h_data)

    def set_h2h_history(self, team_a_id: int, team_b_id: int, h2h_data: Dict):
        """
        Cache head-to-head history

        Args:
            team_a_id: First team ID
            team_b_id: Second team ID
            h2h_data: Dictionary of H2H statistics
        """
        # Normalize team order (smaller ID first)
        if team_a_id > team_b_id:
            team_a_id, team_b_id = team_b_id, team_a_id

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO h2h_history
            (team_a_id, team_b_id, last_updated, h2h_data)
            VALUES (?, ?, ?, ?)
        """, (
            team_a_id,
            team_b_id,
            datetime.now().isoformat(),
            json.dumps(h2h_data)
        ))

        conn.commit()
        conn.close()

    def clear_expired(self, max_age_days: int = 30):
        """
        Clear cache entries older than max_age_days

        Args:
            max_age_days: Maximum age in days before deletion
        """
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM team_form WHERE last_updated < ?", (cutoff_date,))
        cursor.execute("DELETE FROM team_season_stats WHERE last_updated < ?", (cutoff_date,))
        cursor.execute("DELETE FROM h2h_history WHERE last_updated < ?", (cutoff_date,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def get_cache_stats(self) -> Dict:
        """Get statistics about cache usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM team_form")
        form_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM team_season_stats")
        season_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM h2h_history")
        h2h_count = cursor.fetchone()[0]

        conn.close()

        return {
            'team_form_entries': form_count,
            'season_stats_entries': season_count,
            'h2h_entries': h2h_count,
            'total_entries': form_count + season_count + h2h_count
        }


if __name__ == "__main__":
    # Test the cache
    print("Testing TeamStatsCache...")

    cache = TeamStatsCache()

    # Test set/get team form
    test_form = {
        'wins_last_5': 3,
        'draws_last_5': 1,
        'losses_last_5': 1,
        'goals_for_last_5': 8,
        'goals_against_last_5': 4
    }

    cache.set_team_form(50, 39, 2024, test_form)
    retrieved = cache.get_team_form(50, 39, 2024)

    print(f"✅ Form cache test: {retrieved == test_form}")

    # Test set/get season stats
    test_stats = {
        'win_rate': 0.65,
        'goals_per_game': 2.1,
        'conceded_per_game': 0.8
    }

    cache.set_team_season_stats(50, 39, 2024, test_stats)
    retrieved = cache.get_team_season_stats(50, 39, 2024)

    print(f"✅ Season stats cache test: {retrieved == test_stats}")

    # Test cache stats
    stats = cache.get_cache_stats()
    print(f"📊 Cache stats: {stats}")

    print("\n✅ TeamStatsCache tests passed!")
