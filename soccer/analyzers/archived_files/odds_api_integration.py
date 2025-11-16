#!/usr/bin/env python3
"""
The Odds API Integration
https://the-odds-api.com/

Provides comprehensive odds data from multiple bookmakers for enhanced betting analysis
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import logging

class OddsAPIClient:
    """Client for The Odds API - Enhanced odds data from multiple bookmakers"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
        self.session = requests.Session()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Supported markets for soccer
        self.soccer_markets = [
            'h2h',  # Head to head (match winner)
            'spreads',  # Point spreads (Asian handicap)
            'totals',  # Over/under totals
            'btts',  # Both teams to score
            'draw_no_bet',  # Draw no bet
            'double_chance',  # Double chance
            'team_totals',  # Team total goals
            'h2h_lay',  # Lay betting
            'correct_score',  # Correct score
            'first_goal_scorer',  # First goal scorer
            'anytime_goal_scorer'  # Anytime goal scorer
        ]

        # US bookmakers only - DraftKings and FanDuel
        self.preferred_bookmakers = [
            'draftkings',  # US market leader
            'fanduel'      # US market leader
        ]

    def get_api_usage(self):
        """Check API usage and remaining quota"""
        try:
            # The usage endpoint (if available)
            url = f"{self.base_url}/usage"
            params = {'api_key': self.api_key}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Usage check failed: {response.status_code}")
                return None

        except Exception as e:
            self.logger.error(f"Usage check error: {e}")
            return None

    def get_soccer_sports(self):
        """Get all available soccer sports/leagues"""
        try:
            url = f"{self.base_url}/sports"
            params = {'api_key': self.api_key}

            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Filter for soccer sports
                soccer_sports = [sport for sport in data if 'soccer' in sport.get('group', '').lower()]
                return soccer_sports
            else:
                self.logger.error(f"Sports API error: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"Sports API error: {e}")
            return []

    def get_odds_for_sport(self, sport_key: str, markets: List[str] = None,
                          bookmakers: List[str] = None, regions: str = 'us,uk,eu') -> List[Dict]:
        """Get odds for a specific sport"""

        if markets is None:
            markets = ['h2h', 'totals', 'btts']  # Most common markets

        if bookmakers is None:
            bookmakers = self.preferred_bookmakers[:5]  # Top 5 to conserve API calls

        try:
            url = f"{self.base_url}/sports/{sport_key}/odds"
            params = {
                'api_key': self.api_key,
                'regions': regions,
                'markets': ','.join(markets),
                'bookmakers': ','.join(bookmakers),
                'oddsFormat': 'decimal',
                'dateFormat': 'iso'
            }

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✅ {sport_key}: {len(data)} matches with odds")
                return data
            else:
                self.logger.error(f"❌ {sport_key} odds error: {response.status_code}")
                return []

        except Exception as e:
            self.logger.error(f"❌ {sport_key} odds error: {e}")
            return []

    def get_enhanced_soccer_odds(self, sport_keys: List[str] = None) -> Dict[str, List]:
        """Get comprehensive soccer odds from multiple leagues"""

        if sport_keys is None:
            # Default major soccer leagues
            sport_keys = [
                'soccer_epl',  # English Premier League
                'soccer_spain_la_liga',  # Spanish La Liga
                'soccer_italy_serie_a',  # Italian Serie A
                'soccer_germany_bundesliga',  # German Bundesliga
                'soccer_france_ligue_one',  # French Ligue 1
                'soccer_uefa_champs_league',  # Champions League
                'soccer_uefa_europa_league',  # Europa League
                'soccer_fifa_world_cup',  # World Cup
                'soccer_usa_mls'  # MLS
            ]

        all_odds = {}

        for sport_key in sport_keys:
            self.logger.info(f"📊 Fetching odds for {sport_key}...")

            # Get different market types
            h2h_odds = self.get_odds_for_sport(sport_key, ['h2h'])
            totals_odds = self.get_odds_for_sport(sport_key, ['totals'])
            btts_odds = self.get_odds_for_sport(sport_key, ['btts'])

            # Combine all market data
            combined_odds = self.combine_market_data(h2h_odds, totals_odds, btts_odds)

            all_odds[sport_key] = combined_odds

            # Rate limiting
            time.sleep(1)

        return all_odds

    def combine_market_data(self, h2h_data: List, totals_data: List, btts_data: List) -> List[Dict]:
        """Combine different market types for comprehensive odds"""

        combined = []

        # Use h2h as base and merge other markets
        for match in h2h_data:
            match_id = match.get('id')
            enhanced_match = match.copy()

            # Add totals data
            totals_match = next((m for m in totals_data if m.get('id') == match_id), None)
            if totals_match:
                enhanced_match['totals_markets'] = totals_match.get('bookmakers', [])

            # Add BTTS data
            btts_match = next((m for m in btts_data if m.get('id') == match_id), None)
            if btts_match:
                enhanced_match['btts_markets'] = btts_match.get('bookmakers', [])

            combined.append(enhanced_match)

        return combined

    def analyze_odds_value(self, odds_data: List[Dict]) -> List[Dict]:
        """Analyze odds for value betting opportunities"""

        value_opportunities = []

        for match in odds_data:
            try:
                # Extract match info
                match_info = {
                    'match_id': match.get('id'),
                    'sport_title': match.get('sport_title'),
                    'commence_time': match.get('commence_time'),
                    'home_team': match.get('home_team'),
                    'away_team': match.get('away_team')
                }

                # Analyze h2h odds
                h2h_analysis = self.analyze_h2h_odds(match.get('bookmakers', []))
                if h2h_analysis:
                    match_info.update(h2h_analysis)

                # Analyze totals odds
                totals_analysis = self.analyze_totals_odds(match.get('totals_markets', []))
                if totals_analysis:
                    match_info.update(totals_analysis)

                # Analyze BTTS odds
                btts_analysis = self.analyze_btts_odds(match.get('btts_markets', []))
                if btts_analysis:
                    match_info.update(btts_analysis)

                value_opportunities.append(match_info)

            except Exception as e:
                self.logger.warning(f"Match analysis error: {e}")
                continue

        return value_opportunities

    def analyze_h2h_odds(self, bookmakers: List[Dict]) -> Dict:
        """Analyze head-to-head odds for value"""

        if not bookmakers:
            return {}

        # Collect all odds for comparison
        home_odds = []
        draw_odds = []
        away_odds = []

        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'h2h':
                    for outcome in market.get('outcomes', []):
                        if outcome.get('name') == bookmakers[0].get('title', ''):  # Home team
                            home_odds.append((bookmaker.get('title'), outcome.get('price')))
                        elif 'draw' in outcome.get('name', '').lower():
                            draw_odds.append((bookmaker.get('title'), outcome.get('price')))
                        else:  # Away team
                            away_odds.append((bookmaker.get('title'), outcome.get('price')))

        analysis = {}

        if home_odds:
            best_home = max(home_odds, key=lambda x: x[1])
            avg_home = sum(x[1] for x in home_odds) / len(home_odds)
            analysis['h2h_home_best'] = {'bookmaker': best_home[0], 'odds': best_home[1]}
            analysis['h2h_home_avg'] = avg_home
            analysis['h2h_home_value'] = (best_home[1] - avg_home) / avg_home * 100

        if draw_odds:
            best_draw = max(draw_odds, key=lambda x: x[1])
            avg_draw = sum(x[1] for x in draw_odds) / len(draw_odds)
            analysis['h2h_draw_best'] = {'bookmaker': best_draw[0], 'odds': best_draw[1]}
            analysis['h2h_draw_avg'] = avg_draw
            analysis['h2h_draw_value'] = (best_draw[1] - avg_draw) / avg_draw * 100

        if away_odds:
            best_away = max(away_odds, key=lambda x: x[1])
            avg_away = sum(x[1] for x in away_odds) / len(away_odds)
            analysis['h2h_away_best'] = {'bookmaker': best_away[0], 'odds': best_away[1]}
            analysis['h2h_away_avg'] = avg_away
            analysis['h2h_away_value'] = (best_away[1] - avg_away) / avg_away * 100

        return analysis

    def analyze_totals_odds(self, bookmakers: List[Dict]) -> Dict:
        """Analyze over/under totals for value"""

        analysis = {}

        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'totals':
                    # Find common totals like 2.5 goals
                    for outcome in market.get('outcomes', []):
                        point = outcome.get('point', 0)
                        name = outcome.get('name', '')
                        price = outcome.get('price', 0)

                        if point == 2.5:  # Most common total
                            key = f"total_25_{name.lower()}"
                            if key not in analysis:
                                analysis[key] = []
                            analysis[key].append({'bookmaker': bookmaker.get('title'), 'odds': price})

        # Find best odds for each total
        for key, odds_list in analysis.items():
            if odds_list:
                best = max(odds_list, key=lambda x: x['odds'])
                avg = sum(x['odds'] for x in odds_list) / len(odds_list)
                analysis[f"{key}_best"] = best
                analysis[f"{key}_avg"] = avg
                analysis[f"{key}_value"] = (best['odds'] - avg) / avg * 100

        return analysis

    def analyze_btts_odds(self, bookmakers: List[Dict]) -> Dict:
        """Analyze Both Teams to Score odds"""

        btts_yes_odds = []
        btts_no_odds = []

        for bookmaker in bookmakers:
            for market in bookmaker.get('markets', []):
                if market.get('key') == 'btts':
                    for outcome in market.get('outcomes', []):
                        name = outcome.get('name', '').lower()
                        price = outcome.get('price', 0)

                        if 'yes' in name:
                            btts_yes_odds.append({'bookmaker': bookmaker.get('title'), 'odds': price})
                        elif 'no' in name:
                            btts_no_odds.append({'bookmaker': bookmaker.get('title'), 'odds': price})

        analysis = {}

        if btts_yes_odds:
            best_yes = max(btts_yes_odds, key=lambda x: x['odds'])
            avg_yes = sum(x['odds'] for x in btts_yes_odds) / len(btts_yes_odds)
            analysis['btts_yes_best'] = best_yes
            analysis['btts_yes_avg'] = avg_yes
            analysis['btts_yes_value'] = (best_yes['odds'] - avg_yes) / avg_yes * 100

        if btts_no_odds:
            best_no = max(btts_no_odds, key=lambda x: x['odds'])
            avg_no = sum(x['odds'] for x in btts_no_odds) / len(btts_no_odds)
            analysis['btts_no_best'] = best_no
            analysis['btts_no_avg'] = avg_no
            analysis['btts_no_value'] = (best_no['odds'] - avg_no) / avg_no * 100

        return analysis

    def generate_odds_comparison_report(self, enhanced_odds: Dict) -> str:
        """Generate comprehensive odds comparison report"""

        report = "📊 ENHANCED ODDS ANALYSIS REPORT\n"
        report += "=" * 50 + "\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"Data Source: The Odds API (the-odds-api.com)\n\n"

        total_matches = 0
        total_value_opportunities = 0

        for sport_key, matches in enhanced_odds.items():
            report += f"\n🏆 {sport_key.upper().replace('_', ' ')}\n"
            report += "-" * 30 + "\n"

            if not matches:
                report += "   No matches available\n"
                continue

            sport_matches = 0
            sport_opportunities = 0

            for match in matches:
                sport_matches += 1
                total_matches += 1

                report += f"\n⚽ {match.get('home_team', 'TBD')} vs {match.get('away_team', 'TBD')}\n"
                report += f"   🕒 {match.get('commence_time', 'TBD')}\n"

                # H2H odds
                if 'h2h_home_best' in match:
                    home_value = match.get('h2h_home_value', 0)
                    draw_value = match.get('h2h_draw_value', 0)
                    away_value = match.get('h2h_away_value', 0)

                    if any(v > 5 for v in [home_value, draw_value, away_value]):  # 5%+ value
                        sport_opportunities += 1
                        total_value_opportunities += 1
                        report += "   💰 VALUE OPPORTUNITY FOUND!\n"

                    report += f"   🏠 Home: {match['h2h_home_best']['odds']:.2f} @ {match['h2h_home_best']['bookmaker']} ({home_value:+.1f}%)\n"

                    if 'h2h_draw_best' in match:
                        report += f"   ⚖️ Draw: {match['h2h_draw_best']['odds']:.2f} @ {match['h2h_draw_best']['bookmaker']} ({draw_value:+.1f}%)\n"

                    report += f"   🚌 Away: {match['h2h_away_best']['odds']:.2f} @ {match['h2h_away_best']['bookmaker']} ({away_value:+.1f}%)\n"

                # BTTS odds
                if 'btts_yes_best' in match:
                    yes_value = match.get('btts_yes_value', 0)
                    report += f"   🎯 BTTS Yes: {match['btts_yes_best']['odds']:.2f} @ {match['btts_yes_best']['bookmaker']} ({yes_value:+.1f}%)\n"

            report += f"\n📊 {sport_key}: {sport_matches} matches, {sport_opportunities} value opportunities\n"

        report += f"\n🎯 SUMMARY:\n"
        report += f"   Total Matches: {total_matches}\n"
        report += f"   Value Opportunities: {total_value_opportunities}\n"
        report += f"   Success Rate: {(total_value_opportunities/total_matches*100) if total_matches > 0 else 0:.1f}%\n"

        return report

def main():
    """Test the Odds API integration"""

    # API key for the-odds-api.com
    API_KEY = "fc8b43bb8508b51b52b52fd1827eaaf4"

    # Initialize client
    odds_client = OddsAPIClient(API_KEY)

    print("🚀 Testing Odds API Integration...")

    # Check usage
    usage = odds_client.get_api_usage()
    if usage:
        print(f"📊 API Usage: {usage}")

    # Get available sports
    sports = odds_client.get_soccer_sports()
    print(f"⚽ Available soccer sports: {len(sports)}")

    # Get enhanced odds
    enhanced_odds = odds_client.get_enhanced_soccer_odds(['soccer_epl'])

    # Analyze for value
    analyzed_odds = {}
    for sport, matches in enhanced_odds.items():
        analyzed_odds[sport] = odds_client.analyze_odds_value(matches)

    # Generate report
    report = odds_client.generate_odds_comparison_report(analyzed_odds)

    # Save report
    report_file = f"odds_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

    print(f"✅ Odds analysis complete!")
    print(f"📄 Report saved: {report_file}")
    print("\nSample of report:")
    print(report[:500] + "..." if len(report) > 500 else report)

if __name__ == "__main__":
    main()