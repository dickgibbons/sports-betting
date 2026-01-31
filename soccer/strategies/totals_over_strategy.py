#!/usr/bin/env python3
"""
Soccer Totals Over Strategy
Based on 3-season backtest of 11,461 matches

Profitable Angles Identified:
1. Bundesliga Over 2.5: 61.1% hit rate, +16.1% ROI
2. Eliteserien Over 2.5: 60.1% hit rate, +14.3% ROI
3. Eredivisie Over 2.5: 59.6% hit rate, +13.2% ROI
4. Premier League Over 2.5: 58.0% hit rate, +10.2% ROI
"""

import os
import requests
import json
from datetime import datetime
from typing import Dict, List

API_KEY = "960c628e1c91c4b1f125e1eec52ad862"
API_BASE = "https://v3.football.api-sports.io"

# Profitable leagues with their historical performance
PROFITABLE_LEAGUES = {
    78: {
        "name": "Bundesliga",
        "country": "Germany",
        "over_2_5_rate": 0.611,
        "edge": 8.5,
        "roi": 16.1,
        "recommended_stake": 2.0,
        "confidence": "HIGH"
    },
    103: {
        "name": "Eliteserien",
        "country": "Norway",
        "over_2_5_rate": 0.601,
        "edge": 7.5,
        "roi": 14.3,
        "recommended_stake": 1.5,
        "confidence": "HIGH"
    },
    88: {
        "name": "Eredivisie",
        "country": "Netherlands",
        "over_2_5_rate": 0.596,
        "edge": 6.9,
        "roi": 13.2,
        "recommended_stake": 1.5,
        "confidence": "HIGH"
    },
    39: {
        "name": "Premier League",
        "country": "England",
        "over_2_5_rate": 0.580,
        "edge": 5.4,
        "roi": 10.2,
        "recommended_stake": 1.0,
        "confidence": "HIGH"
    }
}

# Minimum acceptable odds
MIN_ODDS = 1.85
TARGET_ODDS = 1.90


