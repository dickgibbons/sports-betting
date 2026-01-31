#!/usr/bin/env python3
"""
Rebuild Performance Tracking from Scratch
Parses all daily reports and looks up actual game results
"""

import requests
from datetime import datetime, timedelta
import re
import csv
import time

# All picks extracted from daily reports
ALL_PICKS = [
    # Oct 27 - NBA
    {"date": "2025-10-27", "sport": "NBA", "game": "Boston Celtics @ New Orleans Pelicans", "bet": "New Orleans Pelicans ML", "confidence": "ELITE", "odds": -125},
    {"date": "2025-10-27", "sport": "NBA", "game": "Toronto Raptors @ San Antonio Spurs", "bet": "Toronto Raptors ML", "confidence": "ELITE", "odds": 180},
    {"date": "2025-10-27", "sport": "NBA", "game": "Portland Trail Blazers @ Los Angeles Lakers", "bet": "Portland Trail Blazers ML", "confidence": "ELITE", "odds": -144},
    {"date": "2025-10-27", "sport": "NBA", "game": "Cleveland Cavaliers @ Detroit Pistons", "bet": "Cleveland Cavaliers ML", "confidence": "ELITE", "odds": -142},
    {"date": "2025-10-27", "sport": "NBA", "game": "Phoenix Suns @ Utah Jazz", "bet": "Utah Jazz ML", "confidence": "ELITE", "odds": -118},
    {"date": "2025-10-27", "sport": "NBA", "game": "Orlando Magic @ Philadelphia 76ers", "bet": "Philadelphia 76ers ML", "confidence": "HIGH", "odds": 180},
    {"date": "2025-10-27", "sport": "NBA", "game": "Atlanta Hawks @ Chicago Bulls", "bet": "Chicago Bulls ML", "confidence": "HIGH", "odds": 110},

    # Oct 28 - NHL and NBA
    {"date": "2025-10-28", "sport": "NHL", "game": "PIT @ PHI", "bet": "PHI ML", "confidence": "ELITE", "odds": -110},
    {"date": "2025-10-28", "sport": "NHL", "game": "NYI @ BOS", "bet": "NYI ML", "confidence": "ELITE", "odds": 150},
    {"date": "2025-10-28", "sport": "NHL", "game": "DET @ STL", "bet": "DET ML", "confidence": "ELITE", "odds": -110},
    {"date": "2025-10-28", "sport": "NBA", "game": "Philadelphia 76ers @ Washington Wizards", "bet": "Washington Wizards ML", "confidence": "ELITE", "odds": 142},
    {"date": "2025-10-28", "sport": "NBA", "game": "Sacramento Kings @ Oklahoma City Thunder", "bet": "Sacramento Kings ML", "confidence": "ELITE", "odds": 380},
    {"date": "2025-10-28", "sport": "NHL", "game": "OTT @ CHI", "bet": "CHI ML", "confidence": "HIGH", "odds": -110},
    {"date": "2025-10-28", "sport": "NHL", "game": "VGK @ CAR", "bet": "CAR ML", "confidence": "HIGH", "odds": -130},
    {"date": "2025-10-28", "sport": "NHL", "game": "UTA @ EDM", "bet": "UTA ML", "confidence": "HIGH", "odds": 200},
    {"date": "2025-10-28", "sport": "NHL", "game": "LAK @ SJS", "bet": "SJS ML", "confidence": "HIGH", "odds": 200},
    {"date": "2025-10-28", "sport": "NHL", "game": "TBL @ NSH", "bet": "TBL ML", "confidence": "LOW", "odds": -120},

    # Oct 29 - NBA and NHL
    {"date": "2025-10-29", "sport": "NBA", "game": "Sacramento Kings @ Chicago Bulls", "bet": "Chicago Bulls ML", "confidence": "ELITE", "odds": -196},
    {"date": "2025-10-29", "sport": "NBA", "game": "Indiana Pacers @ Dallas Mavericks", "bet": "Indiana Pacers ML", "confidence": "ELITE", "odds": 225},
    {"date": "2025-10-29", "sport": "NBA", "game": "Portland Trail Blazers @ Utah Jazz", "bet": "Utah Jazz ML", "confidence": "ELITE", "odds": 110},
    {"date": "2025-10-29", "sport": "NBA", "game": "Orlando Magic @ Detroit Pistons", "bet": "Orlando Magic ML", "confidence": "HIGH", "odds": -116},
    {"date": "2025-10-29", "sport": "NBA", "game": "Los Angeles Lakers @ Minnesota Timberwolves", "bet": "Los Angeles Lakers ML", "confidence": "HIGH", "odds": 215},
    {"date": "2025-10-29", "sport": "NHL", "game": "TOR @ CBJ", "bet": "CBJ ML", "confidence": "LOW", "odds": 150},

    # Oct 30 - NBA
    {"date": "2025-10-30", "sport": "NBA", "game": "Washington Wizards @ Oklahoma City Thunder", "bet": "Washington Wizards ML", "confidence": "HIGH", "odds": 750},
    {"date": "2025-10-30", "sport": "NBA", "game": "Orlando Magic @ Charlotte Hornets", "bet": "Charlotte Hornets ML", "confidence": "MEDIUM", "odds": 128},
    {"date": "2025-10-30", "sport": "NBA", "game": "Golden State Warriors @ Milwaukee Bucks", "bet": "Milwaukee Bucks ML", "confidence": "HIGH", "odds": 124},

    # Nov 2 - NHL and NBA
    {"date": "2025-11-02", "sport": "NHL", "game": "CGY @ PHI", "bet": "PHI ML", "confidence": "ELITE", "odds": -110},
    {"date": "2025-11-02", "sport": "NHL", "game": "NJD @ ANA", "bet": "ANA ML", "confidence": "ELITE", "odds": 120},
    {"date": "2025-11-02", "sport": "NHL", "game": "CBJ @ NYI", "bet": "CBJ ML", "confidence": "HIGH", "odds": 150},
    {"date": "2025-11-02", "sport": "NHL", "game": "DET @ SJS", "bet": "DET ML", "confidence": "HIGH", "odds": -150},
    {"date": "2025-11-02", "sport": "NBA", "game": "Utah Jazz @ Charlotte Hornets", "bet": "Utah Jazz ML", "confidence": "HIGH", "odds": 100},
    {"date": "2025-11-02", "sport": "NBA", "game": "Philadelphia 76ers @ Brooklyn Nets", "bet": "Brooklyn Nets ML", "confidence": "MEDIUM", "odds": 170},

    # Nov 3 - NBA and NHL
    {"date": "2025-11-03", "sport": "NBA", "game": "Los Angeles Lakers @ Portland Trail Blazers", "bet": "Portland Trail Blazers ML", "confidence": "ELITE", "odds": -142},
    {"date": "2025-11-03", "sport": "NBA", "game": "Utah Jazz @ Boston Celtics", "bet": "Utah Jazz ML", "confidence": "HIGH", "odds": 370},
    {"date": "2025-11-03", "sport": "NBA", "game": "Washington Wizards @ New York Knicks", "bet": "Washington Wizards ML", "confidence": "HIGH", "odds": 500},
    {"date": "2025-11-03", "sport": "NBA", "game": "Miami Heat @ LA Clippers", "bet": "LA Clippers ML", "confidence": "MEDIUM", "odds": -130},
    {"date": "2025-11-03", "sport": "NHL", "game": "PIT @ TOR", "bet": "TOR ML", "confidence": "MEDIUM", "odds": -150},

    # Nov 4 - NHL and NBA
    {"date": "2025-11-04", "sport": "NHL", "game": "NSH @ MIN", "bet": "MIN ML", "confidence": "ELITE", "odds": -140},
    {"date": "2025-11-04", "sport": "NHL", "game": "DET @ VGK", "bet": "VGK ML", "confidence": "HIGH", "odds": -180},
    {"date": "2025-11-04", "sport": "NHL", "game": "EDM @ DAL", "bet": "DAL ML", "confidence": "HIGH", "odds": -110},
    {"date": "2025-11-04", "sport": "NBA", "game": "Charlotte Hornets @ New Orleans Pelicans", "bet": "New Orleans Pelicans ML", "confidence": "HIGH", "odds": -130},
    {"date": "2025-11-04", "sport": "NBA", "game": "Orlando Magic @ Atlanta Hawks", "bet": "Atlanta Hawks ML", "confidence": "MEDIUM", "odds": 146},
    {"date": "2025-11-04", "sport": "NHL", "game": "PHI @ MTL", "bet": "MTL ML", "confidence": "LOW", "odds": 110},

    # Nov 5 - NBA and NHL
    {"date": "2025-11-05", "sport": "NBA", "game": "Golden State Warriors @ Sacramento Kings", "bet": "Sacramento Kings ML", "confidence": "HIGH", "odds": -142},
    {"date": "2025-11-05", "sport": "NBA", "game": "Minnesota Timberwolves @ New York Knicks", "bet": "Minnesota Timberwolves ML", "confidence": "HIGH", "odds": 154},
    {"date": "2025-11-05", "sport": "NBA", "game": "San Antonio Spurs @ Los Angeles Lakers", "bet": "San Antonio Spurs ML", "confidence": "HIGH", "odds": 114},
    {"date": "2025-11-05", "sport": "NBA", "game": "Oklahoma City Thunder @ Portland Trail Blazers", "bet": "Portland Trail Blazers ML", "confidence": "HIGH", "odds": 180},
    {"date": "2025-11-05", "sport": "NHL", "game": "UTA @ TOR", "bet": "TOR ML", "confidence": "LOW", "odds": -200},
    {"date": "2025-11-05", "sport": "NHL", "game": "STL @ WSH", "bet": "WSH ML", "confidence": "LOW", "odds": -150},

    # Nov 6 - NHL and NBA
    {"date": "2025-11-06", "sport": "NHL", "game": "WSH @ PIT", "bet": "PIT ML", "confidence": "ELITE", "odds": -130},
    {"date": "2025-11-06", "sport": "NBA", "game": "LA Clippers @ Phoenix Suns", "bet": "Phoenix Suns ML", "confidence": "HIGH", "odds": -180},
    {"date": "2025-11-06", "sport": "NHL", "game": "STL @ BUF", "bet": "BUF ML", "confidence": "LOW", "odds": -120},
    {"date": "2025-11-06", "sport": "NHL", "game": "PHI @ NSH", "bet": "PHI ML", "confidence": "LOW", "odds": 110},
    {"date": "2025-11-06", "sport": "NHL", "game": "OTT @ BOS", "bet": "OTT ML", "confidence": "LOW", "odds": 180},
    {"date": "2025-11-06", "sport": "NHL", "game": "MTL @ NJD", "bet": "NJD ML", "confidence": "LOW", "odds": -180},

    # Nov 7 - NHL and NBA
    {"date": "2025-11-07", "sport": "NHL", "game": "MIN @ NYI", "bet": "NYI ML", "confidence": "HIGH", "odds": 120},
    {"date": "2025-11-07", "sport": "NBA", "game": "Oklahoma City Thunder @ Sacramento Kings", "bet": "Sacramento Kings ML", "confidence": "HIGH", "odds": 440},

    # Nov 8 - NBA and NHL
    {"date": "2025-11-08", "sport": "NBA", "game": "Indiana Pacers @ Denver Nuggets", "bet": "Indiana Pacers ML", "confidence": "ELITE", "odds": 460},
    {"date": "2025-11-08", "sport": "NBA", "game": "Portland Trail Blazers @ Miami Heat", "bet": "Portland Trail Blazers ML", "confidence": "ELITE", "odds": -146},
    {"date": "2025-11-08", "sport": "NBA", "game": "New Orleans Pelicans @ San Antonio Spurs", "bet": "New Orleans Pelicans ML", "confidence": "ELITE", "odds": 425},
    {"date": "2025-11-08", "sport": "NHL", "game": "NYI @ NYR", "bet": "NYR ML", "confidence": "HIGH", "odds": -180},
    {"date": "2025-11-08", "sport": "NBA", "game": "Chicago Bulls @ Cleveland Cavaliers", "bet": "Chicago Bulls ML", "confidence": "HIGH", "odds": 265},

    # Nov 10 - NBA
    {"date": "2025-11-10", "sport": "NBA", "game": "Washington Wizards @ Detroit Pistons", "bet": "Washington Wizards ML", "confidence": "HIGH", "odds": 470},

    # Nov 13 - NBA
    {"date": "2025-11-13", "sport": "NBA", "game": "Indiana Pacers @ Phoenix Suns", "bet": "Indiana Pacers ML", "confidence": "ELITE", "odds": 152},
    {"date": "2025-11-13", "sport": "NBA", "game": "Toronto Raptors @ Cleveland Cavaliers", "bet": "Toronto Raptors ML", "confidence": "ELITE", "odds": 240},

    # Nov 14 - NBA
    {"date": "2025-11-14", "sport": "NBA", "game": "Brooklyn Nets @ Orlando Magic", "bet": "Brooklyn Nets ML", "confidence": "ELITE", "odds": 200},
    {"date": "2025-11-14", "sport": "NBA", "game": "Charlotte Hornets @ Milwaukee Bucks", "bet": "Charlotte Hornets ML", "confidence": "ELITE", "odds": 350},
    {"date": "2025-11-14", "sport": "NBA", "game": "Portland Trail Blazers @ Houston Rockets", "bet": "Portland Trail Blazers ML", "confidence": "HIGH", "odds": 180},
    {"date": "2025-11-14", "sport": "NBA", "game": "Sacramento Kings @ Minnesota Timberwolves", "bet": "Sacramento Kings ML", "confidence": "MEDIUM", "odds": 200},
    {"date": "2025-11-14", "sport": "NBA", "game": "Miami Heat @ New York Knicks", "bet": "Miami Heat ML", "confidence": "LOW", "odds": 190},

    # Nov 15 - NBA
    {"date": "2025-11-15", "sport": "NBA", "game": "Memphis Grizzlies @ Cleveland Cavaliers", "bet": "Memphis Grizzlies ML", "confidence": "HIGH", "odds": 360},

    # Nov 16 - NBA
    {"date": "2025-11-16", "sport": "NBA", "game": "Brooklyn Nets @ San Antonio Spurs", "bet": "Brooklyn Nets ML", "confidence": "HIGH", "odds": -110},
    {"date": "2025-11-16", "sport": "NBA", "game": "Orlando Magic @ Houston Rockets", "bet": "Orlando Magic ML", "confidence": "LOW", "odds": -110},
    {"date": "2025-11-16", "sport": "NBA", "game": "Chicago Bulls @ Phoenix Suns", "bet": "Chicago Bulls ML", "confidence": "LOW", "odds": 250},

    # Nov 17 - NBA and NHL
    {"date": "2025-11-17", "sport": "NBA", "game": "Dallas Mavericks @ Minnesota Timberwolves", "bet": "Dallas Mavericks ML", "confidence": "ELITE", "odds": 600},
    {"date": "2025-11-17", "sport": "NBA", "game": "LA Clippers @ Philadelphia 76ers", "bet": "Philadelphia 76ers ML", "confidence": "ELITE", "odds": 110},
    {"date": "2025-11-17", "sport": "NHL", "game": "LAK @ WSH", "bet": "WSH ML", "confidence": "MEDIUM", "odds": -130},
    {"date": "2025-11-17", "sport": "NHL", "game": "CAR @ BOS", "bet": "BOS ML", "confidence": "LOW", "odds": -140},
    {"date": "2025-11-17", "sport": "NHL", "game": "VAN @ FLA", "bet": "FLA ML", "confidence": "LOW", "odds": -160},

    # Nov 18 - NHL and NBA
    {"date": "2025-11-18", "sport": "NHL", "game": "CBJ @ WPG", "bet": "WPG ML", "confidence": "ELITE", "odds": -250},
    {"date": "2025-11-18", "sport": "NBA", "game": "Detroit Pistons @ Atlanta Hawks", "bet": "Atlanta Hawks ML", "confidence": "HIGH", "odds": -106},
    {"date": "2025-11-18", "sport": "NHL", "game": "NYI @ DAL", "bet": "DAL ML", "confidence": "MEDIUM", "odds": -180},
    {"date": "2025-11-18", "sport": "NBA", "game": "Golden State Warriors @ Orlando Magic", "bet": "Orlando Magic ML", "confidence": "MEDIUM", "odds": 140},
    {"date": "2025-11-18", "sport": "NHL", "game": "SEA @ DET", "bet": "SEA ML", "confidence": "LOW", "odds": 110},
    {"date": "2025-11-18", "sport": "NHL", "game": "NJD @ TBL", "bet": "NJD ML", "confidence": "LOW", "odds": 130},
    {"date": "2025-11-18", "sport": "NHL", "game": "NYR @ VGK", "bet": "NYR ML", "confidence": "LOW", "odds": 140},
    {"date": "2025-11-18", "sport": "NHL", "game": "UTA @ SJS", "bet": "SJS ML", "confidence": "LOW", "odds": 160},

    # Nov 19 - NBA
    {"date": "2025-11-19", "sport": "NBA", "game": "Chicago Bulls @ Portland Trail Blazers", "bet": "Chicago Bulls ML", "confidence": "ELITE", "odds": -142},

    # Nov 23 - NBA and NHL
    {"date": "2025-11-23", "sport": "NBA", "game": "Charlotte Hornets @ Atlanta Hawks", "bet": "Charlotte Hornets ML", "confidence": "ELITE", "odds": 215},
    {"date": "2025-11-23", "sport": "NBA", "game": "Orlando Magic @ Boston Celtics", "bet": "Boston Celtics ML", "confidence": "ELITE", "odds": -186},
    {"date": "2025-11-23", "sport": "NBA", "game": "LA Clippers @ Cleveland Cavaliers", "bet": "Cleveland Cavaliers ML", "confidence": "ELITE", "odds": -250},
    {"date": "2025-11-23", "sport": "NHL", "game": "CGY @ VAN", "bet": "VAN ML", "confidence": "ELITE", "odds": -160},
    {"date": "2025-11-23", "sport": "NHL", "game": "SEA @ NYI", "bet": "SEA ML", "confidence": "HIGH", "odds": 110},
    {"date": "2025-11-23", "sport": "NHL", "game": "CAR @ BUF", "bet": "BUF ML", "confidence": "MEDIUM", "odds": 150},
    {"date": "2025-11-23", "sport": "NHL", "game": "COL @ CHI", "bet": "COL ML", "confidence": "LOW", "odds": -280},
    {"date": "2025-11-23", "sport": "NHL", "game": "BOS @ SJS", "bet": "BOS ML", "confidence": "LOW", "odds": -280},

    # Nov 25 - NCAA and NBA
    {"date": "2025-11-25", "sport": "NCAA", "game": "NC State Wolfpack @ Boise State Broncos", "bet": "Boise State Broncos ML", "confidence": "ELITE", "odds": 245},
    {"date": "2025-11-25", "sport": "NCAA", "game": "St. John's Red Storm @ Baylor Bears", "bet": "Baylor Bears ML", "confidence": "ELITE", "odds": 180},
    {"date": "2025-11-25", "sport": "NBA", "game": "LA Clippers @ Los Angeles Lakers", "bet": "Los Angeles Lakers ML", "confidence": "ELITE", "odds": -150},
    {"date": "2025-11-25", "sport": "NCAA", "game": "Michigan Wolverines @ Auburn Tigers", "bet": "Auburn Tigers ML", "confidence": "HIGH", "odds": 145},
    {"date": "2025-11-25", "sport": "NBA", "game": "Atlanta Hawks @ Washington Wizards", "bet": "Washington Wizards ML", "confidence": "HIGH", "odds": 350},
    {"date": "2025-11-25", "sport": "NBA", "game": "Orlando Magic @ Philadelphia 76ers", "bet": "Philadelphia 76ers ML", "confidence": "HIGH", "odds": 102},
    {"date": "2025-11-25", "sport": "NCAA", "game": "Iowa State Cyclones @ Creighton Bluejays", "bet": "Creighton Bluejays ML", "confidence": "HIGH", "odds": 340},
    {"date": "2025-11-25", "sport": "NCAA", "game": "UNLV Rebels @ Alabama Crimson Tide", "bet": "UNLV Rebels ML", "confidence": "HIGH", "odds": 800},

    # Nov 28 - NCAA and NHL
    {"date": "2025-11-28", "sport": "NCAA", "game": "BYU Cougars @ Dayton Flyers", "bet": "Dayton Flyers ML", "confidence": "HIGH", "odds": 390},
    {"date": "2025-11-28", "sport": "NHL", "game": "OTT @ STL", "bet": "STL ML", "confidence": "MEDIUM", "odds": -130},
    {"date": "2025-11-28", "sport": "NHL", "game": "UTA @ DAL", "bet": "UTA ML", "confidence": "LOW", "odds": 200},
    {"date": "2025-11-28", "sport": "NHL", "game": "LAK @ ANA", "bet": "LAK ML", "confidence": "LOW", "odds": -130},

    # Dec 1 - NCAA
    {"date": "2025-12-01", "sport": "NCAA", "game": "Temple Owls @ Villanova Wildcats", "bet": "Villanova Wildcats -12.5", "confidence": "MEDIUM", "odds": -110},
    {"date": "2025-12-01", "sport": "NCAA", "game": "Bowling Green Falcons @ Kansas State Wildcats", "bet": "Kansas State Wildcats -12.5", "confidence": "MEDIUM", "odds": -110},
]

