#!/usr/bin/env python3
"""
Enhanced Odds Analyzer - Integrates The Odds API with existing system
"""

import pandas as pd
import json
from datetime import datetime
from odds_api_integration import OddsAPIClient
from typing import Dict, List

class EnhancedOddsAnalyzer:
    """Combine The Odds API with existing FootyStats data for comprehensive analysis"""

    def __init__(self, odds_api_key: str = "fc8b43bb8508b51b52b52fd1827eaaf4"):
        self.odds_client = OddsAPIClient(odds_api_key)
        self.date_str = datetime.now().strftime("%Y%m%d")

    def generate_enhanced_daily_odds_report(self):
        """Generate comprehensive daily odds report combining all sources"""

        print("🔍 Generating Enhanced Daily Odds Report...")
        print("=" * 50)

        # Get major league odds
        major_leagues = [
            'soccer_epl',  # Premier League
            'soccer_spain_la_liga',  # La Liga
            'soccer_italy_serie_a',  # Serie A
            'soccer_germany_bundesliga',  # Bundesliga
            'soccer_france_ligue_one',  # Ligue 1
            'soccer_uefa_champs_league',  # Champions League
            'soccer_usa_mls'  # MLS
        ]

        enhanced_data = []

        for league in major_leagues:
            print(f"📊 Processing {league}...")

            # Get odds from The Odds API
            odds_data = self.odds_client.get_odds_for_sport(league, ['h2h', 'totals', 'btts'])

            if odds_data:
                processed_matches = self.process_league_odds(league, odds_data)
                enhanced_data.extend(processed_matches)

        # Save comprehensive data
        self.save_enhanced_odds_data(enhanced_data)

        # Generate value opportunities report
        value_report = self.generate_value_opportunities_report(enhanced_data)

        return enhanced_data, value_report

    def process_league_odds(self, league: str, odds_data: List[Dict]) -> List[Dict]:
        """Process odds data for a specific league"""

        processed_matches = []

        for match in odds_data:
            try:
                match_data = {
                    'date': self.date_str,
                    'league': league.replace('soccer_', '').replace('_', ' ').title(),
                    'match_id': match.get('id'),
                    'home_team': match.get('home_team'),
                    'away_team': match.get('away_team'),
                    'commence_time': match.get('commence_time'),
                    'sport_title': match.get('sport_title')
                }

                # Extract best odds from all bookmakers
                odds_analysis = self.extract_best_odds(match.get('bookmakers', []))
                match_data.update(odds_analysis)

                # Calculate arbitrage opportunities
                arbitrage = self.calculate_arbitrage_opportunities(odds_analysis)
                match_data.update(arbitrage)

                processed_matches.append(match_data)

            except Exception as e:
                print(f"⚠️ Error processing match: {e}")
                continue

        return processed_matches

    def extract_best_odds(self, bookmakers: List[Dict]) -> Dict:
        """Extract best odds across all bookmakers for each market"""

        analysis = {
            'bookmaker_count': len(bookmakers),
            'markets_available': []
        }

        # Track all odds for each outcome
        h2h_odds = {'home': [], 'draw': [], 'away': []}
        totals_odds = {'over_2.5': [], 'under_2.5': []}
        btts_odds = {'yes': [], 'no': []}

        for bookmaker in bookmakers:
            bookmaker_name = bookmaker.get('title', 'Unknown')

            for market in bookmaker.get('markets', []):
                market_key = market.get('key')
                analysis['markets_available'].append(market_key)

                if market_key == 'h2h':
                    for outcome in market.get('outcomes', []):
                        name = outcome.get('name', '').lower()
                        price = outcome.get('price', 0)

                        if any(x in name for x in ['home', match.get('home_team', '').lower()]):
                            h2h_odds['home'].append({'bookmaker': bookmaker_name, 'odds': price})
                        elif 'draw' in name:
                            h2h_odds['draw'].append({'bookmaker': bookmaker_name, 'odds': price})
                        else:
                            h2h_odds['away'].append({'bookmaker': bookmaker_name, 'odds': price})

                elif market_key == 'totals':
                    for outcome in market.get('outcomes', []):
                        point = outcome.get('point', 0)
                        name = outcome.get('name', '').lower()
                        price = outcome.get('price', 0)

                        if point == 2.5:
                            if 'over' in name:
                                totals_odds['over_2.5'].append({'bookmaker': bookmaker_name, 'odds': price})
                            elif 'under' in name:
                                totals_odds['under_2.5'].append({'bookmaker': bookmaker_name, 'odds': price})

                elif market_key == 'btts':
                    for outcome in market.get('outcomes', []):
                        name = outcome.get('name', '').lower()
                        price = outcome.get('price', 0)

                        if 'yes' in name:
                            btts_odds['yes'].append({'bookmaker': bookmaker_name, 'odds': price})
                        elif 'no' in name:
                            btts_odds['no'].append({'bookmaker': bookmaker_name, 'odds': price})

        # Find best odds for each outcome
        for outcome, odds_list in h2h_odds.items():
            if odds_list:
                best = max(odds_list, key=lambda x: x['odds'])
                worst = min(odds_list, key=lambda x: x['odds'])
                avg = sum(x['odds'] for x in odds_list) / len(odds_list)

                analysis[f'h2h_{outcome}_best'] = best['odds']
                analysis[f'h2h_{outcome}_best_bookmaker'] = best['bookmaker']
                analysis[f'h2h_{outcome}_worst'] = worst['odds']
                analysis[f'h2h_{outcome}_avg'] = round(avg, 3)
                analysis[f'h2h_{outcome}_spread'] = round(best['odds'] - worst['odds'], 3)
                analysis[f'h2h_{outcome}_value'] = round((best['odds'] - avg) / avg * 100, 2)

        for outcome, odds_list in totals_odds.items():
            if odds_list:
                best = max(odds_list, key=lambda x: x['odds'])
                avg = sum(x['odds'] for x in odds_list) / len(odds_list)

                analysis[f'totals_{outcome}_best'] = best['odds']
                analysis[f'totals_{outcome}_best_bookmaker'] = best['bookmaker']
                analysis[f'totals_{outcome}_avg'] = round(avg, 3)
                analysis[f'totals_{outcome}_value'] = round((best['odds'] - avg) / avg * 100, 2)

        for outcome, odds_list in btts_odds.items():
            if odds_list:
                best = max(odds_list, key=lambda x: x['odds'])
                avg = sum(x['odds'] for x in odds_list) / len(odds_list)

                analysis[f'btts_{outcome}_best'] = best['odds']
                analysis[f'btts_{outcome}_best_bookmaker'] = best['bookmaker']
                analysis[f'btts_{outcome}_avg'] = round(avg, 3)
                analysis[f'btts_{outcome}_value'] = round((best['odds'] - avg) / avg * 100, 2)

        # Remove duplicates from markets
        analysis['markets_available'] = list(set(analysis['markets_available']))

        return analysis

    def calculate_arbitrage_opportunities(self, odds_data: Dict) -> Dict:
        """Calculate arbitrage opportunities"""

        arbitrage = {}

        # H2H arbitrage
        home_odds = odds_data.get('h2h_home_best', 0)
        draw_odds = odds_data.get('h2h_draw_best', 0)
        away_odds = odds_data.get('h2h_away_best', 0)

        if all([home_odds, away_odds]):
            # Calculate arbitrage percentage
            implied_prob_sum = (1/home_odds) + (1/away_odds)
            if draw_odds:
                implied_prob_sum += (1/draw_odds)

            arbitrage['h2h_arbitrage_pct'] = round((1 - implied_prob_sum) * 100, 3)
            arbitrage['h2h_arbitrage_opportunity'] = implied_prob_sum < 1

            if arbitrage['h2h_arbitrage_opportunity']:
                # Calculate optimal stakes
                total_stake = 100  # $100 example
                home_stake = round(total_stake / (home_odds * implied_prob_sum), 2)
                away_stake = round(total_stake / (away_odds * implied_prob_sum), 2)
                arbitrage['h2h_home_stake'] = home_stake
                arbitrage['h2h_away_stake'] = away_stake

                if draw_odds:
                    draw_stake = round(total_stake / (draw_odds * implied_prob_sum), 2)
                    arbitrage['h2h_draw_stake'] = draw_stake

        # BTTS arbitrage
        btts_yes = odds_data.get('btts_yes_best', 0)
        btts_no = odds_data.get('btts_no_best', 0)

        if btts_yes and btts_no:
            btts_implied_sum = (1/btts_yes) + (1/btts_no)
            arbitrage['btts_arbitrage_pct'] = round((1 - btts_implied_sum) * 100, 3)
            arbitrage['btts_arbitrage_opportunity'] = btts_implied_sum < 1

        return arbitrage

    def save_enhanced_odds_data(self, enhanced_data: List[Dict]):
        """Save enhanced odds data to CSV"""

        if not enhanced_data:
            print("⚠️ No enhanced odds data to save")
            return

        # Convert to DataFrame
        df = pd.DataFrame(enhanced_data)

        # Save to CSV
        filename = f"output reports/enhanced_odds_analysis_{self.date_str}.csv"
        df.to_csv(filename, index=False)

        print(f"💾 Enhanced odds data saved: {filename}")
        print(f"📊 {len(enhanced_data)} matches analyzed across {df['league'].nunique()} leagues")

        return filename

    def generate_value_opportunities_report(self, enhanced_data: List[Dict]) -> str:
        """Generate report highlighting value opportunities"""

        report = f"💰 VALUE OPPORTUNITIES REPORT - {datetime.now().strftime('%Y-%m-%d')}\n"
        report += "=" * 60 + "\n"
        report += "Data Source: The Odds API + Enhanced Analysis\n\n"

        # Find matches with significant value
        value_threshold = 5.0  # 5% value threshold

        value_opportunities = []

        for match in enhanced_data:
            opportunities = []

            # Check H2H value
            for outcome in ['home', 'draw', 'away']:
                value_key = f'h2h_{outcome}_value'
                if match.get(value_key, 0) > value_threshold:
                    opportunities.append({
                        'market': f'H2H {outcome.title()}',
                        'value': match[value_key],
                        'best_odds': match.get(f'h2h_{outcome}_best'),
                        'bookmaker': match.get(f'h2h_{outcome}_best_bookmaker'),
                        'avg_odds': match.get(f'h2h_{outcome}_avg')
                    })

            # Check BTTS value
            for outcome in ['yes', 'no']:
                value_key = f'btts_{outcome}_value'
                if match.get(value_key, 0) > value_threshold:
                    opportunities.append({
                        'market': f'BTTS {outcome.title()}',
                        'value': match[value_key],
                        'best_odds': match.get(f'btts_{outcome}_best'),
                        'bookmaker': match.get(f'btts_{outcome}_best_bookmaker'),
                        'avg_odds': match.get(f'btts_{outcome}_avg')
                    })

            # Check arbitrage
            if match.get('h2h_arbitrage_opportunity'):
                opportunities.append({
                    'market': 'Arbitrage H2H',
                    'value': abs(match.get('h2h_arbitrage_pct', 0)),
                    'type': 'arbitrage'
                })

            if opportunities:
                match['value_opportunities'] = opportunities
                value_opportunities.append(match)

        # Generate report content
        if value_opportunities:
            report += f"🎯 FOUND {len(value_opportunities)} MATCHES WITH VALUE OPPORTUNITIES!\n\n"

            for match in value_opportunities[:10]:  # Top 10
                report += f"⚽ {match['home_team']} vs {match['away_team']}\n"
                report += f"   🏆 {match['league']} | 🕒 {match.get('commence_time', 'TBD')}\n"
                report += f"   📊 {match['bookmaker_count']} bookmakers compared\n"

                for opp in match['value_opportunities']:
                    if opp.get('type') == 'arbitrage':
                        report += f"   🔥 ARBITRAGE: {opp['value']:.2f}% profit guaranteed!\n"
                    else:
                        report += f"   💰 {opp['market']}: {opp['best_odds']:.2f} @ {opp['bookmaker']} "
                        report += f"({opp['value']:+.1f}% value vs {opp['avg_odds']:.2f} avg)\n"

                report += "\n"

        else:
            report += "📊 No significant value opportunities found today\n"
            report += "💡 Recommendations:\n"
            report += "   • Lower value threshold (currently 5%)\n"
            report += "   • Check more leagues/markets\n"
            report += "   • Monitor odds movement throughout day\n"

        report += f"\n📈 SUMMARY:\n"
        report += f"   Total Matches Analyzed: {len(enhanced_data)}\n"
        report += f"   Value Opportunities: {len(value_opportunities)}\n"
        report += f"   Success Rate: {len(value_opportunities)/len(enhanced_data)*100 if enhanced_data else 0:.1f}%\n"

        # Save report
        report_filename = f"output reports/value_opportunities_enhanced_{self.date_str}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)

        print(f"📄 Value opportunities report saved: {report_filename}")

        return report

def main():
    """Generate enhanced odds analysis"""

    analyzer = EnhancedOddsAnalyzer()

    print("🚀 Generating Enhanced Odds Analysis...")

    enhanced_data, value_report = analyzer.generate_enhanced_daily_odds_report()

    print(f"\n✅ Enhanced odds analysis complete!")
    print(f"📊 {len(enhanced_data)} matches analyzed")

    # Show sample of value report
    print("\n📄 Value Opportunities Preview:")
    print(value_report[:500] + "..." if len(value_report) > 500 else value_report)

if __name__ == "__main__":
    main()