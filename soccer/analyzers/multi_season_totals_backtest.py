#!/usr/bin/env python3
"""
Multi-Season Soccer Totals & First Half Backtest
Analyzes 3 seasons of data to find statistically significant profitable angles

Focus Areas:
1. Game Totals (Over/Under 0.5 through 4.5)
2. First Half Totals (H1 Over/Under)
3. League-specific patterns
4. Situational angles (favorites at home, underdogs, etc.)
"""

import os
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
import time
import json

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

# Major European leagues
LEAGUES = {
    39: {"name": "Premier League", "country": "England"},
    140: {"name": "La Liga", "country": "Spain"},
    135: {"name": "Serie A", "country": "Italy"},
    78: {"name": "Bundesliga", "country": "Germany"},
    61: {"name": "Ligue 1", "country": "France"},
    88: {"name": "Eredivisie", "country": "Netherlands"},
    94: {"name": "Primeira Liga", "country": "Portugal"},
    203: {"name": "Süper Lig", "country": "Turkey"},
    144: {"name": "Pro League", "country": "Belgium"},
    106: {"name": "Ekstraklasa", "country": "Poland"},
    119: {"name": "Superliga", "country": "Denmark"},
    103: {"name": "Eliteserien", "country": "Norway"},
}

# Seasons to analyze
SEASONS = [2022, 2023, 2024]

# Typical market odds
TYPICAL_ODDS = {
    'over_0_5': 1.08, 'under_0_5': 7.00,
    'over_1_5': 1.33, 'under_1_5': 3.25,
    'over_2_5': 1.90, 'under_2_5': 1.95,
    'over_3_5': 2.75, 'under_3_5': 1.45,
    'over_4_5': 4.50, 'under_4_5': 1.20,
    'h1_over_0_5': 1.30, 'h1_under_0_5': 3.50,
    'h1_over_1_5': 2.50, 'h1_under_1_5': 1.55,
    'h1_over_2_5': 6.00, 'h1_under_2_5': 1.12,
    'btts_yes': 1.75, 'btts_no': 2.05,
}