def get_nhl_result(date_str, home_abbrev, away_abbrev):
    """Get NHL game result from API"""
    try:
        url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for day in data.get('gameWeek', []):
                for game in day.get('games', []):
                    h = game.get('homeTeam', {}).get('abbrev', '')
                    a = game.get('awayTeam', {}).get('abbrev', '')
                    if (h == home_abbrev or a == away_abbrev) or (h == away_abbrev or a == home_abbrev):
                        home_score = game.get('homeTeam', {}).get('score')
                        away_score = game.get('awayTeam', {}).get('score')
                        if home_score is not None and away_score is not None:
                            winner = h if home_score > away_score else a
                            return {'home': h, 'away': a, 'home_score': home_score, 'away_score': away_score, 'winner': winner}
    except Exception as e:
        print(f"NHL API error: {e}")
    return None

def get_nba_result(date_str, team1, team2):
    """Get NBA game result from ESPN API"""
    try:
        espn_date = date_str.replace('-', '')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={espn_date}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for event in data.get('events', []):
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) >= 2:
                    t1 = competitors[0].get('team', {}).get('displayName', '')
                    t2 = competitors[1].get('team', {}).get('displayName', '')
                    s1 = int(competitors[0].get('score', 0))
                    s2 = int(competitors[1].get('score', 0))

                    if (team1 in t1 or team1 in t2 or team2 in t1 or team2 in t2):
                        winner = t1 if s1 > s2 else t2
                        return {'team1': t1, 'team2': t2, 'score1': s1, 'score2': s2, 'winner': winner}
    except Exception as e:
        print(f"NBA API error: {e}")
    return None

