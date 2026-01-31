#!/usr/bin/env python3
"""
Soccer Betting Angle Investigation

Comprehensive analysis of 1-2 years of historical data to find profitable betting angles.
Tests: Moneylines, Over/Under, BTTS, First Half, Corners
"""

import requests
import time
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict

# API Configuration
API_SPORTS_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_SPORTS_URL = "https://v3.football.api-sports.io"

# Leagues to analyze (API-Sports IDs)
LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    88: "Eredivisie",
    94: "Primeira Liga",
    203: "Super Lig",
    71: "Brazil Serie A",
    253: "MLS",
}

# Data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "soccer_historical.db"


class SoccerDataCollector:
    """Collects historical soccer data from API-Sports"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "x-apisports-key": API_SPORTS_KEY
        })
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                fixture_id INTEGER PRIMARY KEY,
                league_id INTEGER,
                league_name TEXT,
                date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_score INTEGER,
                away_score INTEGER,
                ht_home INTEGER,
                ht_away INTEGER,
                home_corners INTEGER,
                away_corners INTEGER,
                outcome TEXT,
                btts INTEGER,
                over_1_5 INTEGER,
                over_2_5 INTEGER,
                over_3_5 INTEGER,
                ht_over_0_5 INTEGER,
                ht_over_1_5 INTEGER,
                corners_over_9_5 INTEGER,
                corners_over_10_5 INTEGER,
                home_odds REAL,
                draw_odds REAL,
                away_odds REAL,
                over_2_5_odds REAL,
                btts_yes_odds REAL,
                collected_at TEXT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_date ON matches(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_league ON matches(league_id)")

        conn.commit()
        conn.close()

    def collect_fixtures(self, league_id: int, season: int) -> List[Dict]:
        """Collect fixtures for a league and season"""
        url = f"{API_SPORTS_URL}/fixtures"
        params = {
            "league": league_id,
            "season": season,
            "status": "FT"  # Full time (completed)
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            data = response.json()

            if data.get("errors"):
                print(f"  API Error: {data['errors']}")
                return []

            return data.get("response", [])
        except Exception as e:
            print(f"  Error: {e}")
            return []

    def collect_all_data(self, seasons: List[int] = [2023, 2024]):
        """Collect data for all leagues and seasons"""
        print("=" * 70)
        print("COLLECTING HISTORICAL SOCCER DATA")
        print("=" * 70)

        all_matches = []

        for season in seasons:
            print(f"\n--- Season {season}/{season+1} ---")

            for league_id, league_name in LEAGUES.items():
                print(f"  Fetching {league_name}...", end=" ")

                fixtures = self.collect_fixtures(league_id, season)

                if fixtures:
                    matches = self._process_fixtures(fixtures, league_id, league_name)
                    all_matches.extend(matches)
                    print(f"{len(matches)} matches")
                else:
                    print("No data")

                time.sleep(1)  # Rate limiting

        # Save to database
        self._save_to_db(all_matches)

        print(f"\n✅ Total matches collected: {len(all_matches)}")
        return all_matches

    def _process_fixtures(self, fixtures: List[Dict], league_id: int, league_name: str) -> List[Dict]:
        """Process fixtures into standardized format"""
        matches = []

        for f in fixtures:
            try:
                fixture = f.get("fixture", {})
                teams = f.get("teams", {})
                goals = f.get("goals", {})
                score = f.get("score", {})

                home_score = goals.get("home", 0) or 0
                away_score = goals.get("away", 0) or 0

                # Halftime
                ht = score.get("halftime", {})
                ht_home = ht.get("home", 0) or 0
                ht_away = ht.get("away", 0) or 0

                # Statistics (corners) - need separate API call
                # For now, set to None
                home_corners = None
                away_corners = None

                # Calculate outcomes
                if home_score > away_score:
                    outcome = "home"
                elif away_score > home_score:
                    outcome = "away"
                else:
                    outcome = "draw"

                total_goals = home_score + away_score
                ht_total = ht_home + ht_away

                match = {
                    "fixture_id": fixture.get("id"),
                    "league_id": league_id,
                    "league_name": league_name,
                    "date": fixture.get("date", "")[:10],
                    "home_team": teams.get("home", {}).get("name", ""),
                    "away_team": teams.get("away", {}).get("name", ""),
                    "home_score": home_score,
                    "away_score": away_score,
                    "ht_home": ht_home,
                    "ht_away": ht_away,
                    "home_corners": home_corners,
                    "away_corners": away_corners,
                    "outcome": outcome,
                    "btts": 1 if (home_score > 0 and away_score > 0) else 0,
                    "over_1_5": 1 if total_goals > 1.5 else 0,
                    "over_2_5": 1 if total_goals > 2.5 else 0,
                    "over_3_5": 1 if total_goals > 3.5 else 0,
                    "ht_over_0_5": 1 if ht_total > 0.5 else 0,
                    "ht_over_1_5": 1 if ht_total > 1.5 else 0,
                    "corners_over_9_5": None,
                    "corners_over_10_5": None,
                    "home_odds": None,  # Would need odds API
                    "draw_odds": None,
                    "away_odds": None,
                    "over_2_5_odds": None,
                    "btts_yes_odds": None,
                    "collected_at": datetime.now().isoformat()
                }

                matches.append(match)

            except Exception as e:
                continue

        return matches

    def _save_to_db(self, matches: List[Dict]):
        """Save matches to SQLite database"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for m in matches:
            cursor.execute("""
                INSERT OR REPLACE INTO matches VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?
                )
            """, (
                m["fixture_id"], m["league_id"], m["league_name"], m["date"],
                m["home_team"], m["away_team"], m["home_score"], m["away_score"],
                m["ht_home"], m["ht_away"], m["home_corners"], m["away_corners"],
                m["outcome"], m["btts"], m["over_1_5"], m["over_2_5"], m["over_3_5"],
                m["ht_over_0_5"], m["ht_over_1_5"], m["corners_over_9_5"], m["corners_over_10_5"],
                m["home_odds"], m["draw_odds"], m["away_odds"], m["over_2_5_odds"],
                m["btts_yes_odds"], m["collected_at"]
            ))

        conn.commit()
        conn.close()


