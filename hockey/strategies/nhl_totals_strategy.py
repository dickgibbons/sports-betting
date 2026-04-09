#!/usr/bin/env python3
"""
NHL Full Game Totals Strategy

Based on analysis of 828 NHL games (2025-26 season):
- Combined team avg > 13 goals → Over 6.5: 70.0% hit rate (+17.6% edge)
- Both teams avg < 5.9 → Under 5.5: 62.9% hit rate (+10.5% edge)
- Both teams avg > 6.3 → Over 5.5: 61.3% hit rate (+8.9% edge)

Usage: python nhl_totals_strategy.py [YYYY-MM-DD]
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
BASE_URL = "https://v1.hockey.api-sports.io"

# Strategy thresholds (based on backtesting)
STRATEGIES = {
    'OVER_6_5_COMBINED': {
        'name': 'Over 6.5 (High Combined)',
        'description': 'Both teams combined avg > 13 goals/game',
        'threshold': 13.0,
        'line': 6.5,
        'direction': 'over',
        'historical_win_pct': 70.0,
        'edge': 17.6,
        'min_confidence': 65
    },
    'UNDER_5_5_BOTH_LOW': {
        'name': 'Under 5.5 (Both Low)',
        'description': 'Both teams avg < 5.9 goals/game',
        'threshold': 5.9,
        'line': 5.5,
        'direction': 'under',
        'historical_win_pct': 62.9,
        'edge': 10.5,
        'min_confidence': 60
    },
    'OVER_5_5_BOTH_HIGH': {
        'name': 'Over 5.5 (Both High)',
        'description': 'Both teams avg > 6.3 goals/game',
        'threshold': 6.3,
        'line': 5.5,
        'direction': 'over',
        'historical_win_pct': 61.3,
        'edge': 8.9,
        'min_confidence': 58
    }
}


def fetch_team_stats(season=2025):
    """Fetch and calculate team total goals statistics."""
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/games"
    params = {"league": 57, "season": season}

    response = requests.get(url, headers=headers, params=params, timeout=60)
    if response.status_code != 200:
        print(f"Error fetching games: {response.status_code}")
        return {}

    games = response.json().get('response', [])
    completed = [g for g in games if g.get('status', {}).get('short') in ['FT', 'AOT', 'AP']]

    team_stats = defaultdict(lambda: {
        'games': 0,
        'total_goals': 0,
        'goals_for': 0,
        'goals_against': 0,
        'overs_5_5': 0,
        'overs_6_5': 0,
        'last_10_totals': []
    })

    # Sort by date to get recent games
    completed.sort(key=lambda x: x.get('date', ''), reverse=True)

    for g in completed:
        home = g.get('teams', {}).get('home', {}).get('name', '')
        away = g.get('teams', {}).get('away', {}).get('name', '')
        home_score = g.get('scores', {}).get('home', 0) or 0
        away_score = g.get('scores', {}).get('away', 0) or 0
        total = home_score + away_score

        for team, gf, ga in [(home, home_score, away_score), (away, away_score, home_score)]:
            team_stats[team]['games'] += 1
            team_stats[team]['total_goals'] += total
            team_stats[team]['goals_for'] += gf
            team_stats[team]['goals_against'] += ga
            if total > 5.5:
                team_stats[team]['overs_5_5'] += 1
            if total > 6.5:
                team_stats[team]['overs_6_5'] += 1
            if len(team_stats[team]['last_10_totals']) < 10:
                team_stats[team]['last_10_totals'].append(total)

    # Calculate averages
    for team, stats in team_stats.items():
        if stats['games'] > 0:
            stats['avg_total'] = stats['total_goals'] / stats['games']
            stats['avg_for'] = stats['goals_for'] / stats['games']
            stats['avg_against'] = stats['goals_against'] / stats['games']
            stats['over_5_5_pct'] = 100 * stats['overs_5_5'] / stats['games']
            stats['over_6_5_pct'] = 100 * stats['overs_6_5'] / stats['games']
            if stats['last_10_totals']:
                stats['last_10_avg'] = sum(stats['last_10_totals']) / len(stats['last_10_totals'])

    return dict(team_stats)


def fetch_todays_games(date_str, season=2025):
    """Fetch NHL games for a specific date."""
    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/games"
    params = {"league": 57, "season": season, "date": date_str}

    response = requests.get(url, headers=headers, params=params, timeout=60)
    if response.status_code != 200:
        return []

    games = response.json().get('response', [])
    # Filter to scheduled games only
    return [g for g in games if g.get('status', {}).get('short') == 'NS']


def analyze_matchup(home_team, away_team, team_stats):
    """Analyze a matchup and return betting recommendations."""
    if home_team not in team_stats or away_team not in team_stats:
        return []

    home = team_stats[home_team]
    away = team_stats[away_team]

    recommendations = []

    # Check each strategy
    combined_avg = home['avg_total'] + away['avg_total']

    # Strategy 1: Over 6.5 when combined avg > 13
    if combined_avg > STRATEGIES['OVER_6_5_COMBINED']['threshold']:
        confidence = min(95, 65 + (combined_avg - 13) * 10)
        recommendations.append({
            'strategy': 'OVER_6_5_COMBINED',
            'bet': f"Over 6.5",
            'line': 6.5,
            'direction': 'over',
            'confidence': round(confidence, 1),
            'reasoning': f"Combined avg: {combined_avg:.2f} (threshold: 13.0)",
            'home_avg': home['avg_total'],
            'away_avg': away['avg_total'],
            'historical_win_pct': 70.0,
            'edge': '+17.6%'
        })

    # Strategy 2: Under 5.5 when both teams avg < 5.9
    if home['avg_total'] < STRATEGIES['UNDER_5_5_BOTH_LOW']['threshold'] and \
       away['avg_total'] < STRATEGIES['UNDER_5_5_BOTH_LOW']['threshold']:
        avg_diff = STRATEGIES['UNDER_5_5_BOTH_LOW']['threshold'] - max(home['avg_total'], away['avg_total'])
        confidence = min(95, 60 + avg_diff * 20)
        recommendations.append({
            'strategy': 'UNDER_5_5_BOTH_LOW',
            'bet': f"Under 5.5",
            'line': 5.5,
            'direction': 'under',
            'confidence': round(confidence, 1),
            'reasoning': f"Both teams avg < 5.9 ({home['avg_total']:.2f}, {away['avg_total']:.2f})",
            'home_avg': home['avg_total'],
            'away_avg': away['avg_total'],
            'historical_win_pct': 62.9,
            'edge': '+10.5%'
        })

    # Strategy 3: Over 5.5 when both teams avg > 6.3
    if home['avg_total'] > STRATEGIES['OVER_5_5_BOTH_HIGH']['threshold'] and \
       away['avg_total'] > STRATEGIES['OVER_5_5_BOTH_HIGH']['threshold']:
        min_avg = min(home['avg_total'], away['avg_total'])
        confidence = min(95, 58 + (min_avg - 6.3) * 30)
        recommendations.append({
            'strategy': 'OVER_5_5_BOTH_HIGH',
            'bet': f"Over 5.5",
            'line': 5.5,
            'direction': 'over',
            'confidence': round(confidence, 1),
            'reasoning': f"Both teams avg > 6.3 ({home['avg_total']:.2f}, {away['avg_total']:.2f})",
            'home_avg': home['avg_total'],
            'away_avg': away['avg_total'],
            'historical_win_pct': 61.3,
            'edge': '+8.9%'
        })

    return recommendations


def generate_daily_picks(date_str=None):
    """Generate NHL totals picks for a specific date."""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')

    print(f"\n{'='*70}")
    print(f"NHL FULL GAME TOTALS STRATEGY - {date_str}")
    print(f"{'='*70}")

    # Fetch team stats
    print("\nLoading team statistics...")
    team_stats = fetch_team_stats()
    print(f"Loaded stats for {len(team_stats)} teams")

    # Fetch today's games
    print(f"\nFetching games for {date_str}...")
    games = fetch_todays_games(date_str)
    print(f"Found {len(games)} scheduled games")

    if not games:
        print("\nNo NHL games scheduled for this date.")
        return []

    # Analyze each game
    all_picks = []

    print(f"\n{'='*70}")
    print("ANALYSIS")
    print(f"{'='*70}")

    for game in games:
        home = game.get('teams', {}).get('home', {}).get('name', '')
        away = game.get('teams', {}).get('away', {}).get('name', '')
        game_time = game.get('time', '')

        print(f"\n{away} @ {home}")

        if home in team_stats and away in team_stats:
            home_avg = team_stats[home]['avg_total']
            away_avg = team_stats[away]['avg_total']
            combined = home_avg + away_avg
            print(f"  {home}: {home_avg:.2f} avg total | {away}: {away_avg:.2f} avg total")
            print(f"  Combined: {combined:.2f}")

        recommendations = analyze_matchup(home, away, team_stats)

        if recommendations:
            for rec in recommendations:
                pick = {
                    'date': date_str,
                    'game': f"{away} @ {home}",
                    'home_team': home,
                    'away_team': away,
                    **rec
                }
                all_picks.append(pick)
                print(f"  ✅ {rec['bet']} ({rec['confidence']:.1f}% conf)")
                print(f"     {rec['reasoning']}")
                print(f"     Historical: {rec['historical_win_pct']}% win rate, {rec['edge']} edge")
        else:
            print(f"  ❌ No qualifying bets")

    # Sort by confidence
    all_picks.sort(key=lambda x: x['confidence'], reverse=True)

    # Summary
    print(f"\n{'='*70}")
    print("RECOMMENDED PICKS")
    print(f"{'='*70}")

    if all_picks:
        for i, pick in enumerate(all_picks, 1):
            print(f"\n#{i} {pick['game']}")
            print(f"   BET: {pick['bet']}")
            print(f"   Confidence: {pick['confidence']:.1f}%")
            print(f"   Strategy: {STRATEGIES[pick['strategy']]['name']}")
            print(f"   Historical Win Rate: {pick['historical_win_pct']}%")
    else:
        print("\nNo qualifying picks for today.")

    # Save to file
    output_dir = Path(f"/Users/dickgibbons/AI Projects/sports-betting/Daily Reports/{date_str}")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"nhl_totals_picks_{date_str}.json"
    with open(output_file, 'w') as f:
        json.dump(all_picks, f, indent=2)
    print(f"\n📁 Picks saved to: {output_file}")

    # Also save text version
    txt_file = output_dir / f"nhl_totals_picks_{date_str}.txt"
    with open(txt_file, 'w') as f:
        f.write(f"NHL FULL GAME TOTALS PICKS - {date_str}\n")
        f.write("=" * 60 + "\n\n")
        f.write("Strategy based on 828-game backtest:\n")
        f.write("- Over 6.5 (Combined > 13): 70.0% hit rate\n")
        f.write("- Under 5.5 (Both < 5.9): 62.9% hit rate\n")
        f.write("- Over 5.5 (Both > 6.3): 61.3% hit rate\n\n")

        if all_picks:
            f.write(f"TODAY'S PICKS: {len(all_picks)}\n")
            f.write("-" * 60 + "\n\n")
            for i, pick in enumerate(all_picks, 1):
                f.write(f"#{i} {pick['game']}\n")
                f.write(f"   BET: {pick['bet']}\n")
                f.write(f"   Confidence: {pick['confidence']:.1f}%\n")
                f.write(f"   Reasoning: {pick['reasoning']}\n")
                f.write(f"   Historical: {pick['historical_win_pct']}% win rate\n\n")
        else:
            f.write("No qualifying picks today.\n")

    print(f"📁 Text report saved to: {txt_file}")

    return all_picks


if __name__ == '__main__':
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    picks = generate_daily_picks(date_str)
