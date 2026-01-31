"""
NHL First Period Trend Reports Generator
=========================================
Creates visual trend reports for 1P goals scored, allowed, and totals by team.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import os

def fetch_nhl_games_range(start_date, end_date):
    """Fetch NHL games for a date range with 1P stats"""
    all_games = []

    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    print(f"Fetching games from {start_date} to {end_date}...")

    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')

        try:
            url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
            response = requests.get(url, timeout=10)
            data = response.json()

            if 'gameWeek' in data:
                for day in data['gameWeek']:
                    day_date = day.get('date', date_str)  # Get actual game date from API

                    for game in day.get('games', []):
                        if game['gameState'] in ['OFF', 'FINAL']:
                            # Check if this game is within our date range
                            game_date_obj = datetime.strptime(day_date, '%Y-%m-%d')
                            if game_date_obj < current_date or game_date_obj > end:
                                continue

                            # Get detailed game data for period stats
                            game_id = game['id']
                            landing_url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/landing"

                            try:
                                landing_data = requests.get(landing_url, timeout=10).json()

                                # Extract 1P goals using same structure as nhl_ml_totals_predictor.py
                                home_1p = 0
                                away_1p = 0
                                home_team_abbrev = game['homeTeam']['abbrev']

                                if 'summary' in landing_data and 'scoring' in landing_data['summary']:
                                    scoring_by_period = landing_data['summary']['scoring']

                                    # Find period 1
                                    for period in scoring_by_period:
                                        if period.get('periodDescriptor', {}).get('number') == 1:
                                            goals_in_period = period.get('goals', [])

                                            for goal in goals_in_period:
                                                goal_team = goal.get('teamAbbrev', {}).get('default', '')
                                                if goal_team == home_team_abbrev:
                                                    home_1p += 1
                                                else:
                                                    away_1p += 1
                                            break

                                game_data = {
                                    'date': day_date,  # Use actual game date
                                    'home_team': game['homeTeam']['abbrev'],
                                    'away_team': game['awayTeam']['abbrev'],
                                    'home_1p_goals': home_1p,
                                    'away_1p_goals': away_1p,
                                    'total_1p_goals': home_1p + away_1p
                                }

                                all_games.append(game_data)

                            except Exception as e:
                                print(f"  Error fetching game {game_id}: {e}")
                                continue

            print(f"  Week of {date_str}: {len(all_games)} games so far")

        except Exception as e:
            print(f"  Error fetching {date_str}: {e}")

        # Jump by weeks since API returns weekly data
        current_date += timedelta(days=7)

    return pd.DataFrame(all_games)

def create_goals_scored_report(games_df, teams):
    """Create report showing goals scored in 1P by each team"""
    dates = sorted(games_df['date'].unique(), reverse=True)  # Most recent first

    # Initialize matrix with teams as rows, dates as columns
    data = []

    for team in teams:
        row = {'Team': team}

        for date in dates:
            date_games = games_df[games_df['date'] == date]

            # Check if team played (home or away)
            home_game = date_games[date_games['home_team'] == team]
            away_game = date_games[date_games['away_team'] == team]

            if len(home_game) > 0:
                row[date] = f"{home_game.iloc[0]['home_1p_goals']} (H)"
            elif len(away_game) > 0:
                row[date] = f"{away_game.iloc[0]['away_1p_goals']} (A)"
            else:
                row[date] = "NA"

        data.append(row)

    return pd.DataFrame(data)

def create_goals_allowed_report(games_df, teams):
    """Create report showing goals allowed in 1P by each team"""
    dates = sorted(games_df['date'].unique(), reverse=True)  # Most recent first

    # Initialize matrix with teams as rows, dates as columns
    data = []

    for team in teams:
        row = {'Team': team}

        for date in dates:
            date_games = games_df[games_df['date'] == date]

            # Check if team played (home or away)
            home_game = date_games[date_games['home_team'] == team]
            away_game = date_games[date_games['away_team'] == team]

            if len(home_game) > 0:
                # Home team allowed = away team scored
                row[date] = f"{home_game.iloc[0]['away_1p_goals']} (H)"
            elif len(away_game) > 0:
                # Away team allowed = home team scored
                row[date] = f"{away_game.iloc[0]['home_1p_goals']} (A)"
            else:
                row[date] = "NA"

        data.append(row)

    return pd.DataFrame(data)

def create_total_goals_report(games_df, teams):
    """Create report showing total 1P goals in each team's game"""
    dates = sorted(games_df['date'].unique(), reverse=True)  # Most recent first

    # Initialize matrix with teams as rows, dates as columns
    data = []

    for team in teams:
        row = {'Team': team}

        for date in dates:
            date_games = games_df[games_df['date'] == date]

            # Check if team played (home or away)
            home_game = date_games[date_games['home_team'] == team]
            away_game = date_games[date_games['away_team'] == team]

            if len(home_game) > 0:
                row[date] = f"{home_game.iloc[0]['total_1p_goals']} (H)"
            elif len(away_game) > 0:
                row[date] = f"{away_game.iloc[0]['total_1p_goals']} (A)"
            else:
                row[date] = "NA"

        data.append(row)

    return pd.DataFrame(data)

