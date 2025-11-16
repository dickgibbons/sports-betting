#!/usr/bin/env python3
"""
Comprehensive Backtest System
Backtests top 8 picks and high confidence picks from August 1st to present
Uses hierarchical odds: DraftKings > FanDuel > FootyStats
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta
import requests
import time
from typing import Dict, List, Optional, Tuple
import sys

class SoccerBacktester:
    """Comprehensive backtesting system for soccer betting strategies"""

    def __init__(self, start_date: str = "2024-08-01"):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.now()
        self.stake_per_bet = 25.0

        # API configurations
        self.odds_api_key = "fc8b43bb8508b51b52b52fd1827eaaf4"
        self.footystats_key = "test85g57"

        # Results storage
        self.top8_results = []
        self.high_confidence_results = []

        print(f"🎯 Initializing backtest from {start_date} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Stake per bet: ${self.stake_per_bet}")
        print(f"📊 Odds hierarchy: DraftKings → FanDuel → FootyStats")

    def run_complete_backtest(self):
        """Run the complete backtest for both strategies"""

        print(f"\n🚀 Starting comprehensive backtest...")
        print("=" * 60)

        # Get all dates to backtest
        dates_to_test = self.get_backtest_dates()

        print(f"📅 Testing {len(dates_to_test)} days from {self.start_date.strftime('%Y-%m-%d')}")

        for i, test_date in enumerate(dates_to_test):
            print(f"\n📊 Processing {test_date.strftime('%Y-%m-%d')} ({i+1}/{len(dates_to_test)})")

            try:
                # Get fixtures and odds for this date
                fixtures = self.get_historical_fixtures(test_date)
                if not fixtures:
                    print(f"   ⚠️ No fixtures found for {test_date.strftime('%Y-%m-%d')}")
                    continue

                # Generate picks for both strategies
                top8_picks = self.generate_top8_picks(fixtures, test_date)
                high_conf_picks = self.generate_high_confidence_picks(fixtures, test_date)

                # Process results for each strategy
                self.process_daily_results(top8_picks, test_date, "top8")
                self.process_daily_results(high_conf_picks, test_date, "high_confidence")

                print(f"   ✅ Processed {len(top8_picks)} top8 + {len(high_conf_picks)} high-conf picks")

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                print(f"   ❌ Error processing {test_date.strftime('%Y-%m-%d')}: {e}")
                continue

        # Generate final cumulative reports
        self.generate_cumulative_reports()

        print(f"\n🎉 Backtest completed!")
        print(f"📊 Top 8 strategy: {len(self.top8_results)} total bets")
        print(f"🎯 High confidence strategy: {len(self.high_confidence_results)} total bets")

    def get_backtest_dates(self) -> List[datetime]:
        """Generate list of dates to backtest"""
        dates = []
        current_date = self.start_date

        while current_date <= self.end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        return dates

    def get_historical_fixtures(self, date: datetime) -> List[Dict]:
        """Get historical fixtures for a specific date"""

        # Try multiple approaches to get historical data
        fixtures = []

        # 1. Try FootyStats historical data
        try:
            fixtures.extend(self.get_footystats_historical(date))
        except Exception as e:
            print(f"   ⚠️ FootyStats historical failed: {e}")

        # 2. Try The Odds API historical (if available)
        try:
            fixtures.extend(self.get_odds_api_historical(date))
        except Exception as e:
            print(f"   ⚠️ Odds API historical failed: {e}")

        # 3. Use local cache if available
        cache_file = f"historical_fixtures_{date.strftime('%Y%m%d')}.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cached_fixtures = json.load(f)
                fixtures.extend(cached_fixtures)

        return fixtures

    def get_footystats_historical(self, date: datetime) -> List[Dict]:
        """Get historical fixtures from FootyStats"""

        fixtures = []
        leagues = ["EPL", "La_Liga", "Serie_A", "Bundesliga", "Ligue_1", "MLS"]

        for league in leagues:
            try:
                url = f"https://api.footystats.org/league-matches"
                params = {
                    'key': self.footystats_key,
                    'league': league,
                    'season': '2024',
                    'date': date.strftime('%Y-%m-%d')
                }

                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for match in data.get('data', []):
                        fixture = self.format_footystats_fixture(match, league)
                        if fixture:
                            fixtures.append(fixture)

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"     ⚠️ Error getting {league} fixtures: {e}")
                continue

        return fixtures

    def get_odds_api_historical(self, date: datetime) -> List[Dict]:
        """Get historical fixtures from The Odds API (limited historical data)"""

        # The Odds API has limited historical data, so this is mostly for recent dates
        fixtures = []

        if date < datetime.now() - timedelta(days=30):
            return fixtures  # Too old for Odds API

        try:
            leagues = ['soccer_epl', 'soccer_spain_la_liga', 'soccer_usa_mls']

            for league in leagues:
                url = f"https://api.the-odds-api.com/v4/sports/{league}/odds"
                params = {
                    'api_key': self.odds_api_key,
                    'regions': 'us,uk',
                    'markets': 'h2h',
                    'bookmakers': 'draftkings,fanduel',
                    'oddsFormat': 'decimal'
                }

                response = requests.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    for match in data:
                        fixture = self.format_odds_api_fixture(match, league)
                        if fixture:
                            fixtures.append(fixture)

                time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"     ⚠️ Odds API error: {e}")

        return fixtures

    def format_footystats_fixture(self, match: Dict, league: str) -> Optional[Dict]:
        """Format FootyStats match data"""

        try:
            return {
                'home_team': match.get('home_name', ''),
                'away_team': match.get('away_name', ''),
                'league': league,
                'kick_off': match.get('date_unix', 0),
                'home_odds': match.get('odds_ft_1', 0),
                'draw_odds': match.get('odds_ft_x', 0),
                'away_odds': match.get('odds_ft_2', 0),
                'home_score': match.get('homeGoalCount', None),
                'away_score': match.get('awayGoalCount', None),
                'source': 'footystats'
            }
        except Exception:
            return None

    def format_odds_api_fixture(self, match: Dict, league: str) -> Optional[Dict]:
        """Format Odds API match data"""

        try:
            fixture = {
                'home_team': match.get('home_team', ''),
                'away_team': match.get('away_team', ''),
                'league': league,
                'kick_off': match.get('commence_time', ''),
                'source': 'odds_api'
            }

            # Extract odds with hierarchy preference
            odds = self.extract_hierarchical_odds(match)
            fixture.update(odds)

            return fixture
        except Exception:
            return None

    def extract_hierarchical_odds(self, match: Dict) -> Dict:
        """Extract odds with DraftKings > FanDuel > FootyStats preference"""

        odds = {'home_odds': 0, 'draw_odds': 0, 'away_odds': 0, 'odds_source': 'none'}

        bookmakers = match.get('bookmakers', [])

        # Priority order: DraftKings, FanDuel, Others
        preferred_books = ['DraftKings', 'FanDuel']

        for book_name in preferred_books:
            for bookmaker in bookmakers:
                if book_name.lower() in bookmaker.get('title', '').lower():
                    extracted = self.extract_bookmaker_odds(bookmaker)
                    if extracted['home_odds'] > 0:  # Valid odds found
                        odds.update(extracted)
                        odds['odds_source'] = book_name
                        return odds

        # Fall back to any other bookmaker
        for bookmaker in bookmakers:
            extracted = self.extract_bookmaker_odds(bookmaker)
            if extracted['home_odds'] > 0:
                odds.update(extracted)
                odds['odds_source'] = bookmaker.get('title', 'unknown')
                return odds

        return odds

    def extract_bookmaker_odds(self, bookmaker: Dict) -> Dict:
        """Extract odds from a bookmaker's data"""

        odds = {'home_odds': 0, 'draw_odds': 0, 'away_odds': 0}

        for market in bookmaker.get('markets', []):
            if market.get('key') == 'h2h':
                outcomes = market.get('outcomes', [])

                for outcome in outcomes:
                    name = outcome.get('name', '').lower()
                    price = outcome.get('price', 0)

                    if 'draw' in name:
                        odds['draw_odds'] = price
                    elif len([o for o in outcomes if not 'draw' in o.get('name', '').lower()]) >= 2:
                        # First non-draw team is home, second is away
                        non_draw = [o for o in outcomes if not 'draw' in o.get('name', '').lower()]
                        if outcome == non_draw[0]:
                            odds['home_odds'] = price
                        elif outcome == non_draw[1]:
                            odds['away_odds'] = price

        return odds

    def generate_top8_picks(self, fixtures: List[Dict], date: datetime) -> List[Dict]:
        """Generate top 8 picks for the date"""

        picks = []

        # Score and rank fixtures
        scored_fixtures = []
        for fixture in fixtures:
            score = self.calculate_fixture_score(fixture)
            if score > 0:
                scored_fixtures.append((fixture, score))

        # Sort by score and take top 8
        scored_fixtures.sort(key=lambda x: x[1], reverse=True)
        top_fixtures = scored_fixtures[:8]

        # Generate picks
        for i, (fixture, score) in enumerate(top_fixtures):
            pick = self.create_pick(fixture, date, f"top8_pick_{i+1}", score)
            if pick:
                picks.append(pick)

        return picks

    def generate_high_confidence_picks(self, fixtures: List[Dict], date: datetime) -> List[Dict]:
        """Generate high confidence picks for the date"""

        picks = []

        # Only include fixtures with high confidence score
        for fixture in fixtures:
            score = self.calculate_fixture_score(fixture)
            confidence = self.calculate_confidence(fixture)

            if confidence >= 75:  # High confidence threshold
                pick = self.create_pick(fixture, date, f"high_conf", score, confidence)
                if pick:
                    picks.append(pick)

        return picks

    def calculate_fixture_score(self, fixture: Dict) -> float:
        """Calculate a score for fixture selection"""

        score = 0.0

        # Base score from odds value
        home_odds = fixture.get('home_odds', 0)
        draw_odds = fixture.get('draw_odds', 0)
        away_odds = fixture.get('away_odds', 0)

        if home_odds > 0 and draw_odds > 0 and away_odds > 0:
            # Simple value calculation
            implied_prob = 1/home_odds + 1/draw_odds + 1/away_odds
            if implied_prob < 1.0:  # Arbitrage opportunity
                score += (1.0 - implied_prob) * 100

            # Prefer moderate odds (not too short, not too long)
            best_odds = max(home_odds, draw_odds, away_odds)
            if 1.5 <= best_odds <= 3.5:
                score += 20

            # League preference
            league = fixture.get('league', '').lower()
            if 'epl' in league or 'premier' in league:
                score += 15
            elif 'la_liga' in league or 'serie_a' in league:
                score += 10
            elif 'mls' in league:
                score += 5

        return score

    def calculate_confidence(self, fixture: Dict) -> float:
        """Calculate confidence level for a fixture"""

        confidence = 50.0  # Base confidence

        # Odds source quality
        source = fixture.get('odds_source', '').lower()
        if 'draftkings' in source:
            confidence += 25
        elif 'fanduel' in source:
            confidence += 20
        elif 'footystats' in source:
            confidence += 10

        # League quality
        league = fixture.get('league', '').lower()
        if 'epl' in league:
            confidence += 20
        elif 'la_liga' in league or 'serie_a' in league:
            confidence += 15
        elif 'mls' in league:
            confidence += 10

        return min(confidence, 95.0)  # Cap at 95%

    def create_pick(self, fixture: Dict, date: datetime, pick_type: str, score: float, confidence: float = 70) -> Optional[Dict]:
        """Create a betting pick from a fixture"""

        home_odds = fixture.get('home_odds', 0)
        draw_odds = fixture.get('draw_odds', 0)
        away_odds = fixture.get('away_odds', 0)

        if not all([home_odds > 0, draw_odds > 0, away_odds > 0]):
            return None

        # Select the best value outcome
        outcomes = [
            ('home', home_odds),
            ('draw', draw_odds),
            ('away', away_odds)
        ]

        # Simple strategy: pick the outcome with best implied value
        best_outcome = max(outcomes, key=lambda x: x[1])

        return {
            'date': date.strftime('%Y-%m-%d'),
            'home_team': fixture.get('home_team', ''),
            'away_team': fixture.get('away_team', ''),
            'league': fixture.get('league', ''),
            'pick_type': pick_type,
            'selection': best_outcome[0],
            'odds': best_outcome[1],
            'stake': self.stake_per_bet,
            'confidence': confidence,
            'score': score,
            'odds_source': fixture.get('odds_source', 'unknown'),
            'home_score': fixture.get('home_score'),
            'away_score': fixture.get('away_score'),
            'kick_off': fixture.get('kick_off', '')
        }

    def process_daily_results(self, picks: List[Dict], date: datetime, strategy: str):
        """Process and store results for daily picks"""

        for pick in picks:
            # Determine result
            result = self.determine_pick_result(pick)
            pick['result'] = result
            pick['profit_loss'] = self.calculate_profit_loss(pick)

            # Store in appropriate results list
            if strategy == "top8":
                self.top8_results.append(pick)
            else:
                self.high_confidence_results.append(pick)

    def determine_pick_result(self, pick: Dict) -> str:
        """Determine if a pick won, lost, or is pending"""

        home_score = pick.get('home_score')
        away_score = pick.get('away_score')
        selection = pick.get('selection')

        if home_score is None or away_score is None:
            return 'pending'

        try:
            home_score = int(home_score)
            away_score = int(away_score)
        except (ValueError, TypeError):
            return 'pending'

        if selection == 'home':
            return 'won' if home_score > away_score else 'lost'
        elif selection == 'away':
            return 'won' if away_score > home_score else 'lost'
        elif selection == 'draw':
            return 'won' if home_score == away_score else 'lost'

        return 'pending'

    def calculate_profit_loss(self, pick: Dict) -> float:
        """Calculate profit/loss for a pick"""

        result = pick.get('result', 'pending')
        stake = pick.get('stake', 0)
        odds = pick.get('odds', 0)

        if result == 'won':
            return (odds - 1) * stake
        elif result == 'lost':
            return -stake
        else:
            return 0.0

    def generate_cumulative_reports(self):
        """Generate final cumulative reports for both strategies"""

        print(f"\n📊 Generating cumulative reports...")

        # Generate Top 8 Strategy Report
        self.generate_strategy_report(self.top8_results, "top8_picks")

        # Generate High Confidence Strategy Report
        self.generate_strategy_report(self.high_confidence_results, "high_confidence_picks")

        # Generate comparison report
        self.generate_comparison_report()

    def generate_strategy_report(self, results: List[Dict], strategy_name: str):
        """Generate cumulative report for a strategy"""

        if not results:
            print(f"   ⚠️ No results for {strategy_name}")
            return

        # Convert to DataFrame
        df = pd.DataFrame(results)

        # Calculate cumulative metrics
        df['cumulative_profit'] = df['profit_loss'].cumsum()
        df['cumulative_stakes'] = df['stake'].cumsum()
        df['running_roi'] = (df['cumulative_profit'] / df['cumulative_stakes'] * 100).round(2)

        # Calculate win rate
        completed_bets = df[df['result'].isin(['won', 'lost'])]
        if len(completed_bets) > 0:
            wins = len(completed_bets[completed_bets['result'] == 'won'])
            total = len(completed_bets)
            win_rate = (wins / total * 100)
            df['running_win_rate'] = win_rate
        else:
            df['running_win_rate'] = 0

        # Save detailed CSV
        filename = f"output reports/backtest_{strategy_name}_detailed.csv"
        df.to_csv(filename, index=False)

        # Generate summary
        summary = self.generate_strategy_summary(df, strategy_name)

        # Save summary
        summary_filename = f"output reports/backtest_{strategy_name}_summary.txt"
        with open(summary_filename, 'w') as f:
            f.write(summary)

        print(f"   ✅ {strategy_name}: {len(results)} picks, {summary_filename}")

    def generate_strategy_summary(self, df: pd.DataFrame, strategy_name: str) -> str:
        """Generate text summary for a strategy"""

        completed_bets = df[df['result'].isin(['won', 'lost'])]

        if len(completed_bets) == 0:
            return f"No completed bets for {strategy_name}"

        total_bets = len(completed_bets)
        wins = len(completed_bets[completed_bets['result'] == 'won'])
        losses = len(completed_bets[completed_bets['result'] == 'lost'])
        win_rate = wins / total_bets * 100

        total_staked = completed_bets['stake'].sum()
        total_profit = completed_bets['profit_loss'].sum()
        roi = total_profit / total_staked * 100

        avg_odds = completed_bets['odds'].mean()

        # Odds source breakdown
        source_breakdown = completed_bets['odds_source'].value_counts()

        summary = f"""
🎯 BACKTEST SUMMARY - {strategy_name.upper()}
{'='*60}
Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}
Strategy: {strategy_name.replace('_', ' ').title()}

📊 PERFORMANCE METRICS:
   Total Bets: {total_bets}
   Wins: {wins}
   Losses: {losses}
   Win Rate: {win_rate:.1f}%

💰 FINANCIAL RESULTS:
   Total Staked: ${total_staked:,.2f}
   Total Return: ${total_profit:,.2f}
   ROI: {roi:+.2f}%
   Average Odds: {avg_odds:.2f}

📈 BETTING PATTERN:
   Stake per bet: ${self.stake_per_bet}
   Average profit per winning bet: ${completed_bets[completed_bets['result'] == 'won']['profit_loss'].mean():.2f}
   Largest win: ${completed_bets['profit_loss'].max():.2f}
   Largest loss: ${completed_bets['profit_loss'].min():.2f}

🏆 ODDS SOURCES USED:
"""

        for source, count in source_breakdown.items():
            percentage = count / total_bets * 100
            summary += f"   {source}: {count} bets ({percentage:.1f}%)\n"

        # League breakdown
        league_breakdown = completed_bets['league'].value_counts()
        summary += f"\n⚽ LEAGUE BREAKDOWN:\n"
        for league, count in league_breakdown.items():
            percentage = count / total_bets * 100
            league_profit = completed_bets[completed_bets['league'] == league]['profit_loss'].sum()
            summary += f"   {league}: {count} bets ({percentage:.1f}%) - ${league_profit:+.2f}\n"

        return summary

    def generate_comparison_report(self):
        """Generate comparison report between strategies"""

        comparison = f"""
🔄 STRATEGY COMPARISON REPORT
{'='*60}
Backtest Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}

📊 TOP 8 PICKS STRATEGY:
   Total Bets: {len([r for r in self.top8_results if r['result'] in ['won', 'lost']])}
   Total Profit: ${sum([r['profit_loss'] for r in self.top8_results]):.2f}

🎯 HIGH CONFIDENCE STRATEGY:
   Total Bets: {len([r for r in self.high_confidence_results if r['result'] in ['won', 'lost']])}
   Total Profit: ${sum([r['profit_loss'] for r in self.high_confidence_results]):.2f}

💡 RECOMMENDATION:
   Best performing strategy will be highlighted in detailed analysis.

🔗 ODDS SOURCE HIERARCHY EFFECTIVENESS:
   DraftKings: Primary source when available
   FanDuel: Secondary source
   FootyStats: Fallback source

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        with open("output reports/backtest_comparison_summary.txt", 'w') as f:
            f.write(comparison)

        print("   ✅ Comparison report generated")

def main():
    """Run the complete backtest"""

    print("🚀 Starting comprehensive soccer betting backtest...")
    print("💰 $25 per bet | 📅 August 1st - Present")
    print("🎯 Testing: Top 8 Picks + High Confidence strategies")
    print("📊 Odds: DraftKings → FanDuel → FootyStats")

    backtester = SoccerBacktester("2024-08-01")
    backtester.run_complete_backtest()

    print("\n🎉 Backtest complete! Check output reports/ for results.")

if __name__ == "__main__":
    main()