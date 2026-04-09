#!/usr/bin/env python3
"""
NHL 1P Bet Results Tracker

Tracks predictions vs actual results and generates cumulative performance reports.
Stores results in SQLite database for historical analysis.
Now includes odds fetching and selective bet picking (top 3-5 bets only).
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Add paths
sys.path.insert(0, "/Users/dickgibbons/AI Projects/sports-betting/nhl/models")
sys.path.insert(0, "/Users/dickgibbons/AI Projects/sports-betting/nhl/analyzers")

# Constants
ODDS_API_KEY = '518c226b561ad7586ec8c5dd1144e3fb'
MAX_BETS_PER_DAY = 3  # Reduced from 5 - fewer, higher quality picks

# IMPROVEMENT: Stricter filters based on tracking data analysis
# - 70%+ confidence: 0-2 record (0%)
# - 65-69%: 2-2 (50%) - our best tier
# - Below 65%: 2-4 (33%) - losing money
MIN_CONFIDENCE = 65.0  # Raised from no minimum
MAX_ODDS = -140  # Don't bet heavy favorites (worse than -140)


class BetResultsTracker:
    def __init__(self):
        self.db_path = Path("/Users/dickgibbons/AI Projects/sports-betting/nhl/tracking/bet_results.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Predictions table - with odds column
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                game_id TEXT,
                matchup TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                expected_goals REAL,
                odds INTEGER,
                odds_source TEXT,
                fatigue_notes TEXT,
                selected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, matchup, bet_type)
            )
        """)

        # Add odds column if not exists (migration)
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN odds INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN odds_source TEXT")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE predictions ADD COLUMN selected INTEGER DEFAULT 0")
        except:
            pass

        # Results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                game_id TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                period_1_home INTEGER,
                period_1_away INTEGER,
                period_1_total INTEGER,
                final_home INTEGER,
                final_away INTEGER,
                game_status TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, home_team, away_team)
            )
        """)

        # Bet outcomes table (joins predictions with results)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bet_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                date TEXT NOT NULL,
                matchup TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                confidence REAL,
                odds INTEGER,
                predicted_value REAL,
                actual_value REAL,
                won INTEGER,  -- 1 = won, 0 = lost, NULL = pending
                profit REAL,  -- Profit/loss based on odds
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id),
                UNIQUE(date, matchup, bet_type)
            )
        """)

        # Add profit column if not exists
        try:
            cursor.execute("ALTER TABLE bet_outcomes ADD COLUMN odds INTEGER")
        except:
            pass
        try:
            cursor.execute("ALTER TABLE bet_outcomes ADD COLUMN profit REAL")
        except:
            pass

        conn.commit()
        conn.close()

    def save_predictions(self, date_str: str, predictions: List[Dict]):
        """Save today's predictions to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for pred in predictions:
            try:
                # Ensure expected_goals is stored as a float, not bytes
                exp_goals = pred.get('expected_goals')
                if exp_goals is not None:
                    exp_goals = float(exp_goals)

                cursor.execute("""
                    INSERT OR REPLACE INTO predictions
                    (date, matchup, bet_type, confidence, expected_goals, odds, odds_source, fatigue_notes, selected)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date_str,
                    pred['matchup'],
                    pred['bet_type'],
                    float(pred['confidence']),
                    exp_goals,
                    pred.get('odds'),
                    pred.get('odds_source'),
                    pred.get('fatigue_notes', ''),
                    int(pred.get('selected', 0))
                ))
            except Exception as e:
                print(f"Error saving prediction: {e}")

        conn.commit()
        conn.close()

        selected_count = sum(1 for p in predictions if p.get('selected', 0) == 1)
        print(f"Saved {len(predictions)} predictions for {date_str} ({selected_count} selected as best bets)")

    def _get_1p_scores_from_pbp(self, game_id: int, home_team_id: int, away_team_id: int) -> Tuple[Optional[int], Optional[int]]:
        """Get 1st period scores from play-by-play data"""
        try:
            pbp_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/play-by-play"
            response = requests.get(pbp_url, timeout=10)
            if response.status_code != 200:
                return None, None

            data = response.json()
            plays = data.get("plays", [])

            home_goals = 0
            away_goals = 0

            for play in plays:
                if play.get("typeDescKey") == "goal":
                    period = play.get("periodDescriptor", {}).get("number", 0)
                    if period == 1:
                        team_id = play.get("details", {}).get("eventOwnerTeamId")
                        if team_id == home_team_id:
                            home_goals += 1
                        elif team_id == away_team_id:
                            away_goals += 1

            return home_goals, away_goals
        except Exception:
            return None, None

    def fetch_game_results(self, date_str: str) -> List[Dict]:
        """Fetch actual game results from NHL API"""
        results = []

        try:
            url = f"https://api-web.nhle.com/v1/score/{date_str}"
            response = requests.get(url, timeout=15)

            if response.status_code != 200:
                print(f"Could not fetch results for {date_str}")
                return []

            data = response.json()
            games = data.get("games", [])

            for game in games:
                home = game.get("homeTeam", {}).get("abbrev", "")
                away = game.get("awayTeam", {}).get("abbrev", "")
                home_id = game.get("homeTeam", {}).get("id")
                away_id = game.get("awayTeam", {}).get("id")
                status = game.get("gameState", "")
                game_id = game.get("id")

                # Get period scores
                period_1_home = None
                period_1_away = None

                if status in ["FINAL", "OFF"] and game_id:
                    # Get period-by-period scoring from play-by-play
                    home_score = game.get("homeTeam", {}).get("score", 0)
                    away_score = game.get("awayTeam", {}).get("score", 0)

                    # Use play-by-play to get accurate 1P scores
                    period_1_home, period_1_away = self._get_1p_scores_from_pbp(game_id, home_id, away_id)

                    results.append({
                        "date": date_str,
                        "game_id": str(game_id) if game_id else None,
                        "home_team": home,
                        "away_team": away,
                        "period_1_home": period_1_home,
                        "period_1_away": period_1_away,
                        "period_1_total": (period_1_home or 0) + (period_1_away or 0) if period_1_home is not None else None,
                        "final_home": home_score,
                        "final_away": away_score,
                        "game_status": status
                    })

        except Exception as e:
            print(f"Error fetching results: {e}")

        return results

    def save_results(self, results: List[Dict]):
        """Save game results to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for result in results:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO results
                    (date, game_id, home_team, away_team, period_1_home, period_1_away,
                     period_1_total, final_home, final_away, game_status, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result['date'],
                    result.get('game_id'),
                    result['home_team'],
                    result['away_team'],
                    result.get('period_1_home'),
                    result.get('period_1_away'),
                    result.get('period_1_total'),
                    result.get('final_home'),
                    result.get('final_away'),
                    result.get('game_status'),
                    datetime.now().isoformat()
                ))
            except Exception as e:
                print(f"Error saving result: {e}")

        conn.commit()
        conn.close()
        print(f"Saved {len(results)} game results")

    def evaluate_bets(self, date_str: str):
        """Evaluate predictions against actual results (only selected bets)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get selected predictions for date
        cursor.execute("""
            SELECT id, matchup, bet_type, confidence, expected_goals, odds
            FROM predictions WHERE date = ? AND selected = 1
        """, (date_str,))
        predictions = cursor.fetchall()

        # Get results for date
        cursor.execute("""
            SELECT home_team, away_team, period_1_home, period_1_away, period_1_total
            FROM results WHERE date = ? AND game_status IN ('FINAL', 'OFF')
        """, (date_str,))
        results = {f"{r[1]} @ {r[0]}": r for r in cursor.fetchall()}

        evaluated = 0
        for pred_id, matchup, bet_type, confidence, expected, odds in predictions:
            if matchup not in results:
                continue

            home_team, away_team, p1_home, p1_away, p1_total = results[matchup]

            if p1_home is None or p1_away is None:
                continue

            # Determine if bet won
            won = None
            actual_value = None

            if "Over 0.5 (1P)" in bet_type:
                # Team over 0.5 bet
                team = bet_type.replace(" Over 0.5 (1P)", "")
                if team == home_team:
                    actual_value = p1_home
                    won = 1 if p1_home >= 1 else 0
                elif team == away_team:
                    actual_value = p1_away
                    won = 1 if p1_away >= 1 else 0
            elif "1P Total Over 1.5" in bet_type:
                actual_value = p1_total
                won = 1 if p1_total >= 2 else 0

            # Calculate profit based on odds
            profit = None
            if won is not None and odds is not None:
                if won == 1:
                    # American odds profit calculation
                    if odds > 0:
                        profit = odds / 100  # e.g., +150 = 1.5 units profit
                    else:
                        profit = 100 / abs(odds)  # e.g., -150 = 0.67 units profit
                else:
                    profit = -1  # Lost 1 unit

            if won is not None:
                cursor.execute("""
                    INSERT OR REPLACE INTO bet_outcomes
                    (prediction_id, date, matchup, bet_type, confidence, odds, predicted_value, actual_value, won, profit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pred_id, date_str, matchup, bet_type, confidence, odds, expected, actual_value, won, profit))
                evaluated += 1

        conn.commit()
        conn.close()
        print(f"Evaluated {evaluated} bets for {date_str}")

    def get_cumulative_stats(self, days: int = None) -> Dict:
        """Get cumulative betting statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        where_clause = "WHERE won IS NOT NULL"
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            where_clause = f"WHERE date >= '{cutoff}' AND won IS NOT NULL"

        # Overall stats
        cursor.execute(f"""
            SELECT
                COUNT(*) as total_bets,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END) as losses,
                AVG(confidence) as avg_confidence,
                SUM(COALESCE(profit, 0)) as total_profit
            FROM bet_outcomes
            {where_clause}
        """)
        overall = cursor.fetchone()

        # Stats by bet type
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN bet_type LIKE '%Over 0.5 (1P)%' THEN 'Team Over 0.5 (1P)'
                    WHEN bet_type LIKE '%1P Total Over 1.5%' THEN '1P Total Over 1.5'
                    ELSE bet_type
                END as bet_category,
                COUNT(*) as total,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                AVG(confidence) as avg_conf,
                SUM(COALESCE(profit, 0)) as profit
            FROM bet_outcomes
            {where_clause}
            GROUP BY bet_category
        """)
        by_type = cursor.fetchall()

        # Stats by confidence tier
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN confidence >= 70 THEN '70%+'
                    WHEN confidence >= 60 THEN '60-69%'
                    WHEN confidence >= 55 THEN '55-59%'
                    ELSE '<55%'
                END as tier,
                COUNT(*) as total,
                SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                SUM(COALESCE(profit, 0)) as profit
            FROM bet_outcomes
            {where_clause}
            GROUP BY tier
            ORDER BY tier DESC
        """)
        by_tier = cursor.fetchall()

        # Recent results (last 7 days)
        cursor.execute("""
            SELECT date,
                   COUNT(*) as total,
                   SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END) as wins,
                   SUM(COALESCE(profit, 0)) as profit
            FROM bet_outcomes
            WHERE won IS NOT NULL
            GROUP BY date
            ORDER BY date DESC
            LIMIT 7
        """)
        recent = cursor.fetchall()

        conn.close()

        return {
            'overall': {
                'total': overall[0] or 0,
                'wins': overall[1] or 0,
                'losses': overall[2] or 0,
                'win_rate': (overall[1] / overall[0] * 100) if overall[0] else 0,
                'avg_confidence': overall[3] or 0,
                'total_profit': overall[4] or 0
            },
            'by_type': [
                {'type': t[0], 'total': t[1], 'wins': t[2],
                 'win_rate': (t[2] / t[1] * 100) if t[1] else 0, 'profit': t[4] or 0}
                for t in by_type
            ],
            'by_tier': [
                {'tier': t[0], 'total': t[1], 'wins': t[2],
                 'win_rate': (t[2] / t[1] * 100) if t[1] else 0, 'profit': t[3] or 0}
                for t in by_tier
            ],
            'recent': [
                {'date': r[0], 'total': r[1], 'wins': r[2],
                 'win_rate': (r[2] / r[1] * 100) if r[1] else 0, 'profit': r[3] or 0}
                for r in recent
            ]
        }

    def generate_report(self, date_str: str = None) -> str:
        """Generate cumulative results report"""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")
        stats = self.get_cumulative_stats()

        report = []
        report.append("=" * 80)
        report.append(f"NHL 1P BETTING RESULTS - Cumulative Report")
        report.append(f"Generated: {date_str}")
        report.append("=" * 80)
        report.append("")

        # Overall Performance
        report.append("OVERALL PERFORMANCE")
        report.append("-" * 40)
        o = stats['overall']
        report.append(f"  Total Bets Tracked: {o['total']}")
        report.append(f"  Wins: {o['wins']} | Losses: {o['losses']}")
        report.append(f"  Win Rate: {o['win_rate']:.1f}%")
        report.append(f"  Avg Confidence: {o['avg_confidence']:.1f}%")
        report.append(f"  Total Profit: {o['total_profit']:+.2f} units")
        report.append("")

        # Performance by Bet Type
        report.append("PERFORMANCE BY BET TYPE")
        report.append("-" * 40)
        for bt in stats['by_type']:
            report.append(f"  {bt['type']}: {bt['wins']}/{bt['total']} ({bt['win_rate']:.1f}%) | Profit: {bt['profit']:+.2f}u")
        report.append("")

        # Performance by Confidence Tier
        report.append("PERFORMANCE BY CONFIDENCE TIER")
        report.append("-" * 40)
        for tier in stats['by_tier']:
            report.append(f"  {tier['tier']}: {tier['wins']}/{tier['total']} ({tier['win_rate']:.1f}%) | Profit: {tier['profit']:+.2f}u")
        report.append("")

        # Recent Daily Results
        report.append("RECENT DAILY RESULTS")
        report.append("-" * 40)
        for day in stats['recent']:
            report.append(f"  {day['date']}: {day['wins']}/{day['total']} ({day['win_rate']:.1f}%) | {day['profit']:+.2f}u")
        report.append("")

        # Today's Selected Bets
        report.append("TODAY'S SELECTED BETS")
        report.append("-" * 40)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT matchup, bet_type, confidence, odds, expected_goals
            FROM predictions
            WHERE date = ? AND selected = 1
            ORDER BY confidence DESC
        """, (date_str,))
        today_bets = cursor.fetchall()
        conn.close()

        if today_bets:
            for matchup, bet_type, conf, odds, exp_goals in today_bets:
                odds_str = f"({odds:+d})" if odds else "(odds N/A)"
                # Handle exp_goals that might be bytes, None, or corrupted
                try:
                    if exp_goals is None:
                        exp_str = "N/A"
                    elif isinstance(exp_goals, bytes):
                        import struct
                        exp_str = f"{struct.unpack('d', exp_goals)[0]:.2f}"
                    else:
                        exp_str = f"{float(exp_goals):.2f}"
                except:
                    exp_str = "N/A"
                report.append(f"  {matchup}: {bet_type}")
                report.append(f"    Confidence: {conf:.1f}% | Odds: {odds_str} | Expected: {exp_str}")
        else:
            report.append("  No bets selected for today")
        report.append("")

        # Disclaimer
        report.append("=" * 80)
        report.append("Note: Results are tracked automatically from NHL API data.")
        report.append("Only selected bets (top 3-5 per day) are tracked for performance.")
        report.append("Past performance does not guarantee future results.")
        report.append("=" * 80)

        return "\n".join(report)

    def generate_cumulative_csv(self, date_str: str = None) -> str:
        """Generate CSV with all bet outcomes line by line"""
        import csv
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date, matchup, bet_type, confidence, odds, actual_value, won, profit
            FROM bet_outcomes
            ORDER BY date, matchup
        """)
        outcomes = cursor.fetchall()
        conn.close()

        output_dir = Path(f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date_str}")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = output_dir / "NHL_BET_RESULTS_CUMULATIVE.csv"

        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Matchup', 'Bet', 'Confidence', 'Odds', 'Actual', 'Result', 'Profit'])

            for row in outcomes:
                date, matchup, bet_type, confidence, odds, actual, won, profit = row
                result = "WIN" if won == 1 else "LOSS" if won == 0 else "PENDING"
                odds_str = f"{odds:+d}" if odds else "-150"
                profit_str = f"{profit:+.2f}" if profit else ""

                writer.writerow([
                    date,
                    matchup,
                    bet_type,
                    f"{confidence:.1f}%",
                    odds_str,
                    actual,
                    result,
                    profit_str
                ])

        return str(csv_file)

    def update_and_report(self, date_str: str = None) -> str:
        """Full update cycle: fetch results, evaluate, generate report"""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")

        # Also check yesterday's games (in case running early)
        yesterday = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")

        print(f"\nUpdating results for {yesterday} and {date_str}...")

        # Fetch and save results for yesterday and today
        for d in [yesterday, date_str]:
            results = self.fetch_game_results(d)
            if results:
                self.save_results(results)
                self.evaluate_bets(d)

        # Generate report
        report = self.generate_report(date_str)

        # Save report
        output_dir = Path(f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date_str}")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"NHL_BET_RESULTS_{date_str}.txt"

        with open(output_file, "w") as f:
            f.write(report)

        print(f"\nReport saved to: {output_file}")

        # Generate cumulative CSV
        csv_file = self.generate_cumulative_csv(date_str)
        print(f"Cumulative CSV saved to: {csv_file}")

        return report


