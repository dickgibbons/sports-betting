#!/usr/bin/env python3
"""
Full Market Soccer Betting Backtest
Analyzes ALL betting markets to find profitable opportunities
"""

import os
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

# All major leagues
ALL_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    88: "Eredivisie",
    94: "Primeira Liga",
    207: "Super League",
    203: "Süper Lig",
    144: "Belgium Pro League",
    71: "Brazil Serie A",
    253: "MLS",
}

# Typical market odds (for edge calculation)
TYPICAL_ODDS = {
    # BTTS
    'btts_yes': 1.75,
    'btts_no': 2.05,
    # Totals
    'over_0_5': 1.08,
    'under_0_5': 7.00,
    'over_1_5': 1.33,
    'under_1_5': 3.25,
    'over_2_5': 1.90,
    'under_2_5': 1.95,
    'over_3_5': 2.75,
    'under_3_5': 1.45,
    'over_4_5': 4.50,
    'under_4_5': 1.20,
    # First Half
    'h1_over_0_5': 1.28,
    'h1_under_0_5': 3.75,
    'h1_over_1_5': 2.50,
    'h1_under_1_5': 1.50,
    # Money Line
    'home_win': 2.10,
    'draw': 3.40,
    'away_win': 3.50,
    # Double Chance
    'home_or_draw': 1.35,
    'away_or_draw': 1.70,
    # Team Totals
    'home_over_0_5': 1.25,
    'home_over_1_5': 2.10,
    'home_over_2_5': 4.00,
    'away_over_0_5': 1.40,
    'away_over_1_5': 2.60,
    'away_over_2_5': 5.50,
    # Clean Sheet
    'home_clean_sheet': 2.60,
    'away_clean_sheet': 3.00,
    # Win to Nil
    'home_win_to_nil': 4.00,
    'away_win_to_nil': 6.00,
}


