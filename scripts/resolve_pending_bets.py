#!/usr/bin/env python3
"""
Resolve Pending Bets by Fetching Actual Game Results
"""

import json
import requests
from datetime import datetime, timedelta
import time
import re

# API Keys
NHL_API_BASE = "https://api-web.nhle.com/v1"
NBA_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
NCAA_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
FOOTBALL_API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
FOOTBALL_API_BASE = "https://v3.football.api-sports.io"

BET_HISTORY_PATH = "/Users/dickgibbons/AI Projects/sports-betting/data/bet_history.json"


def load_bet_history():
    with open(BET_HISTORY_PATH, 'r') as f:
        return json.load(f)


def save_bet_history(bets):
    with open(BET_HISTORY_PATH, 'w') as f:
        json.dump(bets, f, indent=2)


def extract_pick_from_bet(bet_str, game_str):
    """Extract the team pick from the bet field"""
    if not bet_str:
        return None

    # Remove common suffixes
    bet_str = bet_str.replace(' ML', '').replace(' Moneyline', '').replace('BET: ', '')
    bet_str = bet_str.replace(' Draw No Bet', '').replace(' Win or Draw', '')
    bet_str = bet_str.replace(' -1.5', '').replace(' +1.5', '')

    # Get teams from game string
    if ' @ ' in game_str:
        away, home = game_str.split(' @ ')
    elif ' vs ' in game_str:
        home, away = game_str.split(' vs ')
    else:
        return bet_str.strip()

    # Check which team is in the bet
    if away.lower() in bet_str.lower():
        return away.strip()
    elif home.lower() in bet_str.lower():
        return home.strip()

    return bet_str.strip()


def get_nhl_game_result(date_str, away_team, home_team):
    """Fetch NHL game result"""
    try:
        url = f"{NHL_API_BASE}/schedule/{date_str}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for day in data.get('gameWeek', []):
                for game in day.get('games', []):
                    away = game.get('awayTeam', {}).get('abbrev', '')
                    home = game.get('homeTeam', {}).get('abbrev', '')

                    # Match the game
                    if (away.lower() in away_team.lower() or away_team.lower() in away.lower()) and \
                       (home.lower() in home_team.lower() or home_team.lower() in home.lower()):
                        state = game.get('gameState', '')
                        if state == 'OFF' or state == 'FINAL':
                            away_score = game.get('awayTeam', {}).get('score', 0)
                            home_score = game.get('homeTeam', {}).get('score', 0)
                            return {
                                'away': away,
                                'home': home,
                                'away_score': away_score,
                                'home_score': home_score,
                                'winner': home if home_score > away_score else away
                            }
    except Exception as e:
        print(f"NHL API error: {e}")
    return None


def get_nba_game_result(date_str, team1, team2):
    """Fetch NBA game result from ESPN"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        espn_date = date_obj.strftime("%Y%m%d")

        url = f"{NBA_API_BASE}?dates={espn_date}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) == 2:
                    home = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]
                    away = competitors[1] if competitors[1].get('homeAway') == 'away' else competitors[0]

                    home_name = home.get('team', {}).get('displayName', '')
                    away_name = away.get('team', {}).get('displayName', '')

                    # Check if this is our game
                    if (team1.lower() in home_name.lower() or team1.lower() in away_name.lower()) and \
                       (team2.lower() in home_name.lower() or team2.lower() in away_name.lower()):
                        status = competition.get('status', {}).get('type', {}).get('completed', False)
                        if status:
                            home_score = int(home.get('score', 0))
                            away_score = int(away.get('score', 0))
                            winner = home_name if home_score > away_score else away_name
                            return {
                                'home': home_name,
                                'away': away_name,
                                'home_score': home_score,
                                'away_score': away_score,
                                'winner': winner
                            }
    except Exception as e:
        print(f"NBA API error: {e}")
    return None


def get_ncaa_game_result(date_str, team1, team2):
    """Fetch NCAA game result from ESPN"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        espn_date = date_obj.strftime("%Y%m%d")

        url = f"{NCAA_API_BASE}?dates={espn_date}&limit=300"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for event in data.get('events', []):
                competition = event.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])

                if len(competitors) == 2:
                    home = competitors[0] if competitors[0].get('homeAway') == 'home' else competitors[1]
                    away = competitors[1] if competitors[1].get('homeAway') == 'away' else competitors[0]

                    home_name = home.get('team', {}).get('displayName', '')
                    away_name = away.get('team', {}).get('displayName', '')

                    # Simplified team name matching - use key words
                    team1_clean = team1.replace(' Wildcats', '').replace(' Jayhawks', '').replace(' Blue Devils', '').replace(' Bulldogs', '').strip()
                    team2_clean = team2.replace(' Wildcats', '').replace(' Jayhawks', '').replace(' Blue Devils', '').replace(' Bulldogs', '').strip()

                    match1 = any(word.lower() in home_name.lower() or word.lower() in away_name.lower()
                                for word in team1_clean.split() if len(word) > 3)
                    match2 = any(word.lower() in home_name.lower() or word.lower() in away_name.lower()
                                for word in team2_clean.split() if len(word) > 3)

                    if match1 and match2:
                        status = competition.get('status', {}).get('type', {}).get('completed', False)
                        if status:
                            home_score = int(home.get('score', 0))
                            away_score = int(away.get('score', 0))
                            winner = home_name if home_score > away_score else away_name
                            margin = abs(home_score - away_score)

                            return {
                                'home': home_name,
                                'away': away_name,
                                'home_score': home_score,
                                'away_score': away_score,
                                'winner': winner,
                                'margin': margin
                            }
    except Exception as e:
        print(f"NCAA API error: {e}")
    return None