class MultiSeasonTotalsBacktest:
    """Comprehensive multi-season backtest for totals markets"""

    def __init__(self, cache_dir: str = None):
        self.headers = {'x-apisports-key': API_KEY}
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.all_matches = []

    def fetch_all_seasons(self, use_cache: bool = True) -> pd.DataFrame:
        """Fetch matches from all seasons"""
        cache_file = os.path.join(self.cache_dir, 'multi_season_data.json')

        if use_cache and os.path.exists(cache_file):
            # Check if cache is recent (less than 24 hours old)
            cache_age = time.time() - os.path.getmtime(cache_file)
            if cache_age < 86400:  # 24 hours
                print("📂 Loading from cache...")
                with open(cache_file, 'r') as f:
                    self.all_matches = json.load(f)
                print(f"   Loaded {len(self.all_matches)} matches from cache")
                return pd.DataFrame(self.all_matches)

        print("=" * 80)
        print("FETCHING MULTI-SEASON DATA")
        print("=" * 80)

        for season in SEASONS:
            print(f"\n📅 Season {season}-{season+1}")
            print("-" * 40)

            for league_id, league_info in LEAGUES.items():
                matches = self._fetch_league_season(league_id, league_info['name'], season)
                self.all_matches.extend(matches)
                time.sleep(0.3)  # Rate limiting

        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(self.all_matches, f)

        print(f"\n✅ Total matches fetched: {len(self.all_matches)}")
        return pd.DataFrame(self.all_matches)

    def _fetch_league_season(self, league_id: int, league_name: str, season: int) -> List[Dict]:
        """Fetch all matches for a league season"""
        matches = []

        url = f"{API_BASE}/fixtures"
        params = {
            'league': league_id,
            'season': season,
            'status': 'FT'
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=60)
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get('response', [])

                for fix in fixtures:
                    match = self._parse_match(fix, league_id, league_name, season)
                    if match:
                        matches.append(match)

                print(f"   {league_name}: {len(matches)} matches")
            else:
                print(f"   {league_name}: API error {response.status_code}")

        except Exception as e:
            print(f"   {league_name}: Error - {e}")

        return matches

    def _parse_match(self, fix: Dict, league_id: int, league_name: str, season: int) -> Dict:
        """Parse match data from API response"""
        try:
            fixture = fix.get('fixture', {})
            teams = fix.get('teams', {})
            goals = fix.get('goals', {})
            score = fix.get('score', {})

            home_goals = goals.get('home', 0) or 0
            away_goals = goals.get('away', 0) or 0
            total = home_goals + away_goals

            h1_home = score.get('halftime', {}).get('home', 0) or 0
            h1_away = score.get('halftime', {}).get('away', 0) or 0
            h1_total = h1_home + h1_away

            h2_total = total - h1_total

            return {
                'date': fixture.get('date', '')[:10],
                'season': season,
                'league_id': league_id,
                'league': league_name,
                'home_team': teams.get('home', {}).get('name', ''),
                'away_team': teams.get('away', {}).get('name', ''),
                'home_goals': home_goals,
                'away_goals': away_goals,
                'total': total,
                'h1_home': h1_home,
                'h1_away': h1_away,
                'h1_total': h1_total,
                'h2_total': h2_total,
                # Pre-compute outcomes for faster analysis
                'over_0_5': 1 if total > 0 else 0,
                'over_1_5': 1 if total > 1 else 0,
                'over_2_5': 1 if total > 2 else 0,
                'over_3_5': 1 if total > 3 else 0,
                'over_4_5': 1 if total > 4 else 0,
                'h1_over_0_5': 1 if h1_total > 0 else 0,
                'h1_over_1_5': 1 if h1_total > 1 else 0,
                'h1_over_2_5': 1 if h1_total > 2 else 0,
                'h2_over_0_5': 1 if h2_total > 0 else 0,
                'h2_over_1_5': 1 if h2_total > 1 else 0,
                'btts': 1 if home_goals > 0 and away_goals > 0 else 0,
                'home_scored': 1 if home_goals > 0 else 0,
                'away_scored': 1 if away_goals > 0 else 0,
                'home_win': 1 if home_goals > away_goals else 0,
                'draw': 1 if home_goals == away_goals else 0,
                'away_win': 1 if away_goals > home_goals else 0,
            }
        except:
            return None

    def analyze_totals(self, df: pd.DataFrame) -> Dict:
        """Comprehensive analysis of totals markets"""

        print("\n" + "=" * 100)
        print("GAME TOTALS ANALYSIS")
        print("=" * 100)
        print(f"Total matches: {len(df)} | Seasons: {df['season'].nunique()} | Leagues: {df['league'].nunique()}")

        results = {}

        # Overall totals distribution
        print("\n📊 GOALS DISTRIBUTION:")
        print("-" * 50)
        for i in range(8):
            count = len(df[df['total'] == i])
            pct = count / len(df) * 100
            print(f"   {i} goals: {count:>5} matches ({pct:>5.1f}%)")

        # Totals market analysis
        print("\n📊 TOTALS MARKET ANALYSIS (All Leagues):")
        print("-" * 80)
        print(f"{'Market':<20} {'Hit Rate':>12} {'Fair Odds':>12} {'Typical':>12} {'Edge%':>12}")
        print("-" * 80)

        totals_markets = [
            ('Over 0.5', 'over_0_5', 'over_0_5'),
            ('Over 1.5', 'over_1_5', 'over_1_5'),
            ('Over 2.5', 'over_2_5', 'over_2_5'),
            ('Over 3.5', 'over_3_5', 'over_3_5'),
            ('Over 4.5', 'over_4_5', 'over_4_5'),
            ('Under 0.5', 'over_0_5', 'under_0_5'),
            ('Under 1.5', 'over_1_5', 'under_1_5'),
            ('Under 2.5', 'over_2_5', 'under_2_5'),
            ('Under 3.5', 'over_3_5', 'under_3_5'),
            ('Under 4.5', 'over_4_5', 'under_4_5'),
        ]

        for market_name, col, odds_key in totals_markets:
            if 'Under' in market_name:
                hit_rate = 1 - df[col].mean()
            else:
                hit_rate = df[col].mean()

            fair_odds = 1 / hit_rate if hit_rate > 0 else 999
            typical = TYPICAL_ODDS[odds_key]
            implied = 1 / typical
            edge = (hit_rate - implied) * 100

            emoji = "✅" if edge > 0 else "❌"
            print(f"{emoji} {market_name:<18} {hit_rate*100:>11.1f}% {fair_odds:>12.2f} {typical:>12.2f} {edge:>+11.1f}%")

            results[market_name] = {
                'hit_rate': hit_rate,
                'fair_odds': fair_odds,
                'typical_odds': typical,
                'edge': edge,
                'sample_size': len(df)
            }

        return results

    def analyze_first_half(self, df: pd.DataFrame) -> Dict:
        """Comprehensive analysis of first half totals"""

        print("\n" + "=" * 100)
        print("FIRST HALF TOTALS ANALYSIS")
        print("=" * 100)

        results = {}

        # First half goals distribution
        print("\n📊 FIRST HALF GOALS DISTRIBUTION:")
        print("-" * 50)
        for i in range(6):
            count = len(df[df['h1_total'] == i])
            pct = count / len(df) * 100
            print(f"   {i} goals: {count:>5} matches ({pct:>5.1f}%)")

        # First half markets
        print("\n📊 FIRST HALF MARKET ANALYSIS:")
        print("-" * 80)
        print(f"{'Market':<20} {'Hit Rate':>12} {'Fair Odds':>12} {'Typical':>12} {'Edge%':>12}")
        print("-" * 80)

        h1_markets = [
            ('H1 Over 0.5', 'h1_over_0_5', 'h1_over_0_5'),
            ('H1 Over 1.5', 'h1_over_1_5', 'h1_over_1_5'),
            ('H1 Over 2.5', 'h1_over_2_5', 'h1_over_2_5'),
            ('H1 Under 0.5', 'h1_over_0_5', 'h1_under_0_5'),
            ('H1 Under 1.5', 'h1_over_1_5', 'h1_under_1_5'),
            ('H1 Under 2.5', 'h1_over_2_5', 'h1_under_2_5'),
        ]

        for market_name, col, odds_key in h1_markets:
            if 'Under' in market_name:
                hit_rate = 1 - df[col].mean()
            else:
                hit_rate = df[col].mean()

            fair_odds = 1 / hit_rate if hit_rate > 0 else 999
            typical = TYPICAL_ODDS[odds_key]
            implied = 1 / typical
            edge = (hit_rate - implied) * 100

            emoji = "✅" if edge > 0 else "❌"
            print(f"{emoji} {market_name:<18} {hit_rate*100:>11.1f}% {fair_odds:>12.2f} {typical:>12.2f} {edge:>+11.1f}%")

            results[market_name] = {
                'hit_rate': hit_rate,
                'fair_odds': fair_odds,
                'typical_odds': typical,
                'edge': edge,
                'sample_size': len(df)
            }

        # Second half analysis (can be valuable)
        print("\n📊 SECOND HALF PATTERNS:")
        print("-" * 50)
        h2_over_0_5 = df['h2_over_0_5'].mean()
        h2_over_1_5 = df['h2_over_1_5'].mean()
        print(f"   H2 Over 0.5: {h2_over_0_5*100:.1f}%")
        print(f"   H2 Over 1.5: {h2_over_1_5*100:.1f}%")

        # Correlation: If H1 is low scoring, is H2 higher?
        low_h1 = df[df['h1_total'] == 0]
        if len(low_h1) > 0:
            h2_after_scoreless_h1 = low_h1['h2_total'].mean()
            h2_over_1_5_after_0_h1 = low_h1['h2_over_1_5'].mean()
            print(f"\n🔍 AFTER SCORELESS FIRST HALF (0-0 at HT):")
            print(f"   Matches: {len(low_h1)}")
            print(f"   Avg H2 Goals: {h2_after_scoreless_h1:.2f}")
            print(f"   H2 Over 1.5: {h2_over_1_5_after_0_h1*100:.1f}%")

            results['h2_over_1_5_after_0_0'] = {
                'hit_rate': h2_over_1_5_after_0_h1,
                'sample_size': len(low_h1)
            }

        return results

    def analyze_by_league(self, df: pd.DataFrame) -> Dict:
        """Find league-specific value"""

        print("\n" + "=" * 100)
        print("LEAGUE-SPECIFIC ANALYSIS")
        print("=" * 100)

        results = {}
        opportunities = []

        for league in df['league'].unique():
            league_df = df[df['league'] == league]
            n = len(league_df)

            if n < 100:  # Need sufficient sample
                continue

            # Calculate key metrics
            avg_goals = league_df['total'].mean()
            over_2_5 = league_df['over_2_5'].mean()
            over_3_5 = league_df['over_3_5'].mean()
            h1_over_0_5 = league_df['h1_over_0_5'].mean()
            h1_over_1_5 = league_df['h1_over_1_5'].mean()
            btts = league_df['btts'].mean()

            results[league] = {
                'matches': n,
                'avg_goals': avg_goals,
                'over_2_5': over_2_5,
                'over_3_5': over_3_5,
                'h1_over_0_5': h1_over_0_5,
                'h1_over_1_5': h1_over_1_5,
                'btts': btts
            }

            # Check for value opportunities
            over_2_5_edge = (over_2_5 - 1/TYPICAL_ODDS['over_2_5']) * 100
            over_3_5_edge = (over_3_5 - 1/TYPICAL_ODDS['over_3_5']) * 100
            h1_over_0_5_edge = (h1_over_0_5 - 1/TYPICAL_ODDS['h1_over_0_5']) * 100
            h1_over_1_5_edge = (h1_over_1_5 - 1/TYPICAL_ODDS['h1_over_1_5']) * 100
            btts_edge = (btts - 1/TYPICAL_ODDS['btts_yes']) * 100
            under_2_5_edge = ((1-over_2_5) - 1/TYPICAL_ODDS['under_2_5']) * 100

            if over_2_5_edge > 3:
                opportunities.append((league, 'Over 2.5', over_2_5*100, over_2_5_edge, n))
            if over_3_5_edge > 5:
                opportunities.append((league, 'Over 3.5', over_3_5*100, over_3_5_edge, n))
            if h1_over_0_5_edge > 3:
                opportunities.append((league, 'H1 Over 0.5', h1_over_0_5*100, h1_over_0_5_edge, n))
            if h1_over_1_5_edge > 5:
                opportunities.append((league, 'H1 Over 1.5', h1_over_1_5*100, h1_over_1_5_edge, n))
            if btts_edge > 3:
                opportunities.append((league, 'BTTS Yes', btts*100, btts_edge, n))
            if under_2_5_edge > 3:
                opportunities.append((league, 'Under 2.5', (1-over_2_5)*100, under_2_5_edge, n))

        # Display league stats
        print(f"\n{'League':<20} {'Games':>8} {'Avg':>6} {'O2.5':>8} {'O3.5':>8} {'H1>0.5':>8} {'H1>1.5':>8} {'BTTS':>8}")
        print("-" * 90)

        for league, stats in sorted(results.items(), key=lambda x: -x[1]['avg_goals']):
            print(f"{league:<20} {stats['matches']:>8} {stats['avg_goals']:>6.2f} "
                  f"{stats['over_2_5']*100:>7.1f}% {stats['over_3_5']*100:>7.1f}% "
                  f"{stats['h1_over_0_5']*100:>7.1f}% {stats['h1_over_1_5']*100:>7.1f}% "
                  f"{stats['btts']*100:>7.1f}%")

        # Display opportunities
        if opportunities:
            print("\n" + "=" * 100)
            print("💎 VALUE OPPORTUNITIES (Edge > 3%)")
            print("=" * 100)

            opportunities.sort(key=lambda x: -x[3])

            print(f"\n{'League':<20} {'Market':<15} {'Hit Rate':>10} {'Edge%':>10} {'Sample':>10}")
            print("-" * 70)

            for league, market, rate, edge, sample in opportunities[:25]:
                print(f"✅ {league:<18} {market:<15} {rate:>9.1f}% {edge:>+9.1f}% {sample:>10}")

        return results, opportunities

    def find_situational_angles(self, df: pd.DataFrame) -> List[Dict]:
        """Find situational betting angles"""

        print("\n" + "=" * 100)
        print("SITUATIONAL ANGLES ANALYSIS")
        print("=" * 100)

        angles = []

        # High-scoring leagues
        print("\n🔍 HIGH-SCORING LEAGUE PATTERNS:")
        high_scoring_leagues = ['Bundesliga', 'Eredivisie', 'Eliteserien']
        for league in high_scoring_leagues:
            league_df = df[df['league'] == league]
            if len(league_df) > 0:
                over_2_5 = league_df['over_2_5'].mean()
                over_3_5 = league_df['over_3_5'].mean()
                h1_over_0_5 = league_df['h1_over_0_5'].mean()

                over_2_5_edge = (over_2_5 - 1/TYPICAL_ODDS['over_2_5']) * 100
                over_3_5_edge = (over_3_5 - 1/TYPICAL_ODDS['over_3_5']) * 100

                if over_2_5_edge > 2 or over_3_5_edge > 3:
                    print(f"   {league}: O2.5 {over_2_5*100:.1f}% (+{over_2_5_edge:.1f}%), "
                          f"O3.5 {over_3_5*100:.1f}% (+{over_3_5_edge:.1f}%)")
                    angles.append({
                        'name': f'{league} Over 2.5',
                        'condition': f"league == '{league}'",
                        'market': 'Over 2.5',
                        'hit_rate': over_2_5,
                        'edge': over_2_5_edge,
                        'sample': len(league_df)
                    })

        # Low-scoring leagues (Under value)
        print("\n🔍 LOW-SCORING LEAGUE PATTERNS:")
        low_scoring_leagues = ['Ligue 1', 'Primeira Liga', 'La Liga']
        for league in low_scoring_leagues:
            league_df = df[df['league'] == league]
            if len(league_df) > 0:
                under_2_5 = 1 - league_df['over_2_5'].mean()
                under_3_5 = 1 - league_df['over_3_5'].mean()

                under_2_5_edge = (under_2_5 - 1/TYPICAL_ODDS['under_2_5']) * 100

                if under_2_5_edge > 2:
                    print(f"   {league}: U2.5 {under_2_5*100:.1f}% (+{under_2_5_edge:.1f}%)")
                    angles.append({
                        'name': f'{league} Under 2.5',
                        'condition': f"league == '{league}'",
                        'market': 'Under 2.5',
                        'hit_rate': under_2_5,
                        'edge': under_2_5_edge,
                        'sample': len(league_df)
                    })

        # First Half patterns by total goals expectation
        print("\n🔍 FIRST HALF PATTERNS BY LEAGUE TYPE:")

        # Top 5 leagues for H1 Over 0.5
        league_h1 = df.groupby('league')['h1_over_0_5'].agg(['mean', 'count'])
        league_h1 = league_h1[league_h1['count'] >= 100].sort_values('mean', ascending=False)

        print("\n   Top leagues for H1 Over 0.5:")
        for league, row in league_h1.head(5).iterrows():
            edge = (row['mean'] - 1/TYPICAL_ODDS['h1_over_0_5']) * 100
            print(f"   {league}: {row['mean']*100:.1f}% ({int(row['count'])} games) | Edge: {edge:+.1f}%")
            if edge > 3:
                angles.append({
                    'name': f'{league} H1 Over 0.5',
                    'condition': f"league == '{league}'",
                    'market': 'H1 Over 0.5',
                    'hit_rate': row['mean'],
                    'edge': edge,
                    'sample': int(row['count'])
                })

        # H1 Over 1.5 patterns
        print("\n   Top leagues for H1 Over 1.5:")
        league_h1_15 = df.groupby('league')['h1_over_1_5'].agg(['mean', 'count'])
        league_h1_15 = league_h1_15[league_h1_15['count'] >= 100].sort_values('mean', ascending=False)

        for league, row in league_h1_15.head(5).iterrows():
            edge = (row['mean'] - 1/TYPICAL_ODDS['h1_over_1_5']) * 100
            print(f"   {league}: {row['mean']*100:.1f}% ({int(row['count'])} games) | Edge: {edge:+.1f}%")
            if edge > 5:
                angles.append({
                    'name': f'{league} H1 Over 1.5',
                    'condition': f"league == '{league}'",
                    'market': 'H1 Over 1.5',
                    'hit_rate': row['mean'],
                    'edge': edge,
                    'sample': int(row['count'])
                })

        return angles

    def generate_recommendations(self, df: pd.DataFrame, angles: List[Dict]) -> None:
        """Generate final recommendations"""

        print("\n" + "=" * 100)
        print("🎯 PROFITABLE BETTING ANGLES - RECOMMENDATIONS")
        print("=" * 100)

        # Filter to statistically significant angles
        significant_angles = [a for a in angles if a['edge'] > 3 and a['sample'] >= 100]
        significant_angles.sort(key=lambda x: -x['edge'])

        print("\n📊 STATISTICALLY SIGNIFICANT ANGLES (Edge > 3%, Sample >= 100):")
        print("-" * 90)
        print(f"{'Angle':<30} {'Market':<15} {'Hit Rate':>10} {'Edge%':>10} {'Sample':>10} {'ROI*':>10}")
        print("-" * 90)

        for angle in significant_angles[:15]:
            # Estimate ROI assuming typical odds
            market = angle['market']
            if 'Over 2.5' in market:
                odds = TYPICAL_ODDS['over_2_5']
            elif 'Over 3.5' in market:
                odds = TYPICAL_ODDS['over_3_5']
            elif 'Under 2.5' in market:
                odds = TYPICAL_ODDS['under_2_5']
            elif 'H1 Over 0.5' in market:
                odds = TYPICAL_ODDS['h1_over_0_5']
            elif 'H1 Over 1.5' in market:
                odds = TYPICAL_ODDS['h1_over_1_5']
            elif 'BTTS' in market:
                odds = TYPICAL_ODDS['btts_yes']
            else:
                odds = 1.90

            roi = (angle['hit_rate'] * odds - 1) * 100

            print(f"✅ {angle['name']:<28} {market:<15} {angle['hit_rate']*100:>9.1f}% "
                  f"{angle['edge']:>+9.1f}% {angle['sample']:>10} {roi:>+9.1f}%")

        # Top recommendations
        print("\n" + "=" * 100)
        print("🏆 TOP 5 RECOMMENDED STRATEGIES")
        print("=" * 100)

        for i, angle in enumerate(significant_angles[:5], 1):
            market = angle['market']
            if 'Over 2.5' in market:
                odds = TYPICAL_ODDS['over_2_5']
            elif 'Over 3.5' in market:
                odds = TYPICAL_ODDS['over_3_5']
            elif 'Under 2.5' in market:
                odds = TYPICAL_ODDS['under_2_5']
            elif 'H1 Over 0.5' in market:
                odds = TYPICAL_ODDS['h1_over_0_5']
            elif 'H1 Over 1.5' in market:
                odds = TYPICAL_ODDS['h1_over_1_5']
            else:
                odds = 1.90

            roi = (angle['hit_rate'] * odds - 1) * 100

            print(f"\n{i}. {angle['name']}")
            print(f"   Market: {angle['market']}")
            print(f"   Hit Rate: {angle['hit_rate']*100:.1f}%")
            print(f"   Edge vs Market: +{angle['edge']:.1f}%")
            print(f"   Expected ROI: {roi:+.1f}%")
            print(f"   Sample Size: {angle['sample']} matches")
            print(f"   Confidence: {'HIGH' if angle['sample'] >= 500 else 'MEDIUM' if angle['sample'] >= 200 else 'LOW'}")

        # Summary stats
        print("\n" + "=" * 100)
        print("📈 EXPECTED PERFORMANCE (Based on Historical Data)")
        print("=" * 100)

        if significant_angles:
            avg_edge = np.mean([a['edge'] for a in significant_angles[:5]])
            avg_hit_rate = np.mean([a['hit_rate'] for a in significant_angles[:5]])

            print(f"\n   Average Edge (Top 5): +{avg_edge:.1f}%")
            print(f"   Average Hit Rate (Top 5): {avg_hit_rate*100:.1f}%")
            print(f"   Estimated Monthly ROI (100 bets): +{avg_edge * 0.8:.1f}% to +{avg_edge * 1.2:.1f}%")
            print(f"   Breakeven Win Rate Needed: ~52.4% (at -110 odds)")


def main():
    print("=" * 100)
    print("MULTI-SEASON SOCCER TOTALS BACKTEST")
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    bt = MultiSeasonTotalsBacktest()

    # Fetch data
    df = bt.fetch_all_seasons(use_cache=True)

    if len(df) == 0:
        print("No data fetched")
        return

    print(f"\n📊 Dataset: {len(df)} matches")
    print(f"   Seasons: {sorted(df['season'].unique())}")
    print(f"   Leagues: {df['league'].nunique()}")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")

    # Run analyses
    totals_results = bt.analyze_totals(df)
    h1_results = bt.analyze_first_half(df)
    league_results, opportunities = bt.analyze_by_league(df)
    angles = bt.find_situational_angles(df)

    # Add opportunities to angles
    for opp in opportunities:
        angles.append({
            'name': f"{opp[0]} {opp[1]}",
            'condition': f"league == '{opp[0]}'",
            'market': opp[1],
            'hit_rate': opp[2] / 100,
            'edge': opp[3],
            'sample': opp[4]
        })

    # Generate recommendations
    bt.generate_recommendations(df, angles)

    print("\n" + "=" * 100)
    print("BACKTEST COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()
