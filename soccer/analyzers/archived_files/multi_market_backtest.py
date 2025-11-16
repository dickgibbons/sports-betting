#!/usr/bin/env python3
"""
Multi-Market Soccer Betting Backtest

Tests the multi-market system from August 1st with realistic betting activity
across all major markets: ML, Totals, BTTS, Corners, Team Totals, etc.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv
import random
from multi_market_predictor import MultiMarketPredictor
import logging


class MultiMarketBacktest:
    """Comprehensive backtest with multiple betting markets"""
    
    def __init__(self, initial_bankroll: float = 300.0, start_date: str = "2024-08-01"):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.now()
        
        # Initialize multi-market predictor
        self.predictor = MultiMarketPredictor("test_api_key")
        
        # Risk management (more relaxed to generate bets)
        self.max_daily_risk = 0.20  # 20% daily risk limit
        self.max_single_bet = 0.08  # 8% per bet
        self.max_bets_per_day = 8   # Up to 8 bets per day
        
        # Results storage
        self.all_bets = []
        self.daily_summaries = []
        self.peak_bankroll = initial_bankroll
        self.max_drawdown = 0.0
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def generate_daily_matches(self, date: datetime, num_matches: int = None) -> list:
        """Generate realistic daily match schedule"""
        if num_matches is None:
            # More matches on weekends, fewer on weekdays
            if date.weekday() >= 5:  # Weekend
                num_matches = random.randint(8, 15)
            else:  # Weekday
                num_matches = random.randint(4, 8)
        
        matches = []
        
        # Realistic league distribution
        leagues = [
            ('Premier League', 0.20),
            ('La Liga', 0.15),
            ('Serie A', 0.15),
            ('Bundesliga', 0.15),
            ('Ligue 1', 0.10),
            ('Championship', 0.08),
            ('MLS', 0.07),
            ('Liga MX', 0.05),
            ('Eredivisie', 0.03),
            ('Other', 0.02)
        ]
        
        teams = {
            'Premier League': [
                ('Manchester City', 'Arsenal'), ('Liverpool', 'Chelsea'), 
                ('Tottenham', 'Manchester United'), ('Newcastle', 'Brighton'),
                ('Aston Villa', 'West Ham'), ('Crystal Palace', 'Fulham'),
                ('Brentford', 'Wolves'), ('Everton', 'Nottingham Forest')
            ],
            'La Liga': [
                ('Real Madrid', 'Barcelona'), ('Atletico Madrid', 'Valencia'),
                ('Sevilla', 'Real Betis'), ('Villarreal', 'Athletic Bilbao'),
                ('Real Sociedad', 'Getafe'), ('Osasuna', 'Celta Vigo')
            ],
            'Serie A': [
                ('Juventus', 'AC Milan'), ('Inter Milan', 'Napoli'),
                ('AS Roma', 'Lazio'), ('Atalanta', 'Fiorentina'),
                ('Bologna', 'Torino'), ('Sassuolo', 'Udinese')
            ],
            'Bundesliga': [
                ('Bayern Munich', 'Borussia Dortmund'), ('RB Leipzig', 'Bayer Leverkusen'),
                ('Eintracht Frankfurt', 'VfB Stuttgart'), ('Borussia Monchengladbach', 'Wolfsburg'),
                ('Union Berlin', 'SC Freiburg')
            ]
        }
        
        for i in range(num_matches):
            # Select league based on weights
            league = np.random.choice([l[0] for l in leagues], p=[l[1] for l in leagues])
            
            # Select teams
            if league in teams:
                home_team, away_team = random.choice(teams[league])
            else:
                home_team, away_team = f"Team {i*2+1}", f"Team {i*2+2}"
            
            match = {
                'date': date.strftime('%Y-%m-%d'),
                'time': f"{random.randint(12, 21):02d}:{random.choice(['00', '15', '30', '45'])}",
                'league': league,
                'home_team': home_team,
                'away_team': away_team,
                'match_id': f"{date.strftime('%Y%m%d')}_{i:02d}"
            }
            
            matches.append(match)
        
        return matches
    
    def run_comprehensive_backtest(self):
        """Run full backtest across all markets from August 1st"""
        
        print("🎯 Multi-Market Soccer Betting Backtest")
        print("=" * 60)
        print(f"📅 Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 Starting Bankroll: ${self.initial_bankroll:,.2f}")
        print(f"🎲 Markets: ML, Totals, BTTS, Corners, Team Totals, Double Chance, Asian Handicap")
        
        current_date = self.start_date
        total_opportunities = 0
        total_bets_placed = 0
        
        while current_date < self.end_date:
            if current_date > datetime(2025, 1, 1):  # Limit backtest scope
                break
                
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Generate matches for this day
            daily_matches = self.generate_daily_matches(current_date)
            
            # Process each match
            daily_bets = []
            daily_risk_exposure = 0.0
            
            print(f"\n📅 {date_str} - {len(daily_matches)} matches")
            
            for match in daily_matches:
                # Generate odds for all markets
                odds = self.predictor.generate_realistic_odds()
                
                # Analyze for value opportunities
                opportunities = self.predictor.analyze_all_markets(odds)
                total_opportunities += len(opportunities)
                
                # Apply daily risk limits
                for opp in opportunities:
                    if len(daily_bets) >= self.max_bets_per_day:
                        break
                        
                    proposed_stake = opp['kelly_fraction'] * self.current_bankroll
                    
                    # Risk checks
                    if (proposed_stake <= self.current_bankroll * self.max_single_bet and
                        daily_risk_exposure + proposed_stake <= self.current_bankroll * self.max_daily_risk):
                        
                        # Simulate match outcome
                        odds_with_context = self.predictor.generate_realistic_odds()
                        actual_outcome = self.predictor.simulate_match_outcome(odds_with_context)
                        
                        # Determine if bet won
                        bet_won = self.determine_bet_outcome(opp['market'], actual_outcome)
                        
                        # Calculate P&L
                        if bet_won:
                            profit = proposed_stake * (opp['odds'] - 1)
                            self.current_bankroll += profit
                        else:
                            profit = -proposed_stake
                            self.current_bankroll += profit
                        
                        # Record bet
                        bet_record = {
                            'date': date_str,
                            'match': f"{match['home_team']} vs {match['away_team']}",
                            'league': match['league'],
                            'market': opp['market'],
                            'odds': opp['odds'],
                            'stake': proposed_stake,
                            'profit_loss': profit,
                            'bet_won': bet_won,
                            'edge': opp['edge'],
                            'confidence': opp['confidence'],
                            'bankroll_before': self.current_bankroll - profit,
                            'bankroll_after': self.current_bankroll
                        }
                        
                        daily_bets.append(bet_record)
                        daily_risk_exposure += proposed_stake
                        total_bets_placed += 1
                        
                        result_emoji = "✅" if bet_won else "❌"
                        print(f"   {result_emoji} {opp['market']} @ {opp['odds']:.2f} - "
                              f"${proposed_stake:.0f} ({profit:+.0f}) | ${self.current_bankroll:.0f}")
            
            # Update peak and drawdown
            if self.current_bankroll > self.peak_bankroll:
                self.peak_bankroll = self.current_bankroll
                
            current_drawdown = (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll
            if current_drawdown > self.max_drawdown:
                self.max_drawdown = current_drawdown
            
            # Daily summary
            daily_profit = sum(bet['profit_loss'] for bet in daily_bets)
            daily_summary = {
                'date': date_str,
                'starting_bankroll': self.current_bankroll - daily_profit,
                'ending_bankroll': self.current_bankroll,
                'daily_profit': daily_profit,
                'total_stakes': sum(bet['stake'] for bet in daily_bets),
                'num_bets': len(daily_bets),
                'bets_won': sum(1 for bet in daily_bets if bet['bet_won']),
                'win_rate': (sum(1 for bet in daily_bets if bet['bet_won']) / len(daily_bets) * 100) if daily_bets else 0,
                'roi': (daily_profit / (self.current_bankroll - daily_profit) * 100) if self.current_bankroll != daily_profit else 0,
                'peak_bankroll': self.peak_bankroll,
                'drawdown': current_drawdown * 100
            }
            
            self.daily_summaries.append(daily_summary)
            self.all_bets.extend(daily_bets)
            
            if daily_bets:
                print(f"   💰 Daily: {daily_profit:+.0f} | Bankroll: ${self.current_bankroll:.0f} | "
                      f"Bets: {len(daily_bets)} ({sum(1 for b in daily_bets if b['bet_won'])}/{len(daily_bets)})")
            
            current_date += timedelta(days=1)
        
        self.generate_final_report(total_opportunities, total_bets_placed)
    
    def determine_bet_outcome(self, market: str, actual_outcome: dict) -> bool:
        """Determine if a specific market bet won based on match outcome"""
        
        # Match Result markets
        if market == 'Home':
            return actual_outcome['match_result'] == 'Home'
        elif market == 'Draw':
            return actual_outcome['match_result'] == 'Draw'
        elif market == 'Away':
            return actual_outcome['match_result'] == 'Away'
        
        # Total Goals markets
        elif market == 'Over 1.5':
            return actual_outcome['total_goals'] > 1.5
        elif market == 'Under 1.5':
            return actual_outcome['total_goals'] <= 1.5
        elif market == 'Over 2.5':
            return actual_outcome['total_goals'] > 2.5
        elif market == 'Under 2.5':
            return actual_outcome['total_goals'] <= 2.5
        elif market == 'Over 3.5':
            return actual_outcome['total_goals'] > 3.5
        elif market == 'Under 3.5':
            return actual_outcome['total_goals'] <= 3.5
        
        # BTTS markets
        elif market == 'BTTS Yes':
            return actual_outcome['btts_result'] == 'BTTS Yes'
        elif market == 'BTTS No':
            return actual_outcome['btts_result'] == 'BTTS No'
        
        # Team Totals
        elif market == 'Home Over 1.5':
            return actual_outcome['home_goals'] > 1.5
        elif market == 'Home Under 1.5':
            return actual_outcome['home_goals'] <= 1.5
        elif market == 'Away Over 1.5':
            return actual_outcome['away_goals'] > 1.5
        elif market == 'Away Under 1.5':
            return actual_outcome['away_goals'] <= 1.5
        
        # Double Chance
        elif market == 'Home/Draw':
            return actual_outcome['match_result'] in ['Home', 'Draw']
        elif market == 'Home/Away':
            return actual_outcome['match_result'] in ['Home', 'Away']
        elif market == 'Draw/Away':
            return actual_outcome['match_result'] in ['Draw', 'Away']
        
        # Corners
        elif market == 'Over 9.5 Corners':
            return actual_outcome['actual_corners'] > 9.5
        elif market == 'Under 9.5 Corners':
            return actual_outcome['actual_corners'] <= 9.5
        elif market == 'Over 11.5 Corners':
            return actual_outcome['actual_corners'] > 11.5
        elif market == 'Under 11.5 Corners':
            return actual_outcome['actual_corners'] <= 11.5
        
        # Asian Handicap
        elif market == 'Home -1':
            return actual_outcome['home_goals'] - actual_outcome['away_goals'] > 1
        elif market == 'Home +1':
            return actual_outcome['home_goals'] - actual_outcome['away_goals'] > -1
        elif market == 'Away -1':
            return actual_outcome['away_goals'] - actual_outcome['home_goals'] > 1
        elif market == 'Away +1':
            return actual_outcome['away_goals'] - actual_outcome['home_goals'] > -1
        
        # Default
        return False
    
    def generate_final_report(self, total_opportunities: int, total_bets_placed: int):
        """Generate comprehensive performance report"""
        
        print(f"\n" + "=" * 80)
        print("📊 MULTI-MARKET BACKTEST RESULTS")
        print("=" * 80)
        
        if not self.daily_summaries:
            print("❌ No trading data to analyze")
            return
        
        # Calculate metrics
        total_return = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll * 100
        total_days = len(self.daily_summaries)
        profitable_days = sum(1 for day in self.daily_summaries if day['daily_profit'] > 0)
        total_won = sum(bet['bet_won'] for bet in self.all_bets)
        
        win_rate = (total_won / total_bets_placed * 100) if total_bets_placed > 0 else 0
        selectivity = (total_bets_placed / total_opportunities * 100) if total_opportunities > 0 else 0
        
        avg_daily_return = np.mean([day['roi'] for day in self.daily_summaries])
        volatility = np.std([day['roi'] for day in self.daily_summaries])
        
        # Market breakdown
        market_stats = {}
        for bet in self.all_bets:
            market = bet['market']
            if market not in market_stats:
                market_stats[market] = {'count': 0, 'won': 0, 'profit': 0}
            market_stats[market]['count'] += 1
            market_stats[market]['won'] += bet['bet_won']
            market_stats[market]['profit'] += bet['profit_loss']
        
        print(f"\n💰 PERFORMANCE SUMMARY:")
        print(f"{'Metric':<25} {'Value':<20}")
        print("-" * 45)
        print(f"{'Starting Bankroll':<25} ${self.initial_bankroll:,.2f}")
        print(f"{'Final Bankroll':<25} ${self.current_bankroll:,.2f}")
        print(f"{'Total Return':<25} {total_return:+.2f}%")
        print(f"{'Peak Bankroll':<25} ${self.peak_bankroll:,.2f}")
        print(f"{'Maximum Drawdown':<25} {self.max_drawdown*100:.2f}%")
        
        print(f"\n🎯 BETTING ACTIVITY:")
        print(f"{'Total Opportunities':<25} {total_opportunities:,}")
        print(f"{'Bets Placed':<25} {total_bets_placed:,}")
        print(f"{'Bet Selectivity':<25} {selectivity:.1f}%")
        print(f"{'Overall Win Rate':<25} {win_rate:.1f}%")
        print(f"{'Trading Days':<25} {total_days}")
        print(f"{'Profitable Days':<25} {profitable_days} ({profitable_days/total_days*100:.1f}%)")
        
        print(f"\n📈 RISK METRICS:")
        print(f"{'Avg Daily Return':<25} {avg_daily_return:.2f}%")
        print(f"{'Daily Volatility':<25} {volatility:.2f}%")
        print(f"{'Sharpe Ratio':<25} {avg_daily_return/volatility if volatility > 0 else 0:.2f}")
        
        print(f"\n🏆 TOP PERFORMING MARKETS:")
        sorted_markets = sorted(market_stats.items(), key=lambda x: x[1]['profit'], reverse=True)
        for market, stats in sorted_markets[:10]:
            win_rate_market = stats['won'] / stats['count'] * 100
            print(f"   {market:<20} {stats['count']:>3} bets, {win_rate_market:>5.1f}% WR, {stats['profit']:>+7.0f}")
        
        # Save results
        self.save_results()
        
        print(f"\n✅ Multi-Market Backtest Complete!")
        print(f"📁 Results saved to CSV files")
    
    def save_results(self):
        """Save backtest results to CSV files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed bet results
        if self.all_bets:
            filename = f"multi_market_backtest_detailed_{timestamp}.csv"
            filepath = f"./{filename}"
            
            fieldnames = [
                'date', 'match', 'league', 'market', 'odds', 'stake', 
                'profit_loss', 'bet_won', 'edge', 'confidence',
                'bankroll_before', 'bankroll_after'
            ]
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.all_bets)
            
            print(f"💾 Detailed results: {filename}")
        
        # Save daily summary
        if self.daily_summaries:
            filename = f"multi_market_backtest_summary_{timestamp}.csv"
            filepath = f"./{filename}"
            
            fieldnames = [
                'date', 'starting_bankroll', 'ending_bankroll', 'daily_profit',
                'total_stakes', 'num_bets', 'bets_won', 'win_rate', 'roi',
                'peak_bankroll', 'drawdown'
            ]
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.daily_summaries)
            
            print(f"💾 Daily summary: {filename}")


def main():
    """Run multi-market backtest"""
    
    # Run backtest with same starting conditions as original
    backtest = MultiMarketBacktest(initial_bankroll=300.0, start_date="2024-08-01")
    backtest.run_comprehensive_backtest()


if __name__ == "__main__":
    main()