def create_percentage_trends_report(games_df, teams):
    """Create report showing rolling percentages for recent games

    For each team, shows % of last N games where:
    - Team scored > 0 goal (i.e., >= 1 goal)
    - Team allowed > 0 goal (i.e., >= 1 goal)
    - Total 1P goals > 1.5 (i.e., >= 2 goals)

    Windows: Last 3, 5, 10, 20 games
    """
    windows = [3, 5, 10, 20]
    data = []

    for team in teams:
        row = {'Team': team}

        # Get all games for this team (home and away), sorted by date (most recent first)
        home_games = games_df[games_df['home_team'] == team].copy()
        home_games['team_scored'] = home_games['home_1p_goals']
        home_games['team_allowed'] = home_games['away_1p_goals']

        away_games = games_df[games_df['away_team'] == team].copy()
        away_games['team_scored'] = away_games['away_1p_goals']
        away_games['team_allowed'] = away_games['home_1p_goals']

        # Combine and sort by date (most recent first)
        team_games = pd.concat([home_games, away_games])
        team_games = team_games.sort_values('date', ascending=False)

        # Calculate season-long percentages first (all games)
        if len(team_games) > 0:
            season_scored = (team_games['team_scored'] > 0).sum()
            season_scored_pct = (season_scored / len(team_games)) * 100

            season_allowed = (team_games['team_allowed'] > 0).sum()
            season_allowed_pct = (season_allowed / len(team_games)) * 100

            season_total = (team_games['total_1p_goals'] > 1.5).sum()
            season_total_pct = (season_total / len(team_games)) * 100

            row['Scored>0 Season'] = f"{season_scored_pct:.0f}%"
            row['Allowed>0 Season'] = f"{season_allowed_pct:.0f}%"
            row['Total>1.5 Season'] = f"{season_total_pct:.0f}%"
        else:
            row['Scored>0 Season'] = "N/A"
            row['Allowed>0 Season'] = "N/A"
            row['Total>1.5 Season'] = "N/A"

        # Calculate percentages for each window
        for window in windows:
            recent_games = team_games.head(window)

            if len(recent_games) >= window:
                # Scored > 0 goal (i.e., >= 1)
                scored_over_0 = (recent_games['team_scored'] > 0).sum()
                scored_pct = (scored_over_0 / window) * 100

                # Allowed > 0 goal (i.e., >= 1)
                allowed_over_0 = (recent_games['team_allowed'] > 0).sum()
                allowed_pct = (allowed_over_0 / window) * 100

                # Total > 1.5 (i.e., >= 2)
                total_over_1_5 = (recent_games['total_1p_goals'] > 1.5).sum()
                total_pct = (total_over_1_5 / window) * 100
            else:
                # Not enough games
                scored_pct = None
                allowed_pct = None
                total_pct = None

            # Format as percentages
            row[f'Scored>0 L{window}'] = f"{scored_pct:.0f}%" if scored_pct is not None else "N/A"
            row[f'Allowed>0 L{window}'] = f"{allowed_pct:.0f}%" if allowed_pct is not None else "N/A"
            row[f'Total>1.5 L{window}'] = f"{total_pct:.0f}%" if total_pct is not None else "N/A"

        data.append(row)

    return pd.DataFrame(data)