class TotalsOverStrategy:
    """Strategy for betting Over 2.5 in high-scoring leagues"""

    def __init__(self):
        self.headers = {'x-apisports-key': API_KEY}

    def get_todays_matches(self) -> List[Dict]:
        """Fetch today's matches from profitable leagues"""
        today = datetime.now().strftime("%Y-%m-%d")
        matches = []

        for league_id, league_info in PROFITABLE_LEAGUES.items():
            url = f"{API_BASE}/fixtures"
            # Note: season 2025 is the current season (2025-26) as reported by API
            params = {
                'league': league_id,
                'date': today,
                'season': 2025
            }

            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    fixtures = data.get('response', [])

                    for fix in fixtures:
                        match = self._parse_fixture(fix, league_id, league_info)
                        if match:
                            matches.append(match)

            except Exception as e:
                print(f"Error fetching {league_info['name']}: {e}")

        return matches

    def _parse_fixture(self, fix: Dict, league_id: int, league_info: Dict) -> Dict:
        """Parse fixture data"""
        try:
            fixture = fix.get('fixture', {})
            teams = fix.get('teams', {})

            # Check if match hasn't started
            status = fixture.get('status', {}).get('short', '')
            if status in ['FT', 'AET', 'PEN', 'CANC', 'PST', 'ABD']:
                return None

            return {
                'fixture_id': fixture.get('id'),
                'date': fixture.get('date', '')[:10],
                'time': fixture.get('date', '')[11:16] if fixture.get('date') else '',
                'league_id': league_id,
                'league': league_info['name'],
                'country': league_info['country'],
                'home_team': teams.get('home', {}).get('name', ''),
                'away_team': teams.get('away', {}).get('name', ''),
                'historical_over_2_5': league_info['over_2_5_rate'],
                'edge': league_info['edge'],
                'expected_roi': league_info['roi'],
                'recommended_stake': league_info['recommended_stake'],
                'confidence': league_info['confidence'],
                'bet_type': 'Over 2.5 Goals',
                'min_odds': MIN_ODDS
            }
        except:
            return None

    def get_odds(self, fixture_id: int) -> Dict:
        """Fetch odds for a fixture"""
        url = f"{API_BASE}/odds"
        params = {
            'fixture': fixture_id,
            'bookmaker': 8  # Bet365
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                bookmakers = data.get('response', [{}])[0].get('bookmakers', [])

                for bm in bookmakers:
                    for bet in bm.get('bets', []):
                        if bet.get('name') == 'Over/Under':
                            for value in bet.get('values', []):
                                if value.get('value') == 'Over 2.5':
                                    return {
                                        'over_2_5': float(value.get('odd', 0)),
                                        'bookmaker': bm.get('name', 'Unknown')
                                    }
        except:
            pass

        return {'over_2_5': 0, 'bookmaker': 'N/A'}

    def generate_picks(self) -> List[Dict]:
        """Generate today's Over 2.5 picks"""
        print("=" * 80)
        print("SOCCER TOTALS OVER STRATEGY")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)

        matches = self.get_todays_matches()

        if not matches:
            print("\nNo matches found in profitable leagues today.")
            return []

        print(f"\n{len(matches)} matches found in profitable leagues:")
        print("-" * 80)

        picks = []

        for match in matches:
            odds_data = self.get_odds(match['fixture_id'])
            match['current_odds'] = odds_data['over_2_5']
            match['bookmaker'] = odds_data['bookmaker']

            # Check if odds meet minimum threshold
            if match['current_odds'] >= MIN_ODDS:
                match['status'] = 'RECOMMENDED'
                picks.append(match)
            elif match['current_odds'] > 0:
                match['status'] = 'ODDS_TOO_LOW'
            else:
                # Still recommend if odds not available - user can find manually
                match['status'] = 'RECOMMENDED (verify odds)'
                match['current_odds'] = TARGET_ODDS  # Assume typical odds
                picks.append(match)

            # Display match
            print(f"\n{match['league']} ({match['country']})")
            print(f"  {match['home_team']} vs {match['away_team']}")
            print(f"  Time: {match['time']}")
            print(f"  Historical Over 2.5: {match['historical_over_2_5']*100:.1f}%")
            print(f"  Edge: +{match['edge']:.1f}%")
            print(f"  Current Odds: {match['current_odds']:.2f}" if match['current_odds'] > 0 else "  Odds: Not available")
            print(f"  Status: {match['status']}")

        # Summary
        print("\n" + "=" * 80)
        print("RECOMMENDED PICKS")
        print("=" * 80)

        if picks:
            total_stake = 0
            for pick in picks:
                stake = pick['recommended_stake']
                total_stake += stake
                print(f"\n{pick['league']}: {pick['home_team']} vs {pick['away_team']}")
                print(f"   Bet: Over 2.5 Goals @ {pick['current_odds']:.2f}")
                print(f"   Stake: {stake} units")
                print(f"   Edge: +{pick['edge']:.1f}% | Expected ROI: +{pick['expected_roi']:.1f}%")

            print(f"\n{'=' * 40}")
            print(f"Total Picks: {len(picks)}")
            print(f"Total Stake: {total_stake} units")
        else:
            print("\nNo picks meet criteria today.")

        return picks

    def save_picks(self, picks: List[Dict], output_dir: str = None):
        """Save picks to JSON"""
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'reports',
                datetime.now().strftime('%Y-%m-%d')
            )

        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, 'soccer_totals_picks.json')

        with open(output_path, 'w') as f:
            json.dump({
                'date': datetime.now().strftime('%Y-%m-%d'),
                'strategy': 'Over 2.5 in High-Scoring Leagues',
                'picks': picks,
                'total_picks': len(picks),
                'leagues': list(PROFITABLE_LEAGUES.keys())
            }, f, indent=2)

        print(f"\nPicks saved to: {output_path}")
        return output_path


def main():
    strategy = TotalsOverStrategy()
    picks = strategy.generate_picks()

    if picks:
        strategy.save_picks(picks)


if __name__ == "__main__":
    main()
