#!/usr/bin/env python3
"""
Combined Bet Results Tracker - NHL and Soccer

Tracks predictions vs actual results for all sports.
Generates cumulative CSV reports showing win/loss records.
"""

import csv
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# API Keys
FOOTBALL_API_KEY = "960c628e1c91c4b1f125e1eec52ad862"

# Soccer league IDs
SOCCER_LEAGUES = {
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,
    "Bundesliga": 78,
    "Ligue 1": 61,
    "Eredivisie": 88,
    "MLS": 253,
}


class CombinedBetTracker:
    def __init__(self):
        self.db_path = Path("/Users/dickgibbons/AI Projects/sports-betting/tracking/combined_bets.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Combined predictions table for all sports
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                league TEXT,
                matchup TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                odds INTEGER,
                odds_source TEXT,
                selected INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, sport, matchup, bet_type)
            )
        """)

        # Combined results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                league TEXT,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                home_1h_score INTEGER,
                away_1h_score INTEGER,
                total_goals INTEGER,
                game_status TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, sport, home_team, away_team)
            )
        """)

        # Combined bet outcomes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bet_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id INTEGER,
                date TEXT NOT NULL,
                sport TEXT NOT NULL,
                league TEXT,
                matchup TEXT NOT NULL,
                bet_type TEXT NOT NULL,
                confidence REAL,
                odds INTEGER,
                actual_value REAL,
                won INTEGER,
                profit REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id),
                UNIQUE(date, sport, matchup, bet_type)
            )
        """)

        conn.commit()
        conn.close()

    def save_prediction(self, date_str: str, sport: str, league: str, matchup: str,
                       bet_type: str, confidence: float, odds: int = None,
                       selected: int = 0):
        """Save a single prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO predictions
                (date, sport, league, matchup, bet_type, confidence, odds, selected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, sport, league, matchup, bet_type, confidence, odds, selected))
            conn.commit()
        except Exception as e:
            print(f"Error saving prediction: {e}")
        finally:
            conn.close()

    def save_result(self, date_str: str, sport: str, league: str,
                   home_team: str, away_team: str,
                   home_score: int, away_score: int,
                   home_1h_score: int = None, away_1h_score: int = None,
                   game_status: str = "FINAL"):
        """Save a game result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        total_goals = (home_score or 0) + (away_score or 0)

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO results
                (date, sport, league, home_team, away_team, home_score, away_score,
                 home_1h_score, away_1h_score, total_goals, game_status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date_str, sport, league, home_team, away_team, home_score, away_score,
                  home_1h_score, away_1h_score, total_goals, game_status,
                  datetime.now().isoformat()))
            conn.commit()
        except Exception as e:
            print(f"Error saving result: {e}")
        finally:
            conn.close()

    def evaluate_bet(self, date_str: str, sport: str, matchup: str, bet_type: str,
                    actual_value: float, won: int, profit: float):
        """Record bet outcome"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get prediction details
        cursor.execute("""
            SELECT id, confidence, odds, league FROM predictions
            WHERE date = ? AND sport = ? AND matchup = ? AND bet_type = ?
        """, (date_str, sport, matchup, bet_type))
        pred = cursor.fetchone()

        if pred:
            pred_id, confidence, odds, league = pred
            cursor.execute("""
                INSERT OR REPLACE INTO bet_outcomes
                (prediction_id, date, sport, league, matchup, bet_type, confidence,
                 odds, actual_value, won, profit)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (pred_id, date_str, sport, league, matchup, bet_type, confidence,
                  odds, actual_value, won, profit))
            conn.commit()

        conn.close()

    def fetch_soccer_results(self, date_str: str) -> List[Dict]:
        """Fetch soccer results from API-Football"""
        results = []

        for league_name, league_id in SOCCER_LEAGUES.items():
            try:
                # Determine season
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if league_name == "MLS":
                    season = date_obj.year
                else:
                    season = date_obj.year if date_obj.month >= 7 else date_obj.year - 1

                response = requests.get(
                    "https://v3.football.api-sports.io/fixtures",
                    headers={"x-apisports-key": FOOTBALL_API_KEY},
                    params={"league": league_id, "date": date_str, "season": season},
                    timeout=15
                )
                data = response.json()

                for fixture in data.get("response", []):
                    status = fixture.get("fixture", {}).get("status", {}).get("short", "")
                    if status not in ["FT", "AET", "PEN"]:  # Final, After Extra Time, Penalties
                        continue

                    home_team = fixture.get("teams", {}).get("home", {}).get("name", "")
                    away_team = fixture.get("teams", {}).get("away", {}).get("name", "")
                    home_score = fixture.get("goals", {}).get("home", 0) or 0
                    away_score = fixture.get("goals", {}).get("away", 0) or 0

                    # Get halftime scores
                    halftime = fixture.get("score", {}).get("halftime", {})
                    home_1h = halftime.get("home", 0) or 0
                    away_1h = halftime.get("away", 0) or 0

                    results.append({
                        "date": date_str,
                        "sport": "Soccer",
                        "league": league_name,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score,
                        "home_1h_score": home_1h,
                        "away_1h_score": away_1h,
                        "total_goals": home_score + away_score,
                        "game_status": "FINAL"
                    })

            except Exception as e:
                print(f"Error fetching {league_name}: {e}")

        return results

    def evaluate_soccer_bets(self, date_str: str):
        """Evaluate soccer bets against results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get selected soccer predictions
        cursor.execute("""
            SELECT id, matchup, bet_type, confidence, odds, league
            FROM predictions
            WHERE date = ? AND sport = 'Soccer' AND selected = 1
        """, (date_str,))
        predictions = cursor.fetchall()

        # Get results
        cursor.execute("""
            SELECT home_team, away_team, home_score, away_score, home_1h_score, away_1h_score, total_goals, league
            FROM results WHERE date = ? AND sport = 'Soccer' AND game_status = 'FINAL'
        """, (date_str,))

        results_map = {}
        for r in cursor.fetchall():
            # Create matchup key both ways
            matchup1 = f"{r[0]} vs {r[1]}"
            matchup2 = f"{r[1]} vs {r[0]}"
            results_map[matchup1] = r
            results_map[matchup2] = r

        evaluated = 0
        for pred_id, matchup, bet_type, confidence, odds, league in predictions:
            result = results_map.get(matchup)
            if not result:
                continue

            home_team, away_team, home_score, away_score, home_1h, away_1h, total_goals, _ = result

            won = None
            actual_value = None

            # Evaluate different bet types
            if bet_type == "Over 2.5 Goals":
                actual_value = total_goals
                won = 1 if total_goals > 2.5 else 0
            elif bet_type == "BTTS Yes":
                actual_value = 1 if home_score > 0 and away_score > 0 else 0
                won = 1 if actual_value == 1 else 0
            elif bet_type == "1H Over 0.5":
                actual_value = (home_1h or 0) + (away_1h or 0)
                won = 1 if actual_value >= 1 else 0

            # Calculate profit (assume -110 standard odds if not specified)
            profit = None
            if won is not None:
                bet_odds = odds if odds else -110
                if won == 1:
                    if bet_odds > 0:
                        profit = bet_odds / 100
                    else:
                        profit = 100 / abs(bet_odds)
                else:
                    profit = -1

            if won is not None:
                cursor.execute("""
                    INSERT OR REPLACE INTO bet_outcomes
                    (prediction_id, date, sport, league, matchup, bet_type, confidence,
                     odds, actual_value, won, profit)
                    VALUES (?, ?, 'Soccer', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (pred_id, date_str, league, matchup, bet_type, confidence,
                      odds, actual_value, won, profit))
                evaluated += 1

        conn.commit()
        conn.close()
        print(f"Evaluated {evaluated} soccer bets for {date_str}")

    def generate_cumulative_csv(self, date_str: str = None) -> str:
        """Generate CSV with all bet outcomes from all sports"""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date, sport, league, matchup, bet_type, confidence, odds,
                   actual_value, won, profit
            FROM bet_outcomes
            ORDER BY date, sport, matchup
        """)
        outcomes = cursor.fetchall()
        conn.close()

        output_dir = Path(f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date_str}")
        output_dir.mkdir(parents=True, exist_ok=True)
        csv_file = output_dir / "ALL_SPORTS_BET_RESULTS.csv"

        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Date', 'Sport', 'League', 'Matchup', 'Bet', 'Confidence',
                           'Odds', 'Actual', 'Result', 'Profit'])

            for row in outcomes:
                date, sport, league, matchup, bet_type, confidence, odds, actual, won, profit = row
                result = "WIN" if won == 1 else "LOSS" if won == 0 else "PENDING"
                odds_str = f"{odds:+d}" if odds else "-110"
                profit_str = f"{profit:+.2f}" if profit else ""

                writer.writerow([
                    date, sport, league or "", matchup, bet_type,
                    f"{confidence:.1f}%", odds_str, actual, result, profit_str
                ])

        return str(csv_file)

    def generate_summary_report(self, date_str: str = None) -> str:
        """Generate text summary report"""
        date_str = date_str or datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        lines = []
        lines.append("=" * 80)
        lines.append(f"COMBINED BETTING RESULTS - All Sports")
        lines.append(f"Generated: {date_str}")
        lines.append("=" * 80)
        lines.append("")

        # Overall stats
        cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END),
                   SUM(CASE WHEN won = 0 THEN 1 ELSE 0 END),
                   AVG(confidence), SUM(COALESCE(profit, 0))
            FROM bet_outcomes WHERE won IS NOT NULL
        """)
        total, wins, losses, avg_conf, total_profit = cursor.fetchone()
        total = total or 0
        wins = wins or 0
        losses = losses or 0

        lines.append("OVERALL PERFORMANCE")
        lines.append("-" * 40)
        lines.append(f"  Total Bets: {total}")
        lines.append(f"  Wins: {wins} | Losses: {losses}")
        lines.append(f"  Win Rate: {wins/total*100:.1f}%" if total > 0 else "  Win Rate: N/A")
        lines.append(f"  Total Profit: {total_profit or 0:+.2f} units")
        lines.append("")

        # By sport
        cursor.execute("""
            SELECT sport, COUNT(*), SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END),
                   SUM(COALESCE(profit, 0))
            FROM bet_outcomes WHERE won IS NOT NULL
            GROUP BY sport
        """)
        sport_stats = cursor.fetchall()

        lines.append("PERFORMANCE BY SPORT")
        lines.append("-" * 40)
        for sport, cnt, w, p in sport_stats:
            wr = w/cnt*100 if cnt > 0 else 0
            lines.append(f"  {sport}: {w}/{cnt} ({wr:.1f}%) | Profit: {p or 0:+.2f}u")
        lines.append("")

        # Recent daily results
        cursor.execute("""
            SELECT date, sport, COUNT(*), SUM(CASE WHEN won = 1 THEN 1 ELSE 0 END),
                   SUM(COALESCE(profit, 0))
            FROM bet_outcomes WHERE won IS NOT NULL
            GROUP BY date, sport
            ORDER BY date DESC
            LIMIT 14
        """)
        recent = cursor.fetchall()

        lines.append("RECENT RESULTS")
        lines.append("-" * 40)
        for date, sport, cnt, w, p in recent:
            wr = w/cnt*100 if cnt > 0 else 0
            lines.append(f"  {date} [{sport}]: {w}/{cnt} ({wr:.1f}%) | {p or 0:+.2f}u")
        lines.append("")

        # Today's pending bets
        lines.append("TODAY'S SELECTED BETS")
        lines.append("-" * 40)
        cursor.execute("""
            SELECT sport, matchup, bet_type, confidence, odds
            FROM predictions
            WHERE date = ? AND selected = 1
            ORDER BY sport, confidence DESC
        """, (date_str,))
        today_bets = cursor.fetchall()

        if today_bets:
            current_sport = None
            for sport, matchup, bet_type, conf, odds in today_bets:
                if sport != current_sport:
                    lines.append(f"\n  [{sport}]")
                    current_sport = sport
                odds_str = f"({odds:+d})" if odds else ""
                lines.append(f"    {matchup}: {bet_type} @ {conf:.1f}% {odds_str}")
        else:
            lines.append("  No bets selected for today")

        lines.append("")
        lines.append("=" * 80)

        conn.close()
        return "\n".join(lines)


def parse_soccer_profitable_report(report_path: str) -> List[Dict]:
    """Parse soccer profitable angles report and extract top recommendations"""
    predictions = []

    if not Path(report_path).exists():
        print(f"Soccer report not found: {report_path}")
        return predictions

    with open(report_path, 'r') as f:
        content = f.read()

    # Look for the RECOMMENDED BETS section
    if "RECOMMENDED BETS" not in content:
        return predictions

    # Extract date from filename
    import re
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', report_path)
    date_str = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

    # Parse recommendations section
    rec_section = content.split("RECOMMENDED BETS")[1]
    lines = rec_section.split("\n")

    current_league = None
    current_matchup = None

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match league and matchup pattern: "1. Bundesliga - Team A vs Team B"
        league_match = re.match(r'\d+\.\s+(.+?)\s+-\s+(.+?vs.+)', line)
        if league_match:
            current_league = league_match.group(1).strip()
            current_matchup = league_match.group(2).strip()
            i += 1
            continue

        # Match bet type pattern: "BET: Over 2.5 Goals @ 69.3% confidence"
        bet_match = re.match(r'BET:\s+(.+?)\s+@\s+([\d.]+)%\s+confidence', line)
        if bet_match and current_matchup:
            bet_type = bet_match.group(1).strip()
            confidence = float(bet_match.group(2))

            predictions.append({
                "date": date_str,
                "sport": "Soccer",
                "league": current_league,
                "matchup": current_matchup,
                "bet_type": bet_type,
                "confidence": confidence,
                "odds": -110,  # Default standard odds
                "selected": 1
            })

        i += 1

    return predictions


def save_soccer_predictions_from_report(tracker, date_str: str = None):
    """Parse soccer report and save filtered predictions based on performance analysis

    Improvements based on tracking data:
    - DROP BTTS Yes (20% win rate, -3.09u)
    - FOCUS on 1H Over 0.5 (80% win rate, +2.64u)
    - FOCUS on Bundesliga (62.5% win rate, +1.55u)
    - Over 2.5 Goals still profitable (60% win rate, +0.73u)
    """
    date_str = date_str or datetime.now().strftime("%Y-%m-%d")
    report_path = f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date_str}/soccer_profitable_angles_{date_str}.txt"

    predictions = parse_soccer_profitable_report(report_path)

    if not predictions:
        print(f"No soccer predictions found for {date_str}")
        return 0

    # IMPROVEMENT 1: Filter out BTTS Yes (underperforming)
    predictions = [p for p in predictions if p["bet_type"] != "BTTS Yes"]

    # IMPROVEMENT 2: Prioritize high-performing leagues
    preferred_leagues = ["Bundesliga", "MLS", "Eredivisie"]

    # Group by bet type
    by_bet_type = {}
    for pred in predictions:
        bt = pred["bet_type"]
        if bt not in by_bet_type:
            by_bet_type[bt] = []
        by_bet_type[bt].append(pred)

    saved = 0
    for bet_type, preds in by_bet_type.items():
        # Sort by: preferred league first, then confidence
        preds.sort(key=lambda x: (
            0 if x["league"] in preferred_leagues else 1,
            -x["confidence"]
        ))

        # IMPROVEMENT 3: Take more 1H Over 0.5 (best performer), fewer others
        if bet_type == "1H Over 0.5":
            limit = 5  # Best performing bet type
        elif bet_type == "Over 2.5 Goals":
            limit = 3  # Still profitable but less
        else:
            limit = 2  # Minimize other bet types

        for pred in preds[:limit]:
            tracker.save_prediction(
                pred["date"], pred["sport"], pred["league"],
                pred["matchup"], pred["bet_type"], pred["confidence"],
                pred["odds"], pred["selected"]
            )
            saved += 1

    print(f"Saved {saved} soccer predictions for {date_str} (filtered: no BTTS, prioritize Bundesliga)")
    return saved


def import_nhl_data():
    """Import existing NHL bet data into combined tracker"""
    nhl_db = Path("/Users/dickgibbons/AI Projects/sports-betting/nhl/tracking/bet_results.db")
    if not nhl_db.exists():
        print("No existing NHL database found")
        return

    tracker = CombinedBetTracker()

    nhl_conn = sqlite3.connect(nhl_db)
    nhl_cursor = nhl_conn.cursor()

    # Import predictions
    nhl_cursor.execute("""
        SELECT date, matchup, bet_type, confidence, odds, selected
        FROM predictions
    """)
    for row in nhl_cursor.fetchall():
        date, matchup, bet_type, confidence, odds, selected = row
        tracker.save_prediction(date, "NHL", "NHL", matchup, bet_type, confidence, odds, selected)

    # Import outcomes
    nhl_cursor.execute("""
        SELECT date, matchup, bet_type, confidence, odds, actual_value, won, profit
        FROM bet_outcomes
    """)
    for row in nhl_cursor.fetchall():
        date, matchup, bet_type, confidence, odds, actual, won, profit = row
        if won is not None:
            tracker.evaluate_bet(date, "NHL", matchup, bet_type, actual, won, profit)

    nhl_conn.close()
    print("NHL data imported to combined tracker")


def main():
    """Main entry point"""
    tracker = CombinedBetTracker()
    date_str = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Import NHL data if not already done
    import_nhl_data()

    # Save today's soccer predictions from report
    print(f"\nSaving soccer predictions for {date_str}...")
    save_soccer_predictions_from_report(tracker, date_str)

    # Also save yesterday's predictions if not already saved (for backfill)
    print(f"Checking soccer predictions for {yesterday}...")
    save_soccer_predictions_from_report(tracker, yesterday)

    # Fetch and save soccer results for yesterday
    print(f"\nFetching soccer results for {yesterday}...")
    soccer_results = tracker.fetch_soccer_results(yesterday)
    for r in soccer_results:
        tracker.save_result(
            r["date"], r["sport"], r["league"],
            r["home_team"], r["away_team"],
            r["home_score"], r["away_score"],
            r["home_1h_score"], r["away_1h_score"],
            r["game_status"]
        )
    print(f"Saved {len(soccer_results)} soccer results")

    # Evaluate soccer bets for yesterday
    tracker.evaluate_soccer_bets(yesterday)

    # Generate reports
    report = tracker.generate_summary_report(date_str)
    print("\n" + report)

    # Save reports
    output_dir = Path(f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    report_file = output_dir / "ALL_SPORTS_BET_RESULTS.txt"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")

    csv_file = tracker.generate_cumulative_csv(date_str)
    print(f"CSV saved to: {csv_file}")


if __name__ == "__main__":
    main()
