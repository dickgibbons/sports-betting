"""
Sports Betting Performance Tracker
===================================
Tracks all predictions and calculates real-world performance by sport and bet type.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import json
import requests

DB_PATH = "/Users/dickgibbons/AI Projects/sports-betting/betting_tracker.db"

def init_database():
    """Initialize the tracking database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create predictions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            sport TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            game TEXT NOT NULL,
            home_team TEXT,
            away_team TEXT,
            selection TEXT NOT NULL,
            odds REAL,
            confidence REAL,
            stake REAL DEFAULT 100.0,
            status TEXT DEFAULT 'pending',
            actual_result TEXT,
            profit REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create performance summary table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_summary (
            sport TEXT NOT NULL,
            bet_type TEXT NOT NULL,
            total_bets INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            losses INTEGER DEFAULT 0,
            pending INTEGER DEFAULT 0,
            total_staked REAL DEFAULT 0.0,
            total_profit REAL DEFAULT 0.0,
            roi REAL DEFAULT 0.0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (sport, bet_type)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH}")

def log_prediction(date, sport, bet_type, game, home_team, away_team, selection, odds, confidence, stake=100.0, notes=""):
    """Log a new prediction"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO predictions (date, sport, bet_type, game, home_team, away_team, selection, odds, confidence, stake, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (date, sport, bet_type, game, home_team, away_team, selection, odds, confidence, stake, notes))

    conn.commit()
    conn.close()

def get_nhl_results(date):
    """Fetch NHL game results for a specific date"""
    try:
        url = f"https://api-web.nhle.com/v1/schedule/{date}"
        response = requests.get(url, timeout=10)
        data = response.json()

        results = {}
        if 'gameWeek' in data:
            for day in data['gameWeek']:
                for game in day.get('games', []):
                    home = game['homeTeam']['abbrev']
                    away = game['awayTeam']['abbrev']

                    if game['gameState'] in ['OFF', 'FINAL']:
                        home_score = game['homeTeam']['score']
                        away_score = game['awayTeam']['score']
                        total = home_score + away_score

                        game_key = f"{away} @ {home}"
                        results[game_key] = {
                            'home_score': home_score,
                            'away_score': away_score,
                            'total': total,
                            'winner': home if home_score > away_score else away
                        }

        return results
    except Exception as e:
        print(f"Error fetching NHL results: {e}")
        return {}

def get_nba_results(date):
    """Fetch NBA game results for a specific date"""
    try:
        # Convert date format for NBA API (YYYYMMDD)
        date_formatted = date.replace('-', '')
        url = f"https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_{date_formatted}.json"
        response = requests.get(url, timeout=10)
        data = response.json()

        results = {}
        for game in data.get('scoreboard', {}).get('games', []):
            if game['gameStatusText'] == 'Final':
                home = game['homeTeam']['teamTricode']
                away = game['awayTeam']['teamTricode']
                home_score = game['homeTeam']['score']
                away_score = game['awayTeam']['score']
                total = home_score + away_score

                game_key = f"{away} @ {home}"
                results[game_key] = {
                    'home_score': home_score,
                    'away_score': away_score,
                    'total': total,
                    'winner': home if home_score > away_score else away
                }

        return results
    except Exception as e:
        print(f"Error fetching NBA results: {e}")
        return {}

def get_soccer_results(date):
    """Fetch soccer game results for a specific date from API-Sports"""
    API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
    API_BASE = "https://v3.football.api-sports.io"

    try:
        headers = {"x-apisports-key": API_KEY}
        url = f"{API_BASE}/fixtures"
        params = {"date": date}

        response = requests.get(url, params=params, headers=headers, timeout=60)
        data = response.json()

        results = {}
        for fixture in data.get('response', []):
            status = fixture.get('fixture', {}).get('status', {}).get('short', '')

            # Only process finished games
            if status not in ['FT', 'AET', 'PEN']:
                continue

            teams = fixture.get('teams', {})
            goals = fixture.get('goals', {})
            score = fixture.get('score', {})

            home_team = teams.get('home', {}).get('name', '')
            away_team = teams.get('away', {}).get('name', '')
            home_score = goals.get('home', 0) or 0
            away_score = goals.get('away', 0) or 0
            total = home_score + away_score

            # Get halftime scores for H1 bets
            halftime = score.get('halftime', {})
            h1_home = halftime.get('home', 0) or 0
            h1_away = halftime.get('away', 0) or 0
            h1_total = h1_home + h1_away

            # Determine winner
            if home_score > away_score:
                winner = home_team
                winner_type = 'home'
            elif away_score > home_score:
                winner = away_team
                winner_type = 'away'
            else:
                winner = 'Draw'
                winner_type = 'draw'

            # BTTS check
            btts = (home_score > 0 and away_score > 0)

            game_key = f"{home_team} vs {away_team}"
            results[game_key] = {
                'home_team': home_team,
                'away_team': away_team,
                'home_score': home_score,
                'away_score': away_score,
                'total': total,
                'h1_total': h1_total,
                'h1_home': h1_home,
                'h1_away': h1_away,
                'winner': winner,
                'winner_type': winner_type,
                'btts': btts
            }

        return results
    except Exception as e:
        print(f"Error fetching Soccer results: {e}")
        return {}

def update_results():
    """Update pending predictions with actual results"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all pending predictions
    cursor.execute("SELECT * FROM predictions WHERE status = 'pending' ORDER BY date")
    pending = cursor.fetchall()

    print(f"\nChecking {len(pending)} pending predictions...")

    updated_count = 0

    for pred in pending:
        pred_id, date, sport, bet_type, game, home_team, away_team, selection, odds, confidence, stake, status, actual_result, profit, notes, created_at = pred

        # Only check games from yesterday or earlier
        pred_date = datetime.strptime(date, '%Y-%m-%d')
        if pred_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            continue

        results = {}
        if sport == 'NHL':
            results = get_nhl_results(date)
        elif sport == 'NBA':
            results = get_nba_results(date)
        elif sport == 'Soccer':
            results = get_soccer_results(date)

        if game not in results:
            print(f"  No results yet for {game}")
            continue

        result = results[game]
        won = False

        # Determine if bet won
        if bet_type == 'ML':
            won = (selection == result['winner'])
        elif bet_type == 'OVER':
            line = float(selection.split()[1])
            won = result['total'] > line
        elif bet_type == 'UNDER':
            line = float(selection.split()[1])
            won = result['total'] < line
        # Soccer-specific bet types
        elif bet_type == 'Away Win':
            won = (result.get('winner_type') == 'away')
        elif bet_type == 'Home Win':
            won = (result.get('winner_type') == 'home')
        elif bet_type == 'BTTS Yes':
            won = result.get('btts', False)
        elif bet_type == 'BTTS No':
            won = not result.get('btts', True)
        elif bet_type == 'H1 Under 1.5':
            won = result.get('h1_total', 0) < 1.5
        elif bet_type == 'H1 Over 0.5':
            won = result.get('h1_total', 0) > 0.5
        elif bet_type == 'H1 Over 1.5':
            won = result.get('h1_total', 0) > 1.5
        elif bet_type == 'Over 2.5':
            won = result.get('total', 0) > 2.5
        elif bet_type == 'Under 2.5':
            won = result.get('total', 0) < 2.5

        # Calculate profit
        if won:
            if odds > 0:
                bet_profit = stake * (odds / 100)
            else:
                bet_profit = stake * (100 / abs(odds))
        else:
            bet_profit = -stake

        # Update prediction
        cursor.execute('''
            UPDATE predictions
            SET status = ?, actual_result = ?, profit = ?
            WHERE id = ?
        ''', ('won' if won else 'lost', json.dumps(result), bet_profit, pred_id))

        updated_count += 1
        print(f"  ✓ Updated: {game} - {'WON' if won else 'LOST'} ${bet_profit:+.2f}")

    conn.commit()
    conn.close()

    if updated_count > 0:
        update_performance_summary()
        print(f"\n✓ Updated {updated_count} predictions")
    else:
        print("  No predictions to update")

