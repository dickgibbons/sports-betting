#!/usr/bin/env python3
"""
Historical Backtest System - 2024 Season

Runs a comprehensive backtest for March-May 2024 when all major leagues
were active, using real historical match results to validate system performance.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from real_data_integration import RealDataIntegration
from multi_market_predictor import MultiMarketPredictor
from real_results_fetcher import RealResultsFetcher
from typing import Dict, List, Tuple
import csv
import time

class HistoricalBacktest2024:
    """Comprehensive 2024 season backtest using real results"""
    
    def __init__(self, api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.api_key = api_key
        self.results_fetcher = RealResultsFetcher(api_key)
        self.bet_amount = 25.0  # Standard $25 bet
        
        # Date range for 2024 backtest - active season period
        self.start_date = datetime(2024, 3, 1)   # March 2024
        self.end_date = datetime(2024, 5, 31)    # May 2024
        
        print(f"🔄 Historical Backtest 2024 System Initialized")
        print(f"📅 Backtest Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"🏆 Peak season period with all major leagues active")
        print(f"💰 Standard Bet Amount: ${self.bet_amount}")
        
        # Followed leagues for filtering
        self.followed_leagues = [
            "Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1",
            "Championship", "Serie B", "2. Bundesliga", "Liga Portugal",
            "Eredivisie", "Belgian Pro League", "Swiss Super League",
            "Austrian Bundesliga", "Scottish Premiership", "MLS", "USL Championship",
            "Liga MX", "Brasileirao", "Copa Libertadores", "Copa Sudamericana",
            "UEFA Champions League", "UEFA Europa League", "UEFA Europa Conference League",
            "World Cup - Qualification Europe", "World Cup - Qualification Africa",
            "World Cup - Qualification Asia", "World Cup - Qualification CONCACAF",
            "World Cup - Qualification South America", "UEFA Nations League",
            "Frauen Bundesliga", "UEFA Champions League Women", "MLS Next Pro"
        ]
        
    def is_followed_league(self, league_name: str, country: str = None) -> bool:
        """Check if a league is one we follow - with country verification"""
        
        # Direct match first - but need to verify it's the right country for ambiguous names
        if league_name in self.followed_leagues:
            # For ambiguous league names, verify country
            if league_name == "Premier League" and country != "England":
                return False
            if league_name == "Ligue 1" and country != "France":
                return False
            if league_name == "Serie A" and country != "Italy":
                return False
            if league_name == "Primera Division" and country != "Spain":
                return False
            return True
        
        return False
    
    def get_date_range(self) -> List[str]:
        """Get all dates in the backtest range"""
        
        dates = []
        current_date = self.start_date
        
        while current_date <= self.end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        print(f"📅 Generated {len(dates)} dates for 2024 backtest")
        return dates
    
    def get_historical_fixtures_2024(self, date_str: str) -> List[Dict]:
        """Get historical fixtures for a specific date in 2024"""
        
        print(f"📅 Getting 2024 fixtures for {date_str}...")
        
        # Initialize real data integration
        real_data = RealDataIntegration()
        
        # Get fixtures for this date
        try:
            all_fixtures = real_data.get_real_fixtures_with_odds(date_str)
            
            # Filter for followed leagues only
            followed_fixtures = []
            for fixture in all_fixtures:
                league = fixture.get('league', 'Unknown')
                country = fixture.get('country', 'Unknown')
                
                if self.is_followed_league(league, country):
                    followed_fixtures.append(fixture)
            
            print(f"   ✅ Found {len(followed_fixtures)} fixtures in followed leagues (from {len(all_fixtures)} total)")
            return followed_fixtures
            
        except Exception as e:
            print(f"   ❌ Error getting fixtures for {date_str}: {e}")
            return []
    
    def generate_historical_picks_2024(self, fixtures: List[Dict], date_str: str) -> List[Dict]:
        """Generate betting picks for 2024 historical fixtures"""
        
        if not fixtures:
            return []
        
        print(f"🤖 Generating picks for {len(fixtures)} fixtures on {date_str}...")
        
        try:
            # Initialize predictor
            predictor = MultiMarketPredictor(self.api_key)
            
            all_predictions = []
            
            for fixture in fixtures:
                try:
                    # Generate odds and analyze markets
                    odds = predictor.generate_realistic_odds(fixture)
                    predictions = predictor.analyze_all_markets(odds)
                    
                    if predictions:
                        # Add match context to each prediction
                        for pred in predictions:
                            pred.update({
                                'date': date_str,
                                'kick_off': fixture.get('kick_off', ''),
                                'home_team': fixture.get('home_team', ''),
                                'away_team': fixture.get('away_team', ''),
                                'league': fixture.get('league', ''),
                                'country': fixture.get('country', '')
                            })
                        
                        all_predictions.extend(predictions)
                        
                except Exception as e:
                    print(f"   ⚠️ Error analyzing {fixture.get('home_team', 'Unknown')} vs {fixture.get('away_team', 'Unknown')}: {e}")
                    continue
            
            if not all_predictions:
                return []
            
            # Apply simple filtering (since enhanced strategy had issues)
            # Filter for quality picks with reasonable edge and confidence
            selected_picks = []
            for pred in all_predictions:
                confidence = pred.get('confidence_percent', 0)
                edge = pred.get('edge_percent', 0)
                quality_score = pred.get('quality_score', 0)
                odds = pred.get('odds', 0)
                
                # Apply reasonable selection criteria
                if (confidence >= 65.0 and 
                    edge >= 15.0 and 
                    quality_score >= 0.2 and
                    1.4 <= odds <= 3.5):  # Reasonable odds range
                    
                    selected_picks.append(pred)
            
            # Limit to top 8 picks per day based on quality score
            selected_picks.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            selected_picks = selected_picks[:8]
            
            print(f"   ✅ Selected {len(selected_picks)} high-quality picks from {len(all_predictions)} predictions")
            return selected_picks
            
        except Exception as e:
            print(f"   ❌ Error generating picks for {date_str}: {e}")
            return []
    
    def get_real_result_for_pick_2024(self, pick: Dict) -> Dict:
        """Get real historical result for a 2024 pick"""
        
        home_team = pick.get('home_team')
        away_team = pick.get('away_team')
        match_date = pick.get('date')
        
        try:
            # Search for the fixture result
            result = self.results_fetcher.search_fixture_by_teams(home_team, away_team, match_date)
            
            if result and result.get('status') == 'Finished':
                return {
                    'verified': True,
                    'home_score': result.get('home_score', 0),
                    'away_score': result.get('away_score', 0),
                    'total_goals': result.get('home_score', 0) + result.get('away_score', 0),
                    'total_corners': result.get('total_corners', 0),
                    'btts': result.get('home_score', 0) > 0 and result.get('away_score', 0) > 0,
                    'match_status': 'Finished'
                }
            else:
                return None
                
        except Exception as e:
            print(f"   ⚠️ Error fetching result for {home_team} vs {away_team}: {e}")
            return None
    
    def evaluate_bet_outcome(self, bet_description: str, match_data: Dict) -> bool:
        """Evaluate if a bet won or lost based on real match outcome"""
        
        bet_lower = bet_description.lower()
        
        home_score = match_data['home_score']
        away_score = match_data['away_score']
        total_goals = match_data['total_goals']
        total_corners = match_data.get('total_corners', 0)
        btts = match_data['btts']
        
        # Goal totals
        if 'over 1.5' in bet_lower and 'goals' in bet_lower:
            return total_goals > 1.5
        elif 'under 1.5' in bet_lower and 'goals' in bet_lower:
            return total_goals < 1.5
        elif 'over 2.5' in bet_lower and 'goals' in bet_lower:
            return total_goals > 2.5
        elif 'under 2.5' in bet_lower and 'goals' in bet_lower:
            return total_goals < 2.5
        elif 'over 3.5' in bet_lower and 'goals' in bet_lower:
            return total_goals > 3.5
        elif 'under 3.5' in bet_lower and 'goals' in bet_lower:
            return total_goals < 3.5
        
        # Team totals
        elif 'home team over 1.5' in bet_lower:
            return home_score > 1.5
        elif 'home team under 1.5' in bet_lower:
            return home_score < 1.5
        elif 'away team over 1.5' in bet_lower:
            return away_score > 1.5
        elif 'away team under 1.5' in bet_lower:
            return away_score < 1.5
        
        # BTTS
        elif 'both teams to score - yes' in bet_lower:
            return btts
        elif 'both teams to score - no' in bet_lower:
            return not btts
        
        # Corners
        elif 'over 9.5' in bet_lower and 'corners' in bet_lower:
            return total_corners > 9.5
        elif 'under 9.5' in bet_lower and 'corners' in bet_lower:
            return total_corners < 9.5
        elif 'over 11.5' in bet_lower and 'corners' in bet_lower:
            return total_corners > 11.5
        elif 'under 11.5' in bet_lower and 'corners' in bet_lower:
            return total_corners < 11.5
        
        # Match result
        elif bet_lower == 'home':
            return home_score > away_score
        elif bet_lower == 'draw':
            return home_score == away_score
        elif bet_lower == 'away':
            return away_score > home_score
        
        # Handicaps (simplified)
        elif 'home team +1' in bet_lower:
            return (home_score + 1) > away_score
        elif 'away team +1' in bet_lower:
            return (away_score + 1) > home_score
        elif 'home team -1' in bet_lower:
            return (home_score - 1) > away_score
        elif 'away team -1' in bet_lower:
            return (away_score - 1) > home_score
        
        # Double chance (simplified)
        elif 'home/draw' in bet_lower:
            return home_score >= away_score
        elif 'home/away' in bet_lower:
            return home_score != away_score
        elif 'draw/away' in bet_lower:
            return home_score <= away_score
        
        # Default: return False for unknown bet types
        print(f"   ⚠️ Unknown bet type: {bet_description}")
        return False
    
    def run_comprehensive_backtest_2024(self) -> Dict:
        """Run the complete 2024 historical backtest"""
        
        print(f"🚀 STARTING 2024 SEASON HISTORICAL BACKTEST")
        print("=" * 60)
        
        dates = self.get_date_range()
        all_results = []
        
        total_picks = 0
        total_wins = 0
        total_losses = 0
        total_verified = 0
        total_unverified = 0
        running_pnl = 0.0
        
        for i, date_str in enumerate(dates, 1):
            print(f"\n📅 Processing {date_str} ({i}/{len(dates)})...")
            
            # Get 2024 historical fixtures
            fixtures = self.get_historical_fixtures_2024(date_str)
            
            if not fixtures:
                print(f"   ⚠️ No fixtures found for {date_str}")
                continue
            
            # Generate picks for this date
            picks = self.generate_historical_picks_2024(fixtures, date_str)
            
            if not picks:
                print(f"   ⚠️ No picks generated for {date_str}")
                continue
            
            # Process each pick
            date_wins = 0
            date_losses = 0
            date_verified = 0
            date_pnl = 0.0
            
            for pick in picks:
                # Get real result
                result = self.get_real_result_for_pick_2024(pick)
                
                if result:
                    # Evaluate bet outcome
                    bet_won = self.evaluate_bet_outcome(pick['bet_description'], result)
                    
                    # Calculate P&L
                    odds = pick['odds']
                    if bet_won:
                        pnl = (odds - 1) * self.bet_amount
                        outcome = 'Win'
                        date_wins += 1
                    else:
                        pnl = -self.bet_amount
                        outcome = 'Loss'
                        date_losses += 1
                    
                    date_pnl += pnl
                    date_verified += 1
                    
                    # Store result
                    result_entry = {
                        'date': date_str,
                        'home_team': pick['home_team'],
                        'away_team': pick['away_team'],
                        'league': pick['league'],
                        'country': pick['country'],
                        'market': pick['market'],
                        'bet_description': pick['bet_description'],
                        'odds': odds,
                        'confidence_percent': pick.get('confidence_percent', 0),
                        'edge_percent': pick.get('edge_percent', 0),
                        'quality_score': pick.get('quality_score', 0),
                        'bet_outcome': outcome,
                        'home_score': result['home_score'],
                        'away_score': result['away_score'],
                        'total_goals': result['total_goals'],
                        'total_corners': result.get('total_corners', 0),
                        'btts': result['btts'],
                        'bet_amount': self.bet_amount,
                        'actual_pnl': pnl,
                        'verified': True
                    }
                    all_results.append(result_entry)
                    
                else:
                    print(f"     ⚠️ No result found for {pick['home_team']} vs {pick['away_team']}")
                    total_unverified += 1
            
            # Update totals
            total_picks += len(picks)
            total_wins += date_wins
            total_losses += date_losses
            total_verified += date_verified
            running_pnl += date_pnl
            
            if date_verified > 0:
                print(f"   📊 {date_str}: {date_verified} verified picks | {date_wins}W-{date_losses}L | P&L: ${date_pnl:+.2f}")
            
            # Small delay to avoid API rate limits
            time.sleep(0.1)
        
        # Calculate final stats
        win_rate = (total_wins / total_verified * 100) if total_verified > 0 else 0
        total_staked = total_verified * self.bet_amount
        roi = (running_pnl / total_staked * 100) if total_staked > 0 else 0
        
        backtest_summary = {
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'total_days': len(dates),
            'total_picks_generated': total_picks,
            'total_verified_picks': total_verified,
            'total_unverified_picks': total_unverified,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'win_rate': win_rate,
            'total_staked': total_staked,
            'total_pnl': running_pnl,
            'roi': roi,
            'results': all_results
        }
        
        print(f"\n🎯 2024 BACKTEST COMPLETE!")
        print(f"📊 {total_verified} verified picks | {total_wins}W-{total_losses}L | Win Rate: {win_rate:.1f}%")
        print(f"💰 P&L: ${running_pnl:+.2f} | ROI: {roi:+.1f}% | Total Staked: ${total_staked:.2f}")
        
        return backtest_summary
    
    def save_backtest_results_2024(self, backtest_data: Dict) -> str:
        """Save comprehensive 2024 backtest results"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save CSV results
        csv_filename = f"2024_season_backtest_results_{timestamp}.csv"
        csv_path = f"./soccer/output reports/{csv_filename}"
        
        if backtest_data['results']:
            fieldnames = [
                'date', 'home_team', 'away_team', 'league', 'country',
                'market', 'bet_description', 'odds', 'confidence_percent',
                'edge_percent', 'quality_score', 'bet_outcome', 'home_score',
                'away_score', 'total_goals', 'total_corners', 'btts',
                'bet_amount', 'actual_pnl', 'verified'
            ]
            
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(backtest_data['results'])
        
        # Save formatted report
        report_filename = f"2024_season_backtest_report_{timestamp}.txt"
        report_path = f"./soccer/output reports/{report_filename}"
        
        with open(report_path, 'w') as f:
            f.write("🏆 2024 SEASON HISTORICAL BACKTEST REPORT 🏆\n")
            f.write("=" * 60 + "\n")
            f.write(f"📅 Backtest Period: {backtest_data['start_date']} to {backtest_data['end_date']}\n")
            f.write(f"🏟️ Peak Season Analysis: Major European leagues active\n")
            f.write(f"📊 Analysis Period: {backtest_data['total_days']} days\n")
            f.write(f"💰 Standard Bet Amount: ${self.bet_amount}\n\n")
            
            f.write("📊 OVERALL PERFORMANCE:\n")
            f.write("-" * 30 + "\n")
            f.write(f"🎯 Total Picks Generated: {backtest_data['total_picks_generated']}\n")
            f.write(f"✅ Verified Picks: {backtest_data['total_verified_picks']}\n")
            f.write(f"❌ Unverified Picks: {backtest_data['total_unverified_picks']}\n")
            f.write(f"🏆 Wins: {backtest_data['total_wins']}\n")
            f.write(f"💔 Losses: {backtest_data['total_losses']}\n")
            f.write(f"📈 Win Rate: {backtest_data['win_rate']:.1f}%\n")
            f.write(f"💰 Total P&L: ${backtest_data['total_pnl']:+.2f}\n")
            f.write(f"💸 Total Staked: ${backtest_data['total_staked']:.2f}\n")
            f.write(f"📊 ROI: {backtest_data['roi']:+.1f}%\n\n")
            
            if backtest_data['results']:
                # Group by league
                league_stats = {}
                for result in backtest_data['results']:
                    league = result['league']
                    if league not in league_stats:
                        league_stats[league] = {'wins': 0, 'losses': 0, 'pnl': 0}
                    
                    if result['bet_outcome'] == 'Win':
                        league_stats[league]['wins'] += 1
                    else:
                        league_stats[league]['losses'] += 1
                    league_stats[league]['pnl'] += result['actual_pnl']
                
                f.write("🏟️ PERFORMANCE BY LEAGUE:\n")
                f.write("-" * 30 + "\n")
                for league, stats in sorted(league_stats.items()):
                    total = stats['wins'] + stats['losses']
                    win_rate = (stats['wins'] / total * 100) if total > 0 else 0
                    f.write(f"🏆 {league}:\n")
                    f.write(f"   📊 {stats['wins']}/{total} ({win_rate:.1f}%) | P&L: ${stats['pnl']:+.2f}\n")
                
                # Group by market
                market_stats = {}
                for result in backtest_data['results']:
                    market = result['market']
                    if market not in market_stats:
                        market_stats[market] = {'wins': 0, 'losses': 0, 'pnl': 0}
                    
                    if result['bet_outcome'] == 'Win':
                        market_stats[market]['wins'] += 1
                    else:
                        market_stats[market]['losses'] += 1
                    market_stats[market]['pnl'] += result['actual_pnl']
                
                f.write(f"\n🎯 PERFORMANCE BY MARKET:\n")
                f.write("-" * 30 + "\n")
                for market, stats in sorted(market_stats.items()):
                    total = stats['wins'] + stats['losses']
                    win_rate = (stats['wins'] / total * 100) if total > 0 else 0
                    f.write(f"🎲 {market}:\n")
                    f.write(f"   📊 {stats['wins']}/{total} ({win_rate:.1f}%) | P&L: ${stats['pnl']:+.2f}\n")
                
                f.write(f"\n📅 SAMPLE RECENT RESULTS (Last 10):\n")
                f.write("-" * 40 + "\n")
                recent_results = sorted(backtest_data['results'], key=lambda x: x['date'])[-10:]
                for result in recent_results:
                    outcome_emoji = "✅" if result['bet_outcome'] == 'Win' else "❌"
                    f.write(f"{outcome_emoji} {result['date']} | {result['home_team']} vs {result['away_team']}\n")
                    f.write(f"   🎯 {result['bet_description']} @ {result['odds']:.2f} → ${result['actual_pnl']:+.2f}\n")
                    f.write(f"   🏟️ {result['league']} | Score: {result['home_score']}-{result['away_score']}\n\n")
            
            f.write("⚠️ IMPORTANT NOTES:\n")
            f.write("• All results are based on real 2024 season match outcomes\n")
            f.write("• Only verified results from API-Sports are included\n")
            f.write("• This represents actual system performance during peak season\n")
            f.write("• Performance is based on followed leagues only\n")
            f.write("• Results are for analysis purposes only\n\n")
        
        print(f"💾 2024 Backtest results saved:")
        print(f"   📊 CSV: {csv_filename}")
        print(f"   📋 Report: {report_filename}")
        
        return report_path

def main():
    """Run the comprehensive 2024 historical backtest"""
    backtest_system = HistoricalBacktest2024()
    
    # Run the backtest
    results = backtest_system.run_comprehensive_backtest_2024()
    
    # Save results
    report_path = backtest_system.save_backtest_results_2024(results)
    
    print(f"\n✅ 2024 season backtest complete!")
    print(f"📊 Report saved: {os.path.basename(report_path)}")

if __name__ == "__main__":
    main()