def get_soccer_game_result(date_str, home_team, away_team):
    """Fetch soccer game result"""
    headers = {'x-apisports-key': FOOTBALL_API_KEY}

    # Try multiple date formats since soccer dates can be tricky
    dates_to_try = [date_str]
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        dates_to_try.append((d - timedelta(days=1)).strftime("%Y-%m-%d"))
        dates_to_try.append((d + timedelta(days=1)).strftime("%Y-%m-%d"))
    except:
        pass

    for try_date in dates_to_try:
        try:
            url = f"{FOOTBALL_API_BASE}/fixtures"
            params = {'date': try_date}

            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for fixture in data.get('response', []):
                    teams = fixture.get('teams', {})
                    home = teams.get('home', {}).get('name', '')
                    away = teams.get('away', {}).get('name', '')

                    # Match teams - be flexible
                    home_match = any(word.lower() in home.lower() for word in home_team.split() if len(word) > 3)
                    away_match = any(word.lower() in away.lower() for word in away_team.split() if len(word) > 3)

                    if home_match and away_match:
                        status = fixture.get('fixture', {}).get('status', {}).get('short', '')
                        if status == 'FT':
                            goals = fixture.get('goals', {})
                            home_score = goals.get('home', 0) or 0
                            away_score = goals.get('away', 0) or 0
                            return {
                                'home': home,
                                'away': away,
                                'home_score': home_score,
                                'away_score': away_score,
                                'total': home_score + away_score,
                                'winner': 'home' if home_score > away_score else ('away' if away_score > home_score else 'draw')
                            }
        except Exception as e:
            continue
    return None


def resolve_bet(bet, result, pick):
    """Determine if bet won or lost based on result"""
    if result is None or not pick:
        return None

    bet_type = bet.get('bet_type', '').lower()
    bet_field = bet.get('bet', '').lower()
    winner = result.get('winner', '').lower()

    # Check pick against winner
    pick_lower = pick.lower()

    # Moneyline bets
    if 'moneyline' in bet_type or 'ml' in bet_type or 'ml' in bet_field:
        # Check if pick matches winner
        if pick_lower in winner or winner in pick_lower:
            return 'WIN'
        else:
            return 'LOSS'

    # Draw No Bet
    if 'draw no bet' in bet_field.lower():
        if result.get('winner') == 'draw':
            return 'PUSH'
        elif pick_lower in winner or winner in pick_lower:
            return 'WIN'
        else:
            return 'LOSS'

    # Win or Draw
    if 'win or draw' in bet_field.lower():
        if result.get('winner') == 'draw':
            return 'WIN'
        elif pick_lower in winner or winner in pick_lower:
            return 'WIN'
        else:
            return 'LOSS'

    # Spread bets (NCAA) - need the spread value
    if 'spread' in bet_type:
        # For now, skip spread bets - need the actual line
        return None

    return None


def calculate_profit(bet, result_str):
    """Calculate profit based on odds and result"""
    stake = bet.get('stake')
    if stake is None:
        stake = 25

    odds = bet.get('odds')
    if odds is None:
        odds = -110  # Default

    if result_str == 'WIN':
        if odds > 0:
            return stake * (odds / 100)
        else:
            return stake * (100 / abs(odds))
    elif result_str == 'LOSS':
        return -stake
    else:  # PUSH
        return 0


def main():
    print("=" * 80)
    print("RESOLVING PENDING BETS")
    print("=" * 80)

    bets = load_bet_history()

    # First, reset incorrectly resolved bets (those with actual_result but no proper pick matching)
    reset_count = 0
    for bet in bets:
        if bet.get('actual_result') and bet.get('result') == 'WIN':
            # Check if this was a bad resolution (no proper pick matching done)
            pick = extract_pick_from_bet(bet.get('bet'), bet.get('game', ''))
            if not pick:
                bet['result'] = 'PENDING'
                del bet['actual_result']
                if 'profit' in bet:
                    bet['profit'] = 0
                reset_count += 1

    if reset_count > 0:
        print(f"Reset {reset_count} incorrectly resolved bets")

    resolved_count = {'NHL': 0, 'NBA': 0, 'NCAA': 0, 'SOCCER': 0}
    win_count = {'NHL': 0, 'NBA': 0, 'NCAA': 0, 'SOCCER': 0}
    loss_count = {'NHL': 0, 'NBA': 0, 'NCAA': 0, 'SOCCER': 0}

    for i, bet in enumerate(bets):
        if bet.get('result') != 'PENDING':
            continue

        sport = bet.get('sport', '')
        date_str = bet.get('date', bet.get('game_date', ''))
        game = bet.get('game', '')
        bet_field = bet.get('bet', '')

        # Extract pick from bet field
        pick = extract_pick_from_bet(bet_field, game)

        if not pick:
            continue

        # Parse teams from game string
        if ' @ ' in game:
            parts = game.split(' @ ')
            away_team = parts[0].strip()
            home_team = parts[1].strip()
        elif ' vs ' in game.lower():
            parts = game.lower().split(' vs ')
            home_team = parts[0].strip()
            away_team = parts[1].strip()
        else:
            away_team = bet.get('away_team', '')
            home_team = bet.get('home_team', '')

        result = None

        if sport == 'NHL':
            result = get_nhl_game_result(date_str, away_team, home_team)
        elif sport == 'NBA':
            result = get_nba_game_result(date_str, away_team, home_team)
        elif sport == 'NCAA':
            result = get_ncaa_game_result(date_str, away_team, home_team)
        elif sport == 'SOCCER':
            result = get_soccer_game_result(date_str, home_team, away_team)

        if result:
            bet_result = resolve_bet(bet, result, pick)

            if bet_result:
                bet['result'] = bet_result
                bet['actual_result'] = result
                bet['profit'] = calculate_profit(bet, bet_result)

                resolved_count[sport] += 1
                if bet_result == 'WIN':
                    win_count[sport] += 1
                elif bet_result == 'LOSS':
                    loss_count[sport] += 1

                result_emoji = "✅" if bet_result == 'WIN' else "❌" if bet_result == 'LOSS' else "⏸️"
                print(f"{result_emoji} [{sport}] {date_str}: {game}")
                print(f"       Pick: {pick}")
                print(f"       Result: {result.get('away', '')} {result.get('away_score', 0)} - {result.get('home', '')} {result.get('home_score', 0)}")
                print(f"       Winner: {result.get('winner', 'N/A')}")
                print(f"       Bet: {bet_result} | Profit: ${bet['profit']:.2f}")
                print()

        time.sleep(0.2)  # Rate limiting

    # Save updated bets
    save_bet_history(bets)

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total_wins = 0
    total_losses = 0
    for sport in ['NHL', 'NBA', 'NCAA', 'SOCCER']:
        if resolved_count[sport] > 0:
            print(f"{sport}: Resolved {resolved_count[sport]} bets | {win_count[sport]}-{loss_count[sport]}")
            total_wins += win_count[sport]
            total_losses += loss_count[sport]

    print(f"\nTotal: {total_wins}-{total_losses}")
    print(f"\nBet history updated: {BET_HISTORY_PATH}")


if __name__ == "__main__":
    main()