class FullMarketBacktester:
    def __init__(self):
        self.matches = []

    def fetch_matches(self, days_back: int = 60) -> List[Dict]:
        """Fetch completed matches"""
        print(f"\n📊 Fetching matches (last {days_back} days)...")

        all_matches = []
        headers = {'x-apisports-key': API_KEY}

        for league_id, league_name in ALL_LEAGUES.items():
            url = f"{API_BASE}/fixtures"
            params = {
                'league': league_id,
                'season': 2024,
                'status': 'FT',
                'last': 50
            }

            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get('response', [])

                    for match in matches:
                        fixture = match.get('fixture', {})
                        teams = match.get('teams', {})
                        goals = match.get('goals', {})
                        score = match.get('score', {})

                        home_goals = goals.get('home', 0) or 0
                        away_goals = goals.get('away', 0) or 0
                        total = home_goals + away_goals

                        h1_home = score.get('halftime', {}).get('home', 0) or 0
                        h1_away = score.get('halftime', {}).get('away', 0) or 0
                        h1_total = h1_home + h1_away

                        match_data = {
                            'date': fixture.get('date', '')[:10],
                            'league': league_name,
                            'league_id': league_id,
                            'home_team': teams.get('home', {}).get('name', ''),
                            'away_team': teams.get('away', {}).get('name', ''),
                            'home_goals': home_goals,
                            'away_goals': away_goals,
                            'total': total,
                            'h1_home': h1_home,
                            'h1_away': h1_away,
                            'h1_total': h1_total,
                            # Outcomes
                            'home_win': 1 if home_goals > away_goals else 0,
                            'draw': 1 if home_goals == away_goals else 0,
                            'away_win': 1 if away_goals > home_goals else 0,
                            'btts': 1 if home_goals > 0 and away_goals > 0 else 0,
                            'over_0_5': 1 if total > 0.5 else 0,
                            'over_1_5': 1 if total > 1.5 else 0,
                            'over_2_5': 1 if total > 2.5 else 0,
                            'over_3_5': 1 if total > 3.5 else 0,
                            'over_4_5': 1 if total > 4.5 else 0,
                            'h1_over_0_5': 1 if h1_total > 0.5 else 0,
                            'h1_over_1_5': 1 if h1_total > 1.5 else 0,
                            'home_over_0_5': 1 if home_goals > 0.5 else 0,
                            'home_over_1_5': 1 if home_goals > 1.5 else 0,
                            'home_over_2_5': 1 if home_goals > 2.5 else 0,
                            'away_over_0_5': 1 if away_goals > 0.5 else 0,
                            'away_over_1_5': 1 if away_goals > 1.5 else 0,
                            'away_over_2_5': 1 if away_goals > 2.5 else 0,
                            'home_clean_sheet': 1 if away_goals == 0 else 0,
                            'away_clean_sheet': 1 if home_goals == 0 else 0,
                            'home_win_to_nil': 1 if home_goals > away_goals and away_goals == 0 else 0,
                            'away_win_to_nil': 1 if away_goals > home_goals and home_goals == 0 else 0,
                        }
                        all_matches.append(match_data)

                    print(f"   {league_name}: {len(matches)} matches")

            except Exception as e:
                print(f"   Error {league_name}: {e}")

        self.matches = all_matches
        print(f"\n📊 Total: {len(all_matches)} matches")
        return all_matches

    def analyze_all_markets(self):
        """Analyze all betting markets"""
        df = pd.DataFrame(self.matches)

        if len(df) == 0:
            print("No data")
            return

        print("\n" + "="*100)
        print("COMPREHENSIVE MARKET ANALYSIS - ALL BETTING OPTIONS")
        print("="*100)
        print(f"Matches: {len(df)} | Leagues: {df['league'].nunique()} | Date range: {df['date'].min()} to {df['date'].max()}")

        # Calculate all market stats
        markets = []

        # BTTS Markets
        markets.append(self._calc_market('BTTS Yes', df['btts'].mean(), TYPICAL_ODDS['btts_yes']))
        markets.append(self._calc_market('BTTS No', 1 - df['btts'].mean(), TYPICAL_ODDS['btts_no']))

        # Total Goals Markets
        markets.append(self._calc_market('Over 0.5', df['over_0_5'].mean(), TYPICAL_ODDS['over_0_5']))
        markets.append(self._calc_market('Under 0.5', 1 - df['over_0_5'].mean(), TYPICAL_ODDS['under_0_5']))
        markets.append(self._calc_market('Over 1.5', df['over_1_5'].mean(), TYPICAL_ODDS['over_1_5']))
        markets.append(self._calc_market('Under 1.5', 1 - df['over_1_5'].mean(), TYPICAL_ODDS['under_1_5']))
        markets.append(self._calc_market('Over 2.5', df['over_2_5'].mean(), TYPICAL_ODDS['over_2_5']))
        markets.append(self._calc_market('Under 2.5', 1 - df['over_2_5'].mean(), TYPICAL_ODDS['under_2_5']))
        markets.append(self._calc_market('Over 3.5', df['over_3_5'].mean(), TYPICAL_ODDS['over_3_5']))
        markets.append(self._calc_market('Under 3.5', 1 - df['over_3_5'].mean(), TYPICAL_ODDS['under_3_5']))
        markets.append(self._calc_market('Over 4.5', df['over_4_5'].mean(), TYPICAL_ODDS['over_4_5']))
        markets.append(self._calc_market('Under 4.5', 1 - df['over_4_5'].mean(), TYPICAL_ODDS['under_4_5']))

        # First Half Markets
        markets.append(self._calc_market('H1 Over 0.5', df['h1_over_0_5'].mean(), TYPICAL_ODDS['h1_over_0_5']))
        markets.append(self._calc_market('H1 Under 0.5', 1 - df['h1_over_0_5'].mean(), TYPICAL_ODDS['h1_under_0_5']))
        markets.append(self._calc_market('H1 Over 1.5', df['h1_over_1_5'].mean(), TYPICAL_ODDS['h1_over_1_5']))
        markets.append(self._calc_market('H1 Under 1.5', 1 - df['h1_over_1_5'].mean(), TYPICAL_ODDS['h1_under_1_5']))

        # Money Line Markets
        markets.append(self._calc_market('Home Win', df['home_win'].mean(), TYPICAL_ODDS['home_win']))
        markets.append(self._calc_market('Draw', df['draw'].mean(), TYPICAL_ODDS['draw']))
        markets.append(self._calc_market('Away Win', df['away_win'].mean(), TYPICAL_ODDS['away_win']))

        # Double Chance
        home_or_draw = df['home_win'].mean() + df['draw'].mean()
        away_or_draw = df['away_win'].mean() + df['draw'].mean()
        markets.append(self._calc_market('Home or Draw', home_or_draw, TYPICAL_ODDS['home_or_draw']))
        markets.append(self._calc_market('Away or Draw', away_or_draw, TYPICAL_ODDS['away_or_draw']))

        # Team Totals
        markets.append(self._calc_market('Home O0.5', df['home_over_0_5'].mean(), TYPICAL_ODDS['home_over_0_5']))
        markets.append(self._calc_market('Home O1.5', df['home_over_1_5'].mean(), TYPICAL_ODDS['home_over_1_5']))
        markets.append(self._calc_market('Home O2.5', df['home_over_2_5'].mean(), TYPICAL_ODDS['home_over_2_5']))
        markets.append(self._calc_market('Away O0.5', df['away_over_0_5'].mean(), TYPICAL_ODDS['away_over_0_5']))
        markets.append(self._calc_market('Away O1.5', df['away_over_1_5'].mean(), TYPICAL_ODDS['away_over_1_5']))
        markets.append(self._calc_market('Away O2.5', df['away_over_2_5'].mean(), TYPICAL_ODDS['away_over_2_5']))

        # Clean Sheet / Win to Nil
        markets.append(self._calc_market('Home CS', df['home_clean_sheet'].mean(), TYPICAL_ODDS['home_clean_sheet']))
        markets.append(self._calc_market('Away CS', df['away_clean_sheet'].mean(), TYPICAL_ODDS['away_clean_sheet']))
        markets.append(self._calc_market('Home WTN', df['home_win_to_nil'].mean(), TYPICAL_ODDS['home_win_to_nil']))
        markets.append(self._calc_market('Away WTN', df['away_win_to_nil'].mean(), TYPICAL_ODDS['away_win_to_nil']))

        # Sort by edge
        markets_df = pd.DataFrame(markets)
        markets_df = markets_df.sort_values('edge', ascending=False)

        # Display results
        print("\n" + "="*100)
        print("ALL MARKETS RANKED BY EDGE (Positive = Profitable)")
        print("="*100)
        print(f"{'Market':<20} {'Hit Rate':>10} {'Fair Odds':>10} {'Typical':>10} {'Edge%':>10} {'EV/Bet':>10} {'Verdict':>12}")
        print("-"*100)

        for _, row in markets_df.iterrows():
            edge_symbol = "✅ PROFIT" if row['edge'] > 0 else "❌ LOSS"
            ev = (row['hit_rate'] * row['typical_odds'] - 1) * 100
            print(f"{row['market']:<20} {row['hit_rate']*100:>9.1f}% {row['fair_odds']:>10.2f} {row['typical_odds']:>10.2f} {row['edge']:>+9.1f}% {ev:>+9.1f}% {edge_symbol:>12}")

        # Top profitable markets
        profitable = markets_df[markets_df['edge'] > 0]
        print(f"\n{'='*100}")
        print(f"🏆 PROFITABLE MARKETS: {len(profitable)} out of {len(markets_df)}")
        print("="*100)

        if len(profitable) > 0:
            for _, row in profitable.head(10).iterrows():
                print(f"   ✅ {row['market']}: {row['hit_rate']*100:.1f}% hit rate, +{row['edge']:.1f}% edge at {row['typical_odds']:.2f} odds")

        # League breakdown for top markets
        self._analyze_by_league(df, markets_df)

        return markets_df

    def _calc_market(self, name: str, hit_rate: float, typical_odds: float) -> dict:
        """Calculate market statistics"""
        fair_odds = 1 / hit_rate if hit_rate > 0 else 999
        implied_prob = 1 / typical_odds
        edge = (hit_rate - implied_prob) * 100
        return {
            'market': name,
            'hit_rate': hit_rate,
            'fair_odds': fair_odds,
            'typical_odds': typical_odds,
            'edge': edge
        }

    def _analyze_by_league(self, df: pd.DataFrame, markets_df: pd.DataFrame):
        """Find league-specific value"""
        print(f"\n{'='*100}")
        print("LEAGUE-SPECIFIC OPPORTUNITIES")
        print("="*100)

        # Top markets to analyze by league
        key_markets = ['btts', 'over_2_5', 'over_3_5', 'home_win', 'h1_over_0_5']

        league_opps = []

        for league in df['league'].unique():
            league_df = df[df['league'] == league]
            if len(league_df) < 20:
                continue

            # BTTS No
            btts_no_rate = 1 - league_df['btts'].mean()
            btts_no_edge = (btts_no_rate - 1/TYPICAL_ODDS['btts_no']) * 100
            if btts_no_edge > 3:
                league_opps.append((league, 'BTTS No', btts_no_rate*100, btts_no_edge, TYPICAL_ODDS['btts_no']))

            # BTTS Yes
            btts_yes_rate = league_df['btts'].mean()
            btts_yes_edge = (btts_yes_rate - 1/TYPICAL_ODDS['btts_yes']) * 100
            if btts_yes_edge > 3:
                league_opps.append((league, 'BTTS Yes', btts_yes_rate*100, btts_yes_edge, TYPICAL_ODDS['btts_yes']))

            # Over 2.5
            over25_rate = league_df['over_2_5'].mean()
            over25_edge = (over25_rate - 1/TYPICAL_ODDS['over_2_5']) * 100
            if over25_edge > 3:
                league_opps.append((league, 'Over 2.5', over25_rate*100, over25_edge, TYPICAL_ODDS['over_2_5']))

            # Under 2.5
            under25_rate = 1 - league_df['over_2_5'].mean()
            under25_edge = (under25_rate - 1/TYPICAL_ODDS['under_2_5']) * 100
            if under25_edge > 3:
                league_opps.append((league, 'Under 2.5', under25_rate*100, under25_edge, TYPICAL_ODDS['under_2_5']))

            # Over 3.5
            over35_rate = league_df['over_3_5'].mean()
            over35_edge = (over35_rate - 1/TYPICAL_ODDS['over_3_5']) * 100
            if over35_edge > 3:
                league_opps.append((league, 'Over 3.5', over35_rate*100, over35_edge, TYPICAL_ODDS['over_3_5']))

            # Home Win
            home_rate = league_df['home_win'].mean()
            home_edge = (home_rate - 1/TYPICAL_ODDS['home_win']) * 100
            if home_edge > 3:
                league_opps.append((league, 'Home Win', home_rate*100, home_edge, TYPICAL_ODDS['home_win']))

        # Sort by edge
        league_opps.sort(key=lambda x: x[3], reverse=True)

        print(f"\n{'League':<25} {'Market':<15} {'Hit Rate':>10} {'Edge%':>10} {'Odds':>8}")
        print("-"*75)

        for league, market, rate, edge, odds in league_opps[:20]:
            print(f"💎 {league:<23} {market:<15} {rate:>9.1f}% {edge:>+9.1f}% {odds:>8.2f}")

        # Summary recommendations
        print(f"\n{'='*100}")
        print("📈 ACTIONABLE RECOMMENDATIONS")
        print("="*100)

        # Group by market
        market_leagues = defaultdict(list)
        for league, market, rate, edge, odds in league_opps:
            if edge > 3:
                market_leagues[market].append((league, rate, edge))

        for market, leagues in sorted(market_leagues.items(), key=lambda x: -len(x[1])):
            print(f"\n{market}:")
            for league, rate, edge in sorted(leagues, key=lambda x: -x[2])[:5]:
                print(f"   ✅ {league}: {rate:.1f}% hit rate (+{edge:.1f}% edge)")


def main():
    print("="*100)
    print("FULL MARKET SOCCER BETTING ANALYSIS")
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*100)

    bt = FullMarketBacktester()
    bt.fetch_matches(days_back=60)
    bt.analyze_all_markets()

    print("\n" + "="*100)
    print("ANALYSIS COMPLETE")
    print("="*100)


if __name__ == "__main__":
    main()
