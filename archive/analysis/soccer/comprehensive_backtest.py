#!/usr/bin/env python3
"""
Comprehensive Soccer Betting Backtest
Analyzes historical performance across all markets to identify profitable patterns
"""

import os
import sys
import requests
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

# Top leagues to analyze
TOP_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    88: "Eredivisie",
    94: "Primeira Liga",
    207: "Super League",
    203: "Süper Lig",
}

class SoccerBacktester:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'models', 'soccer_ml_models_with_form.pkl')
        self.models = None
        self.scaler = None
        self.feature_names = []
        self.load_models()

    def load_models(self):
        try:
            model_data = joblib.load(self.model_path)
            self.models = model_data.get('models', {})
            self.scaler = model_data.get('scaler')
            self.feature_names = model_data.get('feature_names', [])
            print(f"✅ Loaded {len(self.models)} models")
        except Exception as e:
            print(f"❌ Error loading models: {e}")

    def fetch_completed_matches(self, days_back: int = 30) -> List[Dict]:
        """Fetch completed matches for backtesting"""
        print(f"\n📊 Fetching completed matches (last {days_back} days)...")

        all_matches = []
        headers = {'x-apisports-key': API_KEY}

        for league_id, league_name in TOP_LEAGUES.items():
            url = f"{API_BASE}/fixtures"
            params = {
                'league': league_id,
                'season': 2024,
                'status': 'FT',  # Finished matches
                'last': min(50, days_back * 2)  # Get recent finished matches
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

                        match_data = {
                            'fixture_id': fixture.get('id'),
                            'date': fixture.get('date', '')[:10],
                            'league': league_name,
                            'league_id': league_id,
                            'home_team': teams.get('home', {}).get('name', ''),
                            'away_team': teams.get('away', {}).get('name', ''),
                            'home_goals': goals.get('home', 0),
                            'away_goals': goals.get('away', 0),
                            'total_goals': (goals.get('home', 0) or 0) + (goals.get('away', 0) or 0),
                            'h1_home': score.get('halftime', {}).get('home', 0) or 0,
                            'h1_away': score.get('halftime', {}).get('away', 0) or 0,
                        }

                        # Calculate outcomes
                        match_data['btts'] = 1 if match_data['home_goals'] > 0 and match_data['away_goals'] > 0 else 0
                        match_data['over_2_5'] = 1 if match_data['total_goals'] > 2.5 else 0
                        match_data['over_1_5'] = 1 if match_data['total_goals'] > 1.5 else 0
                        match_data['h1_over_0_5'] = 1 if (match_data['h1_home'] + match_data['h1_away']) > 0.5 else 0
                        match_data['home_over_1_5'] = 1 if match_data['home_goals'] > 1.5 else 0
                        match_data['away_over_1_5'] = 1 if match_data['away_goals'] > 1.5 else 0

                        all_matches.append(match_data)

                    print(f"   {league_name}: {len(matches)} matches")

            except Exception as e:
                print(f"   Error fetching {league_name}: {e}")

        print(f"\n📊 Total matches: {len(all_matches)}")
        return all_matches

    def analyze_outcomes(self, matches: List[Dict]):
        """Analyze actual outcome distributions"""
        print("\n" + "="*80)
        print("ACTUAL OUTCOME ANALYSIS")
        print("="*80)

        df = pd.DataFrame(matches)

        if len(df) == 0:
            print("No matches to analyze")
            return

        print(f"\nTotal matches analyzed: {len(df)}")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")

        print("\n📊 OUTCOME RATES BY MARKET:")
        print("-"*60)

        outcomes = {
            'BTTS Yes': df['btts'].mean() * 100,
            'BTTS No': (1 - df['btts'].mean()) * 100,
            'Over 2.5': df['over_2_5'].mean() * 100,
            'Under 2.5': (1 - df['over_2_5'].mean()) * 100,
            'Over 1.5': df['over_1_5'].mean() * 100,
            'Under 1.5': (1 - df['over_1_5'].mean()) * 100,
            'H1 Over 0.5': df['h1_over_0_5'].mean() * 100,
            'H1 Under 0.5': (1 - df['h1_over_0_5'].mean()) * 100,
            'Home O1.5': df['home_over_1_5'].mean() * 100,
            'Away O1.5': df['away_over_1_5'].mean() * 100,
        }

        for market, rate in outcomes.items():
            fair_odds = 100 / rate if rate > 0 else 999
            print(f"   {market:15} : {rate:5.1f}% (fair odds: {fair_odds:.2f})")

        print("\n📊 OUTCOME RATES BY LEAGUE:")
        print("-"*60)

        for league in df['league'].unique():
            league_df = df[df['league'] == league]
            btts_rate = league_df['btts'].mean() * 100
            over25_rate = league_df['over_2_5'].mean() * 100
            h1_rate = league_df['h1_over_0_5'].mean() * 100
            print(f"   {league:20} : BTTS {btts_rate:5.1f}% | O2.5 {over25_rate:5.1f}% | H1>0.5 {h1_rate:5.1f}% ({len(league_df)} games)")

        return outcomes

    def identify_value_opportunities(self, matches: List[Dict]):
        """Identify where betting edge exists"""
        print("\n" + "="*80)
        print("VALUE OPPORTUNITY ANALYSIS")
        print("="*80)

        df = pd.DataFrame(matches)

        if len(df) == 0:
            return

        # Typical market odds (approximate)
        typical_odds = {
            'btts_yes': 1.80,
            'btts_no': 2.00,
            'over_2_5': 1.90,
            'under_2_5': 1.95,
            'over_1_5': 1.35,
            'under_1_5': 3.20,
            'h1_over_0_5': 1.30,
            'h1_under_0_5': 3.50,
        }

        print("\n💰 VALUE ANALYSIS (Actual Rate vs Implied by Typical Odds):")
        print("-"*80)

        value_opps = []

        # BTTS No analysis
        btts_no_rate = (1 - df['btts'].mean()) * 100
        btts_no_implied = (1 / typical_odds['btts_no']) * 100
        btts_no_edge = btts_no_rate - btts_no_implied
        value_opps.append(('BTTS No', btts_no_rate, btts_no_implied, btts_no_edge, typical_odds['btts_no']))

        # BTTS Yes analysis
        btts_yes_rate = df['btts'].mean() * 100
        btts_yes_implied = (1 / typical_odds['btts_yes']) * 100
        btts_yes_edge = btts_yes_rate - btts_yes_implied
        value_opps.append(('BTTS Yes', btts_yes_rate, btts_yes_implied, btts_yes_edge, typical_odds['btts_yes']))

        # Over 2.5 analysis
        over25_rate = df['over_2_5'].mean() * 100
        over25_implied = (1 / typical_odds['over_2_5']) * 100
        over25_edge = over25_rate - over25_implied
        value_opps.append(('Over 2.5', over25_rate, over25_implied, over25_edge, typical_odds['over_2_5']))

        # Under 2.5 analysis
        under25_rate = (1 - df['over_2_5'].mean()) * 100
        under25_implied = (1 / typical_odds['under_2_5']) * 100
        under25_edge = under25_rate - under25_implied
        value_opps.append(('Under 2.5', under25_rate, under25_implied, under25_edge, typical_odds['under_2_5']))

        # H1 Over 0.5 analysis
        h1_rate = df['h1_over_0_5'].mean() * 100
        h1_implied = (1 / typical_odds['h1_over_0_5']) * 100
        h1_edge = h1_rate - h1_implied
        value_opps.append(('H1 Over 0.5', h1_rate, h1_implied, h1_edge, typical_odds['h1_over_0_5']))

        # H1 Under 0.5 analysis
        h1_under_rate = (1 - df['h1_over_0_5'].mean()) * 100
        h1_under_implied = (1 / typical_odds['h1_under_0_5']) * 100
        h1_under_edge = h1_under_rate - h1_under_implied
        value_opps.append(('H1 Under 0.5', h1_under_rate, h1_under_implied, h1_under_edge, typical_odds['h1_under_0_5']))

        # Sort by edge
        value_opps.sort(key=lambda x: x[3], reverse=True)

        print(f"{'Market':15} {'Actual%':>10} {'Implied%':>10} {'Edge%':>10} {'Odds':>8}")
        print("-"*60)

        for market, actual, implied, edge, odds in value_opps:
            edge_symbol = "✅" if edge > 0 else "❌"
            print(f"{edge_symbol} {market:13} {actual:10.1f} {implied:10.1f} {edge:+10.1f} {odds:8.2f}")

        print("\n📈 RECOMMENDATIONS TO FIND MORE GOOD BETS:")
        print("-"*80)

        recommendations = []

        # Check if BTTS No is overused
        if btts_no_edge > 0:
            recommendations.append(f"✅ BTTS No has {btts_no_edge:.1f}% edge - KEEP USING")
        else:
            recommendations.append(f"⚠️  BTTS No has {btts_no_edge:.1f}% edge - REDUCE USAGE")

        if h1_under_edge > 3:
            recommendations.append(f"💡 H1 Under 0.5 has {h1_under_edge:.1f}% edge at {typical_odds['h1_under_0_5']:.2f} odds - ADD THIS MARKET")

        if under25_edge > 0:
            recommendations.append(f"💡 Under 2.5 has {under25_edge:.1f}% edge - ADD MORE OF THESE")

        # League-specific recommendations
        print("\n📊 LEAGUE-SPECIFIC VALUE:")
        for league in df['league'].unique():
            league_df = df[df['league'] == league]
            if len(league_df) >= 10:
                btts_no = (1 - league_df['btts'].mean()) * 100
                if btts_no > 55:  # Higher than average
                    recommendations.append(f"💎 {league}: BTTS No hits {btts_no:.1f}% - PRIORITIZE")

        for rec in recommendations:
            print(f"   {rec}")

        return value_opps


def main():
    print("="*80)
    print("COMPREHENSIVE SOCCER BETTING BACKTEST")
    print(f"Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    backtester = SoccerBacktester()

    # Fetch recent completed matches
    matches = backtester.fetch_completed_matches(days_back=45)

    if matches:
        # Analyze outcomes
        backtester.analyze_outcomes(matches)

        # Identify value opportunities
        backtester.identify_value_opportunities(matches)

    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)


if __name__ == "__main__":
    main()