def generate_reports(days_back=30, output_dir=None):
    """Generate all three trend reports"""
    print("="*80)
    print("NHL FIRST PERIOD TREND REPORTS GENERATOR")
    print("="*80)

    # Calculate date range (use 2024 for current NHL season)
    end_date = datetime.now()
    # Fix year to 2024 if system clock is wrong
    if end_date.year >= 2025:
        end_date = end_date.replace(year=2024)
    start_date = end_date - timedelta(days=days_back)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print(f"\nFetching last {days_back} days of games...")
    print(f"Date range: {start_str} to {end_str}")

    # Fetch games
    games_df = fetch_nhl_games_range(start_str, end_str)

    if len(games_df) == 0:
        print("\n❌ No games found!")
        return

    print(f"\n✓ Fetched {len(games_df)} games")

    # Get all teams
    teams = sorted(set(list(games_df['home_team'].unique()) + list(games_df['away_team'].unique())))
    print(f"✓ Found {len(teams)} teams: {', '.join(teams)}")

    # Set output directory
    if output_dir is None:
        today = datetime.now().strftime('%Y-%m-%d')
        output_dir = f"/Users/dickgibbons/Daily Reports/{today}"

    os.makedirs(output_dir, exist_ok=True)

    # Generate reports
    print("\n" + "-"*80)
    print("GENERATING REPORTS")
    print("-"*80)

    # Report 1: Goals Scored
    print("\n1. Goals Scored in 1P...")
    goals_scored = create_goals_scored_report(games_df, teams)
    output_file_1 = f"{output_dir}/nhl_1p_goals_scored_trend.csv"
    goals_scored.to_csv(output_file_1, index=False)
    print(f"   ✓ Saved: {output_file_1}")
    print(f"   Shape: {goals_scored.shape[0]} teams x {goals_scored.shape[1]} columns (dates)")

    # Report 2: Goals Allowed
    print("\n2. Goals Allowed in 1P...")
    goals_allowed = create_goals_allowed_report(games_df, teams)
    output_file_2 = f"{output_dir}/nhl_1p_goals_allowed_trend.csv"
    goals_allowed.to_csv(output_file_2, index=False)
    print(f"   ✓ Saved: {output_file_2}")
    print(f"   Shape: {goals_allowed.shape[0]} teams x {goals_allowed.shape[1]} columns (dates)")

    # Report 3: Total Goals
    print("\n3. Total 1P Goals...")
    total_goals = create_total_goals_report(games_df, teams)
    output_file_3 = f"{output_dir}/nhl_1p_total_goals_trend.csv"
    total_goals.to_csv(output_file_3, index=False)
    print(f"   ✓ Saved: {output_file_3}")
    print(f"   Shape: {total_goals.shape[0]} teams x {total_goals.shape[1]} columns (dates)")

    # Report 4: Percentage Trends (Rolling Windows)
    print("\n4. Percentage Trends (Last 3, 5, 10, 20 games)...")
    pct_trends = create_percentage_trends_report(games_df, teams)
    output_file_4 = f"{output_dir}/nhl_1p_percentage_trends.csv"
    pct_trends.to_csv(output_file_4, index=False)
    print(f"   ✓ Saved: {output_file_4}")
    print(f"   Shape: {pct_trends.shape[0]} teams x {pct_trends.shape[1]} columns")

    # Create Excel with all four sheets
    print("\n5. Creating Excel workbook with all sheets...")
    excel_file = f"{output_dir}/nhl_1p_trends_complete.xlsx"

    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        goals_scored.to_excel(writer, sheet_name='Goals Scored', index=False)
        goals_allowed.to_excel(writer, sheet_name='Goals Allowed', index=False)
        total_goals.to_excel(writer, sheet_name='Total Goals', index=False)
        pct_trends.to_excel(writer, sheet_name='Percentage Trends', index=False)

    print(f"   ✓ Saved: {excel_file}")

    # Print sample for verification
    print("\n" + "-"*80)
    print("SAMPLE DATA (First 5 Teams, Last 5 Dates)")
    print("-"*80)
    print("\nGoals Scored (first 5 teams, last 5 dates):")
    # Get first column (Team) + last 5 date columns
    sample_cols = ['Team'] + list(goals_scored.columns[-5:])
    print(goals_scored[sample_cols].head(5).to_string(index=False))

    print("\n" + "="*80)
    print("USAGE INSTRUCTIONS")
    print("="*80)
    print(f"""
How to use these reports:

1. OPEN THE EXCEL FILE:
   {excel_file}

2. FOUR SHEETS AVAILABLE:
   • Goals Scored      - How many goals each team scored in 1P
   • Goals Allowed     - How many goals each team allowed in 1P
   • Total Goals       - Total 1P goals in each team's games
   • Percentage Trends - % of recent games with >0 goal scored/allowed, >1.5 total
                        (Rolling windows: Last 3, 5, 10, 20 games)

3. PERCENTAGE TRENDS SHEET:
   Quick reference for betting decisions
   • Scored>0 Season   - % of ALL games team scored 1+ goals in 1P
   • Allowed>0 Season  - % of ALL games team allowed 1+ goals in 1P
   • Total>1.5 Season  - % of ALL games with 2+ total goals in 1P
   • Scored>0 L3/L5/L10/L20  - % games team scored 1+ goals (rolling windows)
   • Allowed>0 L3/L5/L10/L20 - % games team allowed 1+ goals (rolling windows)
   • Total>1.5 L3/L5/L10/L20 - % games with 2+ total goals (rolling windows)

   Example: If EDM shows "80%" in Scored>0 L5, they scored 1+ goals
            in 4 of their last 5 games
            If EDM shows "65%" in Scored>0 Season, they've scored 1+ goals
            in 65% of all games this season

4. FILTER BY HOME/AWAY (Goals Scored/Allowed/Total sheets):
   Each cell shows: "2 (H)" or "1 (A)"
   • (H) = Home game
   • (A) = Away game
   • Use Excel's filter to show only home or away games

5. ANALYZE MATCHUPS:
   Example: Oilers @ Kings tonight

   A) Filter "EDM" column (Oilers):
      - Look at last 5-10 away games (A)
      - Check Goals Scored trend
      - Check Goals Allowed trend
      - Check Total Goals trend

   B) Filter "LAK" column (Kings):
      - Look at last 5-10 home games (H)
      - Check same trends

   C) Visual Analysis:
      - EDM averaging 1.5 1P goals on road (A)
      - LAK allowing 0.8 1P goals at home (H)
      - Recent EDM road games showing O1.5 1P trend
      - Recent LAK home games showing U1.5 1P trend

   D) Make Prediction:
      If trends align → Bet with confidence
      If trends conflict → Skip or reduce stake

   E) Quick Check with Percentage Trends:
      - Go to "Percentage Trends" sheet
      - Look at EDM row: Check "Total>1.5 L5" column
      - Look at LAK row: Check "Total>1.5 L5" column
      - High percentages (60%+) indicate scoring trends

6. EXCEL TIPS:
   • Freeze top row: View → Freeze Panes → Freeze Top Row
   • Auto-filter: Data → Filter
   • Conditional formatting: Highlight high/low values
   • Create charts: Insert → Line Chart for visual trends

7. DAILY UPDATES:
   Run this script daily to get updated trends!

   python3 generate_1p_trend_reports.py
""")

    print("="*80)

if __name__ == "__main__":
    import sys

    days = 30  # Default to last 30 days

    if len(sys.argv) > 1:
        days = int(sys.argv[1])

    generate_reports(days_back=days)