def fetch_nhl_1p_odds() -> Dict[str, Dict]:
    """
    Fetch 1st period team totals odds from Action Network API
    Returns dict keyed by matchup with odds for each bet type

    Action Network provides firstperiod type odds with:
    - home_over: home team Over 0.5 odds
    - away_over: away team Over 0.5 odds
    - over: 1P Total Over 1.5 odds
    """
    odds_data = {}

    # NHL team abbreviation mapping
    TEAM_MAP = {
        'ducks': 'ANA', 'coyotes': 'ARI', 'bruins': 'BOS',
        'sabres': 'BUF', 'flames': 'CGY', 'hurricanes': 'CAR',
        'blackhawks': 'CHI', 'avalanche': 'COL', 'blue jackets': 'CBJ',
        'stars': 'DAL', 'red wings': 'DET', 'oilers': 'EDM',
        'panthers': 'FLA', 'kings': 'LAK', 'wild': 'MIN',
        'canadiens': 'MTL', 'predators': 'NSH', 'devils': 'NJD',
        'islanders': 'NYI', 'rangers': 'NYR', 'senators': 'OTT',
        'flyers': 'PHI', 'penguins': 'PIT', 'sharks': 'SJS',
        'kraken': 'SEA', 'blues': 'STL', 'lightning': 'TBL',
        'maple leafs': 'TOR', 'utah hockey club': 'UTA', 'canucks': 'VAN',
        'golden knights': 'VGK', 'capitals': 'WSH', 'jets': 'WPG',
        # Full names
        'anaheim ducks': 'ANA', 'arizona coyotes': 'ARI', 'boston bruins': 'BOS',
        'buffalo sabres': 'BUF', 'calgary flames': 'CGY', 'carolina hurricanes': 'CAR',
        'chicago blackhawks': 'CHI', 'colorado avalanche': 'COL', 'columbus blue jackets': 'CBJ',
        'dallas stars': 'DAL', 'detroit red wings': 'DET', 'edmonton oilers': 'EDM',
        'florida panthers': 'FLA', 'los angeles kings': 'LAK', 'minnesota wild': 'MIN',
        'montreal canadiens': 'MTL', 'nashville predators': 'NSH', 'new jersey devils': 'NJD',
        'new york islanders': 'NYI', 'new york rangers': 'NYR', 'ottawa senators': 'OTT',
        'philadelphia flyers': 'PHI', 'pittsburgh penguins': 'PIT', 'san jose sharks': 'SJS',
        'seattle kraken': 'SEA', 'st louis blues': 'STL', 'st. louis blues': 'STL',
        'tampa bay lightning': 'TBL', 'toronto maple leafs': 'TOR',
        'vancouver canucks': 'VAN', 'vegas golden knights': 'VGK', 'washington capitals': 'WSH',
        'winnipeg jets': 'WPG'
    }

    try:
        # Action Network API - has first period odds
        url = "https://api.actionnetwork.com/web/v1/scoreboard/nhl"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://www.actionnetwork.com/'
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"Action Network API returned status {response.status_code}")
            return odds_data

        data = response.json()
        games = data.get('games', [])

        for game in games:
            # Extract team info
            teams = game.get('teams', [])
            if len(teams) < 2:
                continue

            # Determine home/away using team IDs
            home_team_id = game.get('home_team_id')
            away_team_id = game.get('away_team_id')

            home_team = None
            away_team = None
            for team in teams:
                if team.get('id') == home_team_id:
                    home_team = team
                elif team.get('id') == away_team_id:
                    away_team = team

            if not home_team or not away_team:
                continue

            # Get abbreviations
            home_name = home_team.get('display_name', '').lower()
            away_name = away_team.get('display_name', '').lower()

            home_abbrev = TEAM_MAP.get(home_name)
            away_abbrev = TEAM_MAP.get(away_name)

            # Try shorter name if full name didn't match
            if not home_abbrev:
                for key, val in TEAM_MAP.items():
                    if key in home_name or home_name in key:
                        home_abbrev = val
                        break
            if not away_abbrev:
                for key, val in TEAM_MAP.items():
                    if key in away_name or away_name in key:
                        away_abbrev = val
                        break

            if not home_abbrev or not away_abbrev:
                continue

            matchup = f"{away_abbrev} @ {home_abbrev}"

            # Initialize odds structure
            odds_data[matchup] = {
                'home_over_0_5': None,
                'away_over_0_5': None,
                'total_over_1_5': None,
                'source': 'ActionNetwork'
            }

            # Parse odds array for first period odds
            odds_list = game.get('odds', [])
            for odd in odds_list:
                odd_type = odd.get('type', '')

                if odd_type == 'firstperiod':
                    # First period team totals
                    home_over = odd.get('home_over')  # Home team Over 0.5
                    away_over = odd.get('away_over')  # Away team Over 0.5
                    total_over = odd.get('over')      # 1P Total Over 1.5

                    if home_over is not None:
                        odds_data[matchup]['home_over_0_5'] = int(home_over)
                    if away_over is not None:
                        odds_data[matchup]['away_over_0_5'] = int(away_over)
                    if total_over is not None:
                        odds_data[matchup]['total_over_1_5'] = int(total_over)

                    # Found first period odds, can break
                    break

        # Count games with actual odds
        games_with_odds = sum(1 for m, o in odds_data.items()
                             if o.get('home_over_0_5') or o.get('away_over_0_5'))
        print(f"Fetched 1P odds for {games_with_odds}/{len(odds_data)} games from Action Network")

    except Exception as e:
        print(f"Error fetching odds from Action Network: {e}")
        import traceback
        traceback.print_exc()

    return odds_data