def update_performance_summary():
    """Recalculate performance summary from all predictions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing summary
    cursor.execute("DELETE FROM performance_summary")

    # Calculate stats by sport and bet type
    cursor.execute('''
        SELECT
            sport,
            bet_type,
            COUNT(*) as total_bets,
            SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(stake) as total_staked,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM predictions
        GROUP BY sport, bet_type
    ''')

    results = cursor.fetchall()

    for sport, bet_type, total, wins, losses, pending, staked, profit in results:
        roi = (profit / staked * 100) if staked > 0 else 0

        cursor.execute('''
            INSERT INTO performance_summary (sport, bet_type, total_bets, wins, losses, pending, total_staked, total_profit, roi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sport, bet_type, total, wins, losses, pending, staked, profit, roi))

    conn.commit()
    conn.close()

def show_performance():
    """Display current performance summary"""
    conn = sqlite3.connect(DB_PATH)

    print("\n" + "="*80)
    print("SPORTS BETTING PERFORMANCE TRACKER")
    print("="*80)

    # Overall stats
    overall = pd.read_sql_query('''
        SELECT
            COUNT(*) as total_bets,
            SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(stake) as total_staked,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM predictions
    ''', conn)

    if overall['total_bets'].iloc[0] > 0:
        total = overall['total_bets'].iloc[0]
        wins = overall['wins'].iloc[0]
        losses = overall['losses'].iloc[0]
        pending = overall['pending'].iloc[0]
        staked = overall['total_staked'].iloc[0]
        profit = overall['total_profit'].iloc[0]
        roi = (profit / staked * 100) if staked > 0 else 0
        win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Total Bets: {total} ({wins}W-{losses}L-{pending}P)")
        print(f"  Win Rate: {win_pct:.1f}%")
        print(f"  Total Staked: ${staked:,.2f}")
        print(f"  Total Profit: ${profit:+,.2f}")
        print(f"  ROI: {roi:+.2f}%")
    else:
        print("\nNo predictions tracked yet!")
        conn.close()
        return

    # Performance by sport
    print(f"\n" + "="*80)
    print("PERFORMANCE BY SPORT")
    print("="*80)

    by_sport = pd.read_sql_query('''
        SELECT
            sport,
            COUNT(*) as total_bets,
            SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(stake) as total_staked,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM predictions
        GROUP BY sport
        ORDER BY total_profit DESC
    ''', conn)

    for _, row in by_sport.iterrows():
        roi = (row['total_profit'] / row['total_staked'] * 100) if row['total_staked'] > 0 else 0
        win_pct = (row['wins'] / (row['wins'] + row['losses']) * 100) if (row['wins'] + row['losses']) > 0 else 0

        print(f"\n{row['sport']}:")
        print(f"  Bets: {int(row['total_bets'])} ({int(row['wins'])}W-{int(row['losses'])}L-{int(row['pending'])}P)")
        print(f"  Win Rate: {win_pct:.1f}%")
        print(f"  Profit: ${row['total_profit']:+,.2f}")
        print(f"  ROI: {roi:+.2f}%")

    # Performance by bet type
    print(f"\n" + "="*80)
    print("PERFORMANCE BY BET TYPE")
    print("="*80)

    by_type = pd.read_sql_query('''
        SELECT
            sport,
            bet_type,
            COUNT(*) as total_bets,
            SUM(CASE WHEN status = 'won' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'lost' THEN 1 ELSE 0 END) as losses,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(stake) as total_staked,
            SUM(COALESCE(profit, 0)) as total_profit
        FROM predictions
        GROUP BY sport, bet_type
        ORDER BY sport, total_profit DESC
    ''', conn)

    current_sport = None
    for _, row in by_type.iterrows():
        if row['sport'] != current_sport:
            print(f"\n{row['sport']}:")
            current_sport = row['sport']

        roi = (row['total_profit'] / row['total_staked'] * 100) if row['total_staked'] > 0 else 0
        win_pct = (row['wins'] / (row['wins'] + row['losses']) * 100) if (row['wins'] + row['losses']) > 0 else 0

        print(f"  {row['bet_type']}: {int(row['total_bets'])} bets, {win_pct:.1f}% win rate, ${row['total_profit']:+,.2f} ({roi:+.2f}% ROI)")

    # Recent predictions
    print(f"\n" + "="*80)
    print("RECENT PREDICTIONS (Last 10)")
    print("="*80)

    recent = pd.read_sql_query('''
        SELECT date, sport, bet_type, game, selection, confidence, status, profit
        FROM predictions
        ORDER BY created_at DESC
        LIMIT 10
    ''', conn)

    for _, row in recent.iterrows():
        status_icon = "✓" if row['status'] == 'won' else "✗" if row['status'] == 'lost' else "⏳"
        profit_str = f"${row['profit']:+.2f}" if pd.notna(row['profit']) else "Pending"
        print(f"{status_icon} {row['date']} | {row['sport']} {row['bet_type']} | {row['game']}")
        print(f"   Selection: {row['selection']} ({row['confidence']*100:.1f}% conf) | {profit_str}")

    conn.close()
    print("\n" + "="*80)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "init":
            init_database()
        elif command == "update":
            update_results()
        elif command == "show":
            show_performance()
        else:
            print("Usage: python track_performance.py [init|update|show]")
    else:
        show_performance()
