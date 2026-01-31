"""
Log Daily Predictions to Performance Tracker
==============================================
Parses daily prediction files and logs them to the tracking database
"""

import sys
import os
import csv
import re
from datetime import datetime
from track_performance import log_prediction, init_database

def parse_nhl_predictions(file_path, date):
    """Parse NHL ML predictions from text file"""
    if not os.path.exists(file_path):
        print(f"NHL file not found: {file_path}")
        return 0

    count = 0
    with open(file_path, 'r') as f:
        content = f.read()

        # Parse high-confidence predictions
        # Pattern: "PHI @ NJD: NJD (92.9%)"
        matches = re.findall(r'([A-Z]{3}) @ ([A-Z]{3}): ([A-Z]{3}) \((\d+\.\d+)%\)', content)

        for away, home, winner, confidence in matches:
            game = f"{away} @ {home}"
            confidence_val = float(confidence) / 100

            # Only log high-confidence picks (90%+)
            if confidence_val >= 0.90:
                log_prediction(
                    date=date,
                    sport='NHL',
                    bet_type='ML',
                    game=game,
                    home_team=home,
                    away_team=away,
                    selection=winner,
                    odds=-200,  # Estimate for high confidence
                    confidence=confidence_val,
                    stake=100.0,
                    notes="ML Model (High Confidence)"
                )
                count += 1

    return count

def parse_nba_predictions(file_path, date):
    """Parse NBA predictions from text file"""
    if not os.path.exists(file_path):
        print(f"NBA file not found: {file_path}")
        return 0

    count = 0
    with open(file_path, 'r') as f:
        content = f.read()

        # Parse XGBoost predictions with positive EV
        # Pattern: "Washington Wizards EV: 31.62"
        lines = content.split('\n')

        for i, line in enumerate(lines):
            if 'EV:' in line and 'Fraction of Bankroll: 0%' not in lines[i+1] if i+1 < len(lines) else True:
                # Extract team and EV
                match = re.search(r'([\w\s]+) EV: ([-\d.]+)', line)
                if match:
                    team = match.group(1).strip()
                    ev = float(match.group(2))

                    if ev > 0:  # Only positive EV
                        # Look for odds
                        odds_match = re.search(f'{team}.*?\(([+-]\d+)\)', content)
                        odds = int(odds_match.group(1)) if odds_match else 0

                        # Estimate confidence from EV
                        confidence = min(0.95, 0.50 + (ev / 100))

                        log_prediction(
                            date=date,
                            sport='NBA',
                            bet_type='ML',
                            game=team,
                            home_team='',
                            away_team='',
                            selection=team,
                            odds=odds,
                            confidence=confidence,
                            stake=100.0,
                            notes=f"XGBoost Model (EV: +{ev:.2f})"
                        )
                        count += 1

    return count

def parse_ncaa_predictions(file_path, date):
    """Parse NCAA betting angles from text file"""
    if not os.path.exists(file_path):
        print(f"NCAA file not found: {file_path}")
        return 0

    count = 0
    with open(file_path, 'r') as f:
        content = f.read()

        # Parse HIGH confidence bets
        # Pattern: "[HIGH] BET: Baylor Bears ML"
        high_bets = re.findall(r'\[HIGH\] BET: ([\w\s]+) (ML|Spread)', content)

        for team, bet_type in high_bets:
            team = team.strip()

            # Extract game context
            game_match = re.search(f'GAME: (.*?) @ {team}', content)
            if not game_match:
                game_match = re.search(f'GAME: {team} @ (.*?)\n', content)

            opponent = game_match.group(1).strip() if game_match else "Unknown"
            game = f"{opponent} vs {team}" if game_match else team

            log_prediction(
                date=date,
                sport='NCAA',
                bet_type=bet_type,
                game=game,
                home_team=team,
                away_team=opponent,
                selection=team,
                odds=-110,
                confidence=0.82,  # Historical win rate from file
                stake=100.0,
                notes="Situational Betting Angle (HIGH)"
            )
            count += 1

    return count

def parse_soccer_predictions(file_path, date):
    """Parse Soccer predictions from CSV"""
    if not os.path.exists(file_path):
        print(f"Soccer file not found: {file_path}")
        return 0

    count = 0
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            confidence = float(row['confidence'])

            # Only log high-confidence picks (90%+)
            if confidence >= 0.90:
                game = f"{row['home_team']} vs {row['away_team']}"

                log_prediction(
                    date=date,
                    sport='Soccer',
                    bet_type=row['market'],
                    game=game,
                    home_team=row['home_team'],
                    away_team=row['away_team'],
                    selection=row['selection'],
                    odds=float(row['odds']),
                    confidence=confidence,
                    stake=100.0,
                    notes=f"{row['league']} - Kelly: {float(row['kelly_stake'])*100:.1f}%"
                )
                count += 1

    return count

def main():
    if len(sys.argv) < 2:
        print("Usage: python log_daily_predictions.py YYYY-MM-DD")
        sys.exit(1)

    date = sys.argv[1]
    reports_dir = f"/Users/dickgibbons/Daily Reports/{date}"

    print(f"="*80)
    print(f"LOGGING PREDICTIONS FOR {date}")
    print(f"="*80)

    # Initialize database if needed
    if not os.path.exists("/Users/dickgibbons/sports-betting/betting_tracker.db"):
        print("\nInitializing tracking database...")
        init_database()

    total_logged = 0

    # Parse NHL
    nhl_file = f"{reports_dir}/nhl_ml_totals_{date}.txt"
    nhl_count = parse_nhl_predictions(nhl_file, date)
    print(f"NHL: {nhl_count} predictions logged")
    total_logged += nhl_count

    # Parse NBA
    nba_file = f"{reports_dir}/nba_predictions_{date}.txt"
    nba_count = parse_nba_predictions(nba_file, date)
    print(f"NBA: {nba_count} predictions logged")
    total_logged += nba_count

    # Parse NCAA
    ncaa_file = f"{reports_dir}/ncaa_betting_angles_{date}.txt"
    ncaa_count = parse_ncaa_predictions(ncaa_file, date)
    print(f"NCAA: {ncaa_count} predictions logged")
    total_logged += ncaa_count

    # Parse Soccer
    soccer_file = f"{reports_dir}/soccer_best_bets_{date}.csv"
    soccer_count = parse_soccer_predictions(soccer_file, date)
    print(f"Soccer: {soccer_count} predictions logged")
    total_logged += soccer_count

    print(f"\n✓ Total: {total_logged} predictions logged for {date}")
    print(f"="*80)

if __name__ == "__main__":
    main()