class SoccerAngleAnalyzer:
    """Analyzes soccer betting angles from historical data"""

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.df = None

    def load_data(self) -> pd.DataFrame:
        """Load data from database"""
        self.df = pd.read_sql_query("SELECT * FROM matches ORDER BY date", self.conn)
        print(f"Loaded {len(self.df)} matches")
        return self.df

    def analyze_all_angles(self):
        """Comprehensive analysis of all betting angles"""
        if self.df is None:
            self.load_data()

        print("\n" + "=" * 70)
        print("SOCCER BETTING ANGLE ANALYSIS")
        print("=" * 70)
        print(f"Total matches: {len(self.df)}")
        print(f"Date range: {self.df['date'].min()} to {self.df['date'].max()}")
        print(f"Leagues: {self.df['league_name'].nunique()}")

        results = {}

        # 1. Over/Under Analysis
        print("\n" + "-" * 70)
        print("1. OVER/UNDER TOTALS ANALYSIS")
        print("-" * 70)
        results['totals'] = self._analyze_totals()

        # 2. BTTS Analysis
        print("\n" + "-" * 70)
        print("2. BOTH TEAMS TO SCORE (BTTS) ANALYSIS")
        print("-" * 70)
        results['btts'] = self._analyze_btts()

        # 3. First Half Analysis
        print("\n" + "-" * 70)
        print("3. FIRST HALF TOTALS ANALYSIS")
        print("-" * 70)
        results['first_half'] = self._analyze_first_half()

        # 4. Moneyline/Match Outcome
        print("\n" + "-" * 70)
        print("4. MATCH OUTCOME ANALYSIS")
        print("-" * 70)
        results['outcome'] = self._analyze_outcomes()

        # 5. League-Specific Analysis
        print("\n" + "-" * 70)
        print("5. LEAGUE-SPECIFIC PROFITABLE ANGLES")
        print("-" * 70)
        results['league_angles'] = self._analyze_by_league()

        return results

    def _analyze_totals(self) -> Dict:
        """Analyze Over/Under totals"""
        results = {}

        for col, line in [("over_1_5", 1.5), ("over_2_5", 2.5), ("over_3_5", 3.5)]:
            hit_rate = self.df[col].mean()
            implied_prob = 1 / 1.9  # Typical odds
            edge = hit_rate - implied_prob

            # Estimate ROI at typical odds
            roi = (hit_rate * 1.9 - 1) * 100

            print(f"\nOver {line} Goals:")
            print(f"  Hit Rate: {hit_rate*100:.1f}%")
            print(f"  Implied (1.90 odds): {implied_prob*100:.1f}%")
            print(f"  Edge: {edge*100:+.1f}%")
            print(f"  Est. ROI: {roi:+.1f}%")

            results[f"over_{line}"] = {
                "hit_rate": hit_rate,
                "edge": edge,
                "roi": roi
            }

        return results

    def _analyze_btts(self) -> Dict:
        """Analyze Both Teams To Score"""
        btts_rate = self.df['btts'].mean()
        implied_prob = 1 / 1.85
        edge = btts_rate - implied_prob
        roi = (btts_rate * 1.85 - 1) * 100

        print(f"\nBTTS Yes:")
        print(f"  Hit Rate: {btts_rate*100:.1f}%")
        print(f"  Implied (1.85 odds): {implied_prob*100:.1f}%")
        print(f"  Edge: {edge*100:+.1f}%")
        print(f"  Est. ROI: {roi:+.1f}%")

        # BTTS No
        btts_no_rate = 1 - btts_rate
        edge_no = btts_no_rate - implied_prob
        roi_no = (btts_no_rate * 1.85 - 1) * 100

        print(f"\nBTTS No:")
        print(f"  Hit Rate: {btts_no_rate*100:.1f}%")
        print(f"  Edge: {edge_no*100:+.1f}%")
        print(f"  Est. ROI: {roi_no:+.1f}%")

        return {
            "btts_yes": {"hit_rate": btts_rate, "edge": edge, "roi": roi},
            "btts_no": {"hit_rate": btts_no_rate, "edge": edge_no, "roi": roi_no}
        }

    def _analyze_first_half(self) -> Dict:
        """Analyze First Half totals"""
        results = {}

        for col, line in [("ht_over_0_5", 0.5), ("ht_over_1_5", 1.5)]:
            hit_rate = self.df[col].mean()

            # Typical odds for HT markets
            if line == 0.5:
                typical_odds = 1.45
            else:
                typical_odds = 2.10

            implied_prob = 1 / typical_odds
            edge = hit_rate - implied_prob
            roi = (hit_rate * typical_odds - 1) * 100

            print(f"\n1H Over {line} Goals:")
            print(f"  Hit Rate: {hit_rate*100:.1f}%")
            print(f"  Implied ({typical_odds} odds): {implied_prob*100:.1f}%")
            print(f"  Edge: {edge*100:+.1f}%")
            print(f"  Est. ROI: {roi:+.1f}%")

            results[f"ht_over_{line}"] = {
                "hit_rate": hit_rate,
                "edge": edge,
                "roi": roi
            }

        return results

    def _analyze_outcomes(self) -> Dict:
        """Analyze match outcomes"""
        outcomes = self.df['outcome'].value_counts(normalize=True)

        print("\nMatch Outcome Distribution:")
        for outcome, rate in outcomes.items():
            print(f"  {outcome.capitalize()}: {rate*100:.1f}%")

        # Home win analysis
        home_rate = outcomes.get('home', 0)
        typical_home_odds = 2.0
        home_edge = home_rate - (1/typical_home_odds)
        home_roi = (home_rate * typical_home_odds - 1) * 100

        print(f"\nHome Win at 2.0 odds:")
        print(f"  Edge: {home_edge*100:+.1f}%")
        print(f"  Est. ROI: {home_roi:+.1f}%")

        # Away win analysis
        away_rate = outcomes.get('away', 0)
        typical_away_odds = 3.5
        away_edge = away_rate - (1/typical_away_odds)
        away_roi = (away_rate * typical_away_odds - 1) * 100

        print(f"\nAway Win at 3.5 odds:")
        print(f"  Edge: {away_edge*100:+.1f}%")
        print(f"  Est. ROI: {away_roi:+.1f}%")

        return {
            "home": {"rate": home_rate, "edge": home_edge, "roi": home_roi},
            "draw": {"rate": outcomes.get('draw', 0)},
            "away": {"rate": away_rate, "edge": away_edge, "roi": away_roi}
        }

    def _analyze_by_league(self) -> Dict:
        """Find profitable angles by league"""
        results = []

        print("\nProfitable League-Specific Angles (ROI > 5%):\n")

        for league in self.df['league_name'].unique():
            league_df = self.df[self.df['league_name'] == league]

            if len(league_df) < 50:  # Minimum sample
                continue

            # Check each angle
            angles = [
                ("Over 2.5", "over_2_5", 1.90),
                ("Over 3.5", "over_3_5", 2.50),
                ("BTTS Yes", "btts", 1.85),
                ("HT Over 0.5", "ht_over_0_5", 1.45),
                ("HT Over 1.5", "ht_over_1_5", 2.10),
            ]

            for angle_name, col, odds in angles:
                hit_rate = league_df[col].mean()
                roi = (hit_rate * odds - 1) * 100

                if roi > 5:  # Only show profitable
                    print(f"  {league} - {angle_name}:")
                    print(f"    Matches: {len(league_df)}, Hit Rate: {hit_rate*100:.1f}%, ROI: {roi:+.1f}%")

                    results.append({
                        "league": league,
                        "angle": angle_name,
                        "matches": len(league_df),
                        "hit_rate": hit_rate,
                        "roi": roi
                    })

        # Sort by ROI
        results.sort(key=lambda x: x['roi'], reverse=True)

        return results

    def generate_recommendations(self, results: Dict):
        """Generate actionable recommendations"""
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS")
        print("=" * 70)

        profitable = []

        # Check league-specific angles
        for angle in results.get('league_angles', []):
            if angle['roi'] > 5 and angle['matches'] >= 100:
                profitable.append(angle)

        if profitable:
            print("\n✅ RECOMMENDED BETTING ANGLES (ROI > 5%, 100+ sample):\n")
            for i, angle in enumerate(profitable[:10], 1):
                print(f"  {i}. {angle['league']} - {angle['angle']}")
                print(f"     ROI: {angle['roi']:+.1f}%, Hit Rate: {angle['hit_rate']*100:.1f}%, Sample: {angle['matches']}")
        else:
            print("\n⚠️  No angles with ROI > 5% and 100+ sample size found")
            print("   This suggests the market is efficient and edges are small")

        # Global angles
        print("\n📊 GLOBAL MARKET ANALYSIS:\n")

        totals = results.get('totals', {})
        for line, data in totals.items():
            status = "✅" if data['roi'] > 0 else "❌"
            print(f"  {status} {line.replace('_', ' ').title()}: ROI {data['roi']:+.1f}%")

        btts = results.get('btts', {})
        for market, data in btts.items():
            status = "✅" if data['roi'] > 0 else "❌"
            print(f"  {status} {market.replace('_', ' ').upper()}: ROI {data['roi']:+.1f}%")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("SOCCER BETTING ANGLE INVESTIGATION")
    print("=" * 70)

    # Check if data exists
    if not DB_PATH.exists() or DB_PATH.stat().st_size < 1000:
        print("\n📥 Collecting historical data (this may take a few minutes)...")
        collector = SoccerDataCollector()
        collector.collect_all_data(seasons=[2023, 2024])
    else:
        print(f"\n✅ Using existing data from {DB_PATH}")

    # Analyze angles
    analyzer = SoccerAngleAnalyzer()
    results = analyzer.analyze_all_angles()

    # Generate recommendations
    analyzer.generate_recommendations(results)

    print("\n" + "=" * 70)
    print("INVESTIGATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