def get_ncaa_result(date_str, team1, team2):
    """Get NCAA game result from ESPN API"""
    try:
        espn_date = date_str.replace('-', '')
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={espn_date}&limit=300"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for event in data.get('events', []):
                competitors = event.get('competitions', [{}])[0].get('competitors', [])
                if len(competitors) >= 2:
                    t1 = competitors[0].get('team', {}).get('displayName', '')
                    t2 = competitors[1].get('team', {}).get('displayName', '')
                    s1 = int(competitors[0].get('score', 0) or 0)
                    s2 = int(competitors[1].get('score', 0) or 0)

                    # Match team names loosely
                    t1_words = set(team1.lower().split())
                    t2_words = set(team2.lower().split())
                    match1_words = set(t1.lower().split())
                    match2_words = set(t2.lower().split())

                    if (t1_words & match1_words or t1_words & match2_words or
                        t2_words & match1_words or t2_words & match2_words):
                        home_away = {c.get('homeAway'): c for c in competitors}
                        home = home_away.get('home', {})
                        away = home_away.get('away', {})
                        home_name = home.get('team', {}).get('displayName', '')
                        away_name = away.get('team', {}).get('displayName', '')
                        home_score = int(home.get('score', 0) or 0)
                        away_score = int(away.get('score', 0) or 0)

                        if home_score > 0 or away_score > 0:
                            return {
                                'home': home_name,
                                'away': away_name,
                                'home_score': home_score,
                                'away_score': away_score,
                                'winner': home_name if home_score > away_score else away_name,
                                'margin': abs(home_score - away_score)
                            }
    except Exception as e:
        print(f"NCAA API error: {e}")
    return None

