#!/usr/bin/env python3
"""
US Sportsbooks Integration - DraftKings & FanDuel Only
Focused integration for US soccer betting markets
"""

import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import csv

class USSportsbooksAPI:
    """Integration specifically for DraftKings and FanDuel via The Odds API"""

    def __init__(self, api_key: str = "fc8b43bb8508b51b52b52fd1827eaaf4"):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"

        # US bookmakers only
        self.us_bookmakers = ['draftkings', 'fanduel']

        # US-focused soccer leagues
        self.us_soccer_leagues = [
            'soccer_usa_mls',  # Major League Soccer
            'soccer_epl',      # Premier League (popular in US)
            'soccer_uefa_champs_league',  # Champions League
            'soccer_fifa_world_cup'       # World Cup
        ]

    def get_us_soccer_odds(self, date_filter: str = None) -> Dict[str, List]:
        """Get soccer odds from DraftKings and FanDuel only"""

        print("🇺🇸 Fetching US Sportsbook Odds (DraftKings & FanDuel)")
        print("=" * 50)

        all_odds = {}

        for league in self.us_soccer_leagues:
            print(f"📊 Getting {league} odds...")

            try:
                url = f"{self.base_url}/sports/{league}/odds"
                params = {
                    'api_key': self.api_key,
                    'regions': 'us',  # US region only
                    'markets': 'h2h,totals',  # Main markets
                    'bookmakers': ','.join(self.us_bookmakers),
                    'oddsFormat': 'american',  # US odds format
                    'dateFormat': 'iso'
                }

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    all_odds[league] = data
                    print(f"   ✅ {len(data)} matches found")
                else:
                    print(f"   ❌ Error {response.status_code}")
                    all_odds[league] = []

            except Exception as e:
                print(f"   ❌ Error: {e}")
                all_odds[league] = []

        return all_odds

    def analyze_us_odds_comparison(self, odds_data: Dict) -> List[Dict]:
        """Compare DraftKings vs FanDuel odds"""

        comparisons = []

        for league, matches in odds_data.items():
            for match in matches:
                comparison = self.compare_dk_vs_fd(match, league)
                if comparison:
                    comparisons.append(comparison)

        return comparisons

    def compare_dk_vs_fd(self, match: Dict, league: str) -> Optional[Dict]:
        """Compare DraftKings vs FanDuel for a single match"""

        comparison = {
            'league': league.replace('soccer_', '').replace('_', ' ').title(),
            'home_team': match.get('home_team'),
            'away_team': match.get('away_team'),
            'commence_time': match.get('commence_time'),
            'dk_available': False,
            'fd_available': False
        }

        dk_odds = {}
        fd_odds = {}

        # Extract odds from each bookmaker
        for bookmaker in match.get('bookmakers', []):
            bookie_name = bookmaker.get('title', '').lower()

            if 'draftkings' in bookie_name:
                comparison['dk_available'] = True
                dk_odds = self.extract_bookmaker_odds(bookmaker)

            elif 'fanduel' in bookie_name:
                comparison['fd_available'] = True
                fd_odds = self.extract_bookmaker_odds(bookmaker)

        # Only proceed if we have both bookmakers
        if not (comparison['dk_available'] and comparison['fd_available']):
            return None

        # Compare odds
        comparison.update(self.calculate_odds_differences(dk_odds, fd_odds))

        return comparison

    def extract_bookmaker_odds(self, bookmaker: Dict) -> Dict:
        """Extract odds from a bookmaker's data"""

        odds = {}

        for market in bookmaker.get('markets', []):
            market_key = market.get('key')

            if market_key == 'h2h':
                for outcome in market.get('outcomes', []):
                    name = outcome.get('name', '').lower()
                    price = outcome.get('price', 0)

                    if 'draw' in name:
                        odds['draw'] = price
                    elif len(odds) == 0:  # First team is home
                        odds['home'] = price
                    else:  # Second team is away
                        odds['away'] = price

            elif market_key == 'totals':
                for outcome in market.get('outcomes', []):
                    name = outcome.get('name', '').lower()
                    point = outcome.get('point', 0)
                    price = outcome.get('price', 0)

                    if point == 2.5:  # Focus on 2.5 goals
                        if 'over' in name:
                            odds['over_2.5'] = price
                        elif 'under' in name:
                            odds['under_2.5'] = price

        return odds

    def calculate_odds_differences(self, dk_odds: Dict, fd_odds: Dict) -> Dict:
        """Calculate differences between DraftKings and FanDuel odds"""

        differences = {}

        # Compare each market
        markets = ['home', 'draw', 'away', 'over_2.5', 'under_2.5']

        for market in markets:
            dk_price = dk_odds.get(market)
            fd_price = fd_odds.get(market)

            if dk_price is not None and fd_price is not None:
                differences[f'dk_{market}'] = dk_price
                differences[f'fd_{market}'] = fd_price

                # Calculate which is better (higher American odds = better)
                if dk_price > fd_price:
                    differences[f'{market}_better'] = 'DraftKings'
                    differences[f'{market}_advantage'] = dk_price - fd_price
                elif fd_price > dk_price:
                    differences[f'{market}_better'] = 'FanDuel'
                    differences[f'{market}_advantage'] = fd_price - dk_price
                else:
                    differences[f'{market}_better'] = 'Equal'
                    differences[f'{market}_advantage'] = 0

        return differences

    def generate_us_sportsbooks_report(self, comparisons: List[Dict]) -> str:
        """Generate report comparing DraftKings vs FanDuel"""

        date_str = datetime.now().strftime("%Y-%m-%d")

        report = f"🇺🇸 US SPORTSBOOKS COMPARISON REPORT - {date_str}\n"
        report += "=" * 60 + "\n"
        report += "Comparing DraftKings vs FanDuel Soccer Odds\n\n"

        if not comparisons:
            report += "❌ No matches found with both DraftKings and FanDuel odds\n"
            report += "💡 This could be because:\n"
            report += "   • Limited soccer coverage on US sportsbooks\n"
            report += "   • Matches not yet available for betting\n"
            report += "   • Regional restrictions\n"
            return report

        dk_better_count = 0
        fd_better_count = 0

        for comparison in comparisons[:10]:  # Top 10 matches
            report += f"⚽ {comparison['home_team']} vs {comparison['away_team']}\n"
            report += f"   🏆 {comparison['league']} | 🕒 {comparison.get('commence_time', 'TBD')}\n"

            # Show H2H comparison
            markets = ['home', 'draw', 'away']
            for market in markets:
                dk_key = f'dk_{market}'
                fd_key = f'fd_{market}'
                better_key = f'{market}_better'

                if dk_key in comparison and fd_key in comparison:
                    dk_odds = comparison[dk_key]
                    fd_odds = comparison[fd_key]
                    better = comparison.get(better_key, 'Equal')

                    if better == 'DraftKings':
                        dk_better_count += 1
                        marker = " 🥇"
                    elif better == 'FanDuel':
                        fd_better_count += 1
                        marker = " 🥇"
                    else:
                        marker = ""

                    report += f"   {market.title()}: DK {dk_odds:+d} | FD {fd_odds:+d}"
                    if better != 'Equal':
                        report += f" | {better} better{marker}"
                    report += "\n"

            # Show totals if available
            if 'dk_over_2.5' in comparison:
                dk_over = comparison['dk_over_2.5']
                fd_over = comparison['fd_over_2.5']
                over_better = comparison.get('over_2.5_better', 'Equal')

                report += f"   Over 2.5: DK {dk_over:+d} | FD {fd_over:+d}"
                if over_better != 'Equal':
                    report += f" | {over_better} better"
                report += "\n"

            report += "\n"

        # Summary
        report += f"📊 SUMMARY:\n"
        report += f"   Total Matches Compared: {len(comparisons)}\n"
        report += f"   DraftKings Better: {dk_better_count} markets\n"
        report += f"   FanDuel Better: {fd_better_count} markets\n"

        if dk_better_count + fd_better_count > 0:
            dk_pct = dk_better_count / (dk_better_count + fd_better_count) * 100
            fd_pct = fd_better_count / (dk_better_count + fd_better_count) * 100
            report += f"   DraftKings Win Rate: {dk_pct:.1f}%\n"
            report += f"   FanDuel Win Rate: {fd_pct:.1f}%\n"

        return report

    def save_us_odds_data(self, comparisons: List[Dict]):
        """Save US sportsbooks comparison to CSV"""

        if not comparisons:
            print("⚠️ No US sportsbooks data to save")
            return

        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"output reports/us_sportsbooks_comparison_{date_str}.csv"

        # Prepare data for CSV
        csv_data = []
        for comp in comparisons:
            row = {
                'date': date_str,
                'league': comp['league'],
                'home_team': comp['home_team'],
                'away_team': comp['away_team'],
                'commence_time': comp.get('commence_time', ''),
                'dk_available': comp['dk_available'],
                'fd_available': comp['fd_available']
            }

            # Add odds comparisons
            markets = ['home', 'draw', 'away', 'over_2.5', 'under_2.5']
            for market in markets:
                row[f'dk_{market}'] = comp.get(f'dk_{market}', '')
                row[f'fd_{market}'] = comp.get(f'fd_{market}', '')
                row[f'{market}_better'] = comp.get(f'{market}_better', '')
                row[f'{market}_advantage'] = comp.get(f'{market}_advantage', '')

            csv_data.append(row)

        # Save to CSV
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False)

        print(f"💾 US sportsbooks data saved: {filename}")
        print(f"📊 {len(csv_data)} match comparisons saved")

def main():
    """Test US sportsbooks integration"""

    print("🇺🇸 Testing US Sportsbooks Integration...")

    # Initialize client
    us_books = USSportsbooksAPI()

    # Get odds from DraftKings and FanDuel
    odds_data = us_books.get_us_soccer_odds()

    # Compare the odds
    comparisons = us_books.analyze_us_odds_comparison(odds_data)

    # Generate report
    report = us_books.generate_us_sportsbooks_report(comparisons)

    # Save data
    us_books.save_us_odds_data(comparisons)

    # Save report
    date_str = datetime.now().strftime("%Y%m%d")
    report_file = f"output reports/us_sportsbooks_report_{date_str}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"\n✅ US Sportsbooks analysis complete!")
    print(f"📄 Report saved: {report_file}")
    print(f"📊 {len(comparisons)} matches compared")

    # Show preview
    print("\n📄 Report Preview:")
    print(report[:800] + "..." if len(report) > 800 else report)

if __name__ == "__main__":
    main()