def calculate_ev(confidence: float, odds: int) -> Tuple[float, float]:
    """
    Calculate Expected Value and edge for a bet.
    Returns (ev_per_unit, edge_over_book)
    """
    if odds is None:
        return 0.0, 0.0

    # Calculate break-even probability from odds
    if odds < 0:
        break_even = abs(odds) / (abs(odds) + 100) * 100
        payout_on_win = 100 / abs(odds)
    else:
        break_even = 100 / (odds + 100) * 100
        payout_on_win = odds / 100

    # Calculate Expected Value
    win_prob = confidence / 100
    loss_prob = 1 - win_prob
    ev = (win_prob * payout_on_win) - (loss_prob * 1)

    # Edge over the book
    edge = confidence - break_even

    return ev, edge


def select_best_bets(all_predictions: List[Dict], max_bets: int = MAX_BETS_PER_DAY) -> List[Dict]:
    """
    Select the top bets based on:
    1. Expected Value (EV) - MUST be positive
    2. Confidence level (higher is better)
    3. Edge over the book's implied probability
    4. Prefer spread across different games

    IMPROVEMENTS based on tracking data (Dec 4-6):
    - MIN_CONFIDENCE = 65% (below this: 33% win rate)
    - MAX_ODDS = -140 (heavy favorites aren't hitting)
    - MAX_BETS_PER_DAY = 3 (quality over quantity)

    Returns selected predictions with 'selected' flag set
    """
    if not all_predictions:
        return []

    # IMPROVEMENT: Pre-filter predictions
    filtered = []
    for pred in all_predictions:
        confidence = pred['confidence']
        odds = pred.get('odds')

        # Filter 1: Minimum confidence threshold
        if confidence < MIN_CONFIDENCE:
            continue

        # Filter 2: Avoid heavy favorites (odds worse than MAX_ODDS)
        if odds is not None and odds < MAX_ODDS:
            continue

        filtered.append(pred)

    if not filtered:
        print(f"Warning: No bets meet criteria (conf >= {MIN_CONFIDENCE}%, odds >= {MAX_ODDS})")
        # Fall back to top 2 by confidence if nothing passes
        all_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        filtered = all_predictions[:2]

    # Score each prediction with EV consideration
    scored = []
    for pred in filtered:
        confidence = pred['confidence']
        odds = pred.get('odds')

        # Calculate EV and edge
        ev, edge = calculate_ev(confidence, odds)
        pred['ev'] = ev
        pred['edge'] = edge

        # Base score is confidence
        score = confidence

        if odds is not None:
            # BIG bonus for positive EV bets
            if ev > 0:
                score += 15 + (ev * 100)  # +15 base + EV percentage bonus

            # Penalty for negative EV bets
            if ev < 0:
                score -= 20  # Significant penalty for -EV

            # Additional bonus for edge over the book
            if edge > 0:
                score += edge * 0.5

            # Penalty for very short odds (hard to profit)
            if odds < -200:
                score -= 5

        # Bonus for higher confidence tiers
        if confidence >= 65:
            score += 3
        if confidence >= 70:
            score += 3

        scored.append((score, ev, pred))

    # Sort by score descending
    scored.sort(key=lambda x: x[0], reverse=True)

    # Select top bets, preferring +EV and spreading across games
    selected = []
    games_used = {}

    # First pass: select +EV bets
    for score, ev, pred in scored:
        matchup = pred['matchup']
        odds = pred.get('odds')

        # Skip -EV bets if we have odds data
        if odds is not None and ev < 0:
            continue

        # Allow max 2 bets per game
        if games_used.get(matchup, 0) < 2:
            pred['selected'] = 1
            selected.append(pred)
            games_used[matchup] = games_used.get(matchup, 0) + 1

            if len(selected) >= max_bets:
                break

    # If we don't have enough +EV bets, fall back to top confidence
    # (only if odds weren't available to calculate EV)
    if len(selected) < max_bets:
        for score, ev, pred in scored:
            if pred in selected:
                continue
            matchup = pred['matchup']
            odds = pred.get('odds')

            # Only include bets without odds data (can't calculate EV)
            if odds is not None:
                continue

            if games_used.get(matchup, 0) < 2:
                pred['selected'] = 1
                selected.append(pred)
                games_used[matchup] = games_used.get(matchup, 0) + 1

                if len(selected) >= max_bets:
                    break

    # Mark non-selected predictions
    for pred in all_predictions:
        if pred not in selected:
            pred['selected'] = 0

    return all_predictions