def calculate_profit(odds, stake=25):
    """Calculate profit from American odds"""
    if odds > 0:
        return stake * (odds / 100)
    else:
        return stake * (100 / abs(odds))

def determine_bet_result(pick, result):
    """Determine if a bet won or lost"""
    if not result:
        return "PENDING"

    bet = pick['bet']
    sport = pick['sport']

    # Extract team from bet
    if " ML" in bet:
        team_bet = bet.replace(" ML", "")
    elif " -" in bet:  # Spread bet
        team_bet = bet.split(" -")[0]
        spread = float(bet.split(" -")[1])
        # For spread bets, need to check margin
        if 'margin' in result:
            margin = result['margin']
            if team_bet in result.get('winner', ''):
                return "WIN" if margin > spread else "LOSS"
            else:
                return "LOSS"
        return "PENDING"
    else:
        team_bet = bet

    winner = result.get('winner', '')

    # Check if our team won
    if team_bet in winner or any(word in winner for word in team_bet.split()):
        return "WIN"
    else:
        return "LOSS"

def main():
    print("=" * 80)
    print("REBUILDING PERFORMANCE TRACKING FROM SCRATCH")
    print("=" * 80)

    results = {
        'NHL': {'wins': 0, 'losses': 0, 'pending': 0, 'profit': 0},
        'NBA': {'wins': 0, 'losses': 0, 'pending': 0, 'profit': 0},
        'NCAA': {'wins': 0, 'losses': 0, 'pending': 0, 'profit': 0},
    }

    detailed_results = []

    for pick in ALL_PICKS:
        sport = pick['sport']
        date = pick['date']
        game = pick['game']
        bet = pick['bet']
        odds = pick['odds']
        confidence = pick['confidence']

        # Look up result based on sport
        result = None
        if sport == 'NHL':
            # Parse teams from game string like "PIT @ PHI"
            parts = game.split(' @ ')
            if len(parts) == 2:
                result = get_nhl_result(date, parts[1].strip(), parts[0].strip())
        elif sport == 'NBA':
            # Parse teams
            parts = game.split(' @ ')
            if len(parts) == 2:
                result = get_nba_result(date, parts[0].strip().split()[-1], parts[1].strip().split()[-1])
        elif sport == 'NCAA':
            parts = game.split(' @ ')
            if len(parts) == 2:
                result = get_ncaa_result(date, parts[0].strip(), parts[1].strip())

        bet_result = determine_bet_result(pick, result)

        profit = 0
        if bet_result == "WIN":
            results[sport]['wins'] += 1
            profit = calculate_profit(odds)
            results[sport]['profit'] += profit
        elif bet_result == "LOSS":
            results[sport]['losses'] += 1
            profit = -25
            results[sport]['profit'] += profit
        else:
            results[sport]['pending'] += 1

        detailed_results.append({
            'date': date,
            'sport': sport,
            'game': game,
            'bet': bet,
            'odds': odds,
            'confidence': confidence,
            'result': bet_result,
            'profit': profit
        })

        print(f"{date} | {sport} | {game} | {bet} | {bet_result} | ${profit:+.2f}")
        time.sleep(0.1)  # Rate limiting

    print("\n" + "=" * 80)
    print("SUMMARY BY SPORT")
    print("=" * 80)

    total_wins = 0
    total_losses = 0
    total_profit = 0

    for sport, stats in results.items():
        total = stats['wins'] + stats['losses']
        win_pct = (stats['wins'] / total * 100) if total > 0 else 0
        print(f"\n{sport}:")
        print(f"  Record: {stats['wins']}-{stats['losses']} ({win_pct:.1f}%)")
        print(f"  Pending: {stats['pending']}")
        print(f"  Profit: ${stats['profit']:+.2f}")
        total_wins += stats['wins']
        total_losses += stats['losses']
        total_profit += stats['profit']

    print("\n" + "=" * 80)
    print("OVERALL:")
    overall_pct = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    print(f"  Record: {total_wins}-{total_losses} ({overall_pct:.1f}%)")
    print(f"  Total Profit: ${total_profit:+.2f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