def save_todays_predictions():
    """Save today's predictions from the ML model with odds"""
    from nhl_1p_ml_model import NHL1PGoalsModel

    date_str = datetime.now().strftime("%Y-%m-%d")
    tracker = BetResultsTracker()

    # Load model and get predictions
    model = NHL1PGoalsModel()
    try:
        model.load_models()
    except FileNotFoundError:
        print("Model not trained yet")
        return

    # Get today's games
    url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
    response = requests.get(url, timeout=15)
    if response.status_code != 200:
        print("Could not fetch schedule")
        return

    data = response.json()
    games = []
    for day in data.get("gameWeek", []):
        if day.get("date") == date_str:
            for game in day.get("games", []):
                games.append({
                    "home": game.get("homeTeam", {}).get("abbrev", ""),
                    "away": game.get("awayTeam", {}).get("abbrev", ""),
                })
            break

    # Fetch odds from Action Network (has 1P team totals)
    print("Fetching 1P odds from Action Network...")
    odds_data = fetch_nhl_1p_odds()

    predictions = []
    for game in games:
        home = game["home"]
        away = game["away"]
        pred = model.predict_game(home, away)

        if pred is None:
            continue

        matchup = f"{away} @ {home}"
        game_odds = odds_data.get(matchup, {})

        # Build fatigue notes
        fatigue_notes = []
        if pred.get('home_b2b'):
            fatigue_notes.append(f"{home} B2B")
        if pred.get('away_b2b'):
            fatigue_notes.append(f"{away} B2B")
        if pred.get('home_3_in_4'):
            fatigue_notes.append(f"{home} 3-in-4")
        if pred.get('away_3_in_4'):
            fatigue_notes.append(f"{away} 3-in-4")
        if pred.get('away_road_trip_game', 0) >= 3:
            fatigue_notes.append(f"{away} Road #{pred['away_road_trip_game']}")

        fatigue_str = ", ".join(fatigue_notes) if fatigue_notes else ""

        # Home team over 0.5
        if pred["prob_home_over_0_5"] >= 55:
            predictions.append({
                "matchup": matchup,
                "bet_type": f"{home} Over 0.5 (1P)",
                "confidence": pred["prob_home_over_0_5"],
                "expected_goals": pred["expected_home_goals"],
                "odds": game_odds.get('home_over_0_5'),
                "odds_source": game_odds.get('source', 'N/A'),
                "fatigue_notes": fatigue_str
            })

        # Away team over 0.5
        if pred["prob_away_over_0_5"] >= 55:
            predictions.append({
                "matchup": matchup,
                "bet_type": f"{away} Over 0.5 (1P)",
                "confidence": pred["prob_away_over_0_5"],
                "expected_goals": pred["expected_away_goals"],
                "odds": game_odds.get('away_over_0_5'),
                "odds_source": game_odds.get('source', 'N/A'),
                "fatigue_notes": fatigue_str
            })

        # Total over 1.5
        if pred["prob_total_over_1_5"] >= 55:
            predictions.append({
                "matchup": matchup,
                "bet_type": "1P Total Over 1.5",
                "confidence": pred["prob_total_over_1_5"],
                "expected_goals": pred["expected_total_goals"],
                "odds": game_odds.get('total_over_1_5'),
                "odds_source": game_odds.get('source', 'N/A'),
                "fatigue_notes": fatigue_str
            })

    # Select best 3-5 bets
    print(f"\nFound {len(predictions)} qualifying predictions, selecting top {MAX_BETS_PER_DAY}...")
    predictions = select_best_bets(predictions, MAX_BETS_PER_DAY)

    selected = [p for p in predictions if p.get('selected', 0) == 1]
    print(f"Selected {len(selected)} best bets:")
    for p in selected:
        odds_str = f"({p['odds']:+d})" if p.get('odds') else "(no odds)"
        print(f"  {p['matchup']}: {p['bet_type']} @ {p['confidence']:.1f}% {odds_str}")

    tracker.save_predictions(date_str, predictions)
    return predictions


def main():
    """Main entry point"""
    tracker = BetResultsTracker()

    # Save today's predictions
    print("Saving today's predictions...")
    save_todays_predictions()

    # Update results and generate report
    report = tracker.update_and_report()
    print("\n" + report)


if __name__ == "__main__":
    main()
