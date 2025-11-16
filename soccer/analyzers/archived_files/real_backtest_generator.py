#!/usr/bin/env python3
"""
Real Data Backtest Generator

Generates backtested report from August 1 through September 9, 2025
Using real API data for fixtures and results
"""

import pandas as pd
from datetime import datetime, timedelta
import requests
import json
import time
from real_data_integration import RealDataIntegration
from real_results_fetcher import RealResultsFetcher
from multi_market_predictor import MultiMarketPredictor

class RealBacktestGenerator:
    """Generate backtest report using real API data"""
    
    def __init__(self):
        self.start_date = datetime.strptime('2025-08-01', '%Y-%m-%d')
        self.end_date = datetime.strptime('2025-09-09', '%Y-%m-%d')  # Through yesterday
        
        # Initialize our real data systems
        self.data_integrator = RealDataIntegration()
        self.results_fetcher = RealResultsFetcher()
        self.predictor = MultiMarketPredictor("960c628e1c91c4b1f125e1eec52ad862")
        
        print(f"🕰️ Real Backtest Generator initialized")
        print(f"📅 Period: {self.start_date.strftime('%B %d, %Y')} to {self.end_date.strftime('%B %d, %Y')}")
        print(f"📊 Total days: {(self.end_date - self.start_date).days + 1}")
    
    def generate_backtest_report(self):
        """Generate comprehensive backtest report with real data"""
        
        print("🔄 Generating comprehensive backtest report...")
        
        all_picks = []
        total_days = (self.end_date - self.start_date).days + 1
        successful_days = 0
        
        current_date = self.start_date
        while current_date <= self.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            day_name = current_date.strftime('%A')
            
            print(f"\n📅 Processing {day_name}, {date_str}...")
            
            # Get real fixtures for this date
            try:
                daily_picks = self.process_date(date_str)
                if daily_picks:
                    all_picks.extend(daily_picks)
                    successful_days += 1
                    print(f"   ✅ Found {len(daily_picks)} picks")
                else:
                    print(f"   ⏳ No fixtures/picks for this date")
                
                # Rate limiting to avoid API limits
                time.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error processing {date_str}: {e}")
            
            current_date += timedelta(days=1)
        
        print(f"\n📊 Backtest Data Collection Complete:")
        print(f"   🗓️ Days processed: {successful_days}/{total_days}")
        print(f"   🎯 Total picks generated: {len(all_picks)}")
        
        if all_picks:
            # Save picks and generate comprehensive report
            self.save_backtest_data(all_picks)
            self.generate_performance_report(all_picks)
            
        return all_picks
    
    def process_date(self, date_str: str):
        """Process a single date to get fixtures and picks"""
        
        # Get real fixtures for this date
        real_fixtures = self.data_integrator.get_real_fixtures_with_odds(date_str)
        
        if not real_fixtures:
            return []
        
        # Filter for significant fixtures (major leagues, good odds coverage)
        quality_fixtures = []
        for fixture in real_fixtures:
            # Skip if missing key odds data
            if (fixture.get('home_odds', 0) == 0 or 
                fixture.get('over_25_odds', 0) == 0 or
                fixture.get('btts_yes_odds', 0) == 0):
                continue
                
            # Focus on major leagues and competitions
            league = fixture['league'].lower()
            if any(keyword in league for keyword in [
                'premier league', 'la liga', 'serie a', 'bundesliga', 'ligue 1',
                'champions league', 'europa league', 'world cup', 'mls',
                'championship', 'liga mx', 'serie b', 'brazilian'
            ]):
                quality_fixtures.append(fixture)
        
        if not quality_fixtures:
            return []
        
        print(f"   📊 Found {len(quality_fixtures)} quality fixtures")
        
        # Generate predictions for these fixtures
        daily_picks = []
        for fixture in quality_fixtures[:10]:  # Limit to top 10 to avoid API overload
            try:
                # Get picks for this fixture
                fixture_picks = self.get_fixture_picks(fixture, date_str)
                daily_picks.extend(fixture_picks)
                
            except Exception as e:
                print(f"   ⚠️ Error processing fixture {fixture['home_team']} vs {fixture['away_team']}: {e}")
                continue
        
        return daily_picks
    
    def get_fixture_picks(self, fixture, date_str):
        """Get betting picks for a specific fixture"""
        
        # Convert fixture to format expected by predictor
        match_data = {
            'date': date_str,
            'kick_off': fixture['kick_off'],
            'home_team': fixture['home_team'],
            'away_team': fixture['away_team'],
            'league': fixture['league'],
            'home_odds': fixture.get('home_odds', 2.0),
            'draw_odds': fixture.get('draw_odds', 3.0),
            'away_odds': fixture.get('away_odds', 3.0),
            'over_25_odds': fixture.get('over_25_odds', 2.0),
            'under_25_odds': fixture.get('under_25_odds', 1.8),
            'btts_yes_odds': fixture.get('btts_yes_odds', 1.9),
            'btts_no_odds': fixture.get('btts_no_odds', 1.9),
            'over_95_corners_odds': fixture.get('over_95_corners_odds', 2.0),
            'over_15_odds': fixture.get('over_15_odds', 1.3)
        }
        
        # Get predictions from our model
        try:
            predictions = self.predictor.predict_all_markets([match_data])
            
            # Filter for high-value picks (edge > 10%, confidence > 60%)
            quality_picks = []
            for pred in predictions:
                if pred['edge_pct'] > 10.0 and pred['confidence_pct'] > 60.0:
                    # Add real result when available
                    real_result = self.get_real_result(
                        fixture['home_team'], 
                        fixture['away_team'], 
                        date_str
                    )
                    
                    if real_result:
                        pred.update(real_result)
                        pred['bet_outcome'] = self.evaluate_bet_outcome(
                            pred['bet_description'], 
                            real_result
                        )
                        pred['actual_pnl'] = self.calculate_pnl(pred)
                    else:
                        pred['bet_outcome'] = 'Unknown'
                        pred['actual_pnl'] = 0
                        pred['home_score'] = None
                        pred['away_score'] = None
                    
                    quality_picks.append(pred)
            
            return quality_picks
            
        except Exception as e:
            print(f"   ⚠️ Prediction error: {e}")
            return []
    
    def get_real_result(self, home_team, away_team, date_str):
        """Get real match result if available"""
        
        try:
            result = self.results_fetcher.get_match_result(home_team, away_team, date_str)
            if result and result.get('finished'):
                return {
                    'home_score': result['home_score'],
                    'away_score': result['away_score'],
                    'total_goals': result['total_goals'],
                    'total_corners': result.get('total_corners', 0),
                    'btts': result['btts'],
                    'match_status': 'Completed'
                }
        except:
            pass
        
        return None
    
    def evaluate_bet_outcome(self, bet_description, match_data):
        """Evaluate if bet won or lost based on real result"""
        
        bet_lower = bet_description.lower()
        total_goals = match_data['total_goals']
        total_corners = match_data.get('total_corners', 0)
        btts = match_data['btts']
        
        # Goals markets
        if 'over 1.5 goals' in bet_lower:
            return 'Win' if total_goals > 1.5 else 'Loss'
        elif 'under 1.5 goals' in bet_lower:
            return 'Win' if total_goals < 1.5 else 'Loss'
        elif 'over 2.5 goals' in bet_lower:
            return 'Win' if total_goals > 2.5 else 'Loss'
        elif 'under 2.5 goals' in bet_lower:
            return 'Win' if total_goals < 2.5 else 'Loss'
        elif 'over 3.5 goals' in bet_lower:
            return 'Win' if total_goals > 3.5 else 'Loss'
        elif 'under 3.5 goals' in bet_lower:
            return 'Win' if total_goals < 3.5 else 'Loss'
        
        # BTTS markets
        elif 'both teams to score - yes' in bet_lower or 'btts yes' in bet_lower:
            return 'Win' if btts else 'Loss'
        elif 'both teams to score - no' in bet_lower or 'btts no' in bet_lower:
            return 'Win' if not btts else 'Loss'
        
        # Corner markets
        elif 'over 9.5' in bet_lower and 'corners' in bet_lower:
            return 'Win' if total_corners > 9.5 else 'Loss'
        elif 'under 9.5' in bet_lower and 'corners' in bet_lower:
            return 'Win' if total_corners < 9.5 else 'Loss'
        
        return 'Unknown'
    
    def calculate_pnl(self, prediction):
        """Calculate P&L for a prediction"""
        
        stake = 25.0  # Standard $25 stake
        odds = prediction['odds']
        outcome = prediction['bet_outcome']
        
        if outcome == 'Win':
            return (odds - 1) * stake
        elif outcome == 'Loss':
            return -stake
        else:
            return 0
    
    def save_backtest_data(self, picks):
        """Save backtest data to CSV"""
        
        if not picks:
            return
        
        df = pd.DataFrame(picks)
        
        # Calculate running totals
        running_total = 0
        running_totals = []
        
        for _, pick in df.iterrows():
            running_total += pick.get('actual_pnl', 0)
            running_totals.append(running_total)
        
        df['running_total'] = running_totals
        
        # Save to CSV
        output_file = f"./soccer/output reports/backtest_report_aug01_sep09.csv"
        df.to_csv(output_file, index=False)
        
        print(f"💾 Backtest data saved: {output_file}")
    
    def generate_performance_report(self, picks):
        """Generate detailed performance report"""
        
        if not picks:
            print("❌ No picks to analyze")
            return
        
        df = pd.DataFrame(picks)
        
        # Filter out unknown outcomes
        completed_picks = df[df['bet_outcome'].isin(['Win', 'Loss'])]
        
        if len(completed_picks) == 0:
            print("❌ No completed picks with results")
            return
        
        # Performance metrics
        total_picks = len(completed_picks)
        wins = len(completed_picks[completed_picks['bet_outcome'] == 'Win'])
        losses = len(completed_picks[completed_picks['bet_outcome'] == 'Loss'])
        win_rate = (wins / total_picks) * 100
        
        total_pnl = completed_picks['actual_pnl'].sum()
        avg_pnl_per_pick = total_pnl / total_picks
        
        # Best and worst picks
        best_pick = completed_picks.loc[completed_picks['actual_pnl'].idxmax()]
        worst_pick = completed_picks.loc[completed_picks['actual_pnl'].idxmin()]
        
        # Generate report
        report_content = f"""
🏆 COMPREHENSIVE BACKTEST REPORT
=================================================
📅 Period: August 1 - September 9, 2025
🔍 Using Real API Data (API-Sports & FootyStats)

📊 OVERALL PERFORMANCE:
-----------------------
🎯 Total Picks: {total_picks}
✅ Wins: {wins}
❌ Losses: {losses}
📈 Win Rate: {win_rate:.1f}%

💰 FINANCIAL PERFORMANCE:
--------------------------
💵 Total P&L: ${total_pnl:+,.2f}
📊 Average per Pick: ${avg_pnl_per_pick:+,.2f}
🎪 ROI: {(total_pnl / (total_picks * 25)) * 100:+.1f}%

🌟 BEST PICK:
-------------
📅 {best_pick['date']} | {best_pick['home_team']} vs {best_pick['away_team']}
🎯 {best_pick['bet_description']} @ {best_pick['odds']:.2f}
💰 P&L: ${best_pick['actual_pnl']:+,.2f}
📊 Result: {best_pick['home_score']}-{best_pick['away_score']} 

😱 WORST PICK:
--------------
📅 {worst_pick['date']} | {worst_pick['home_team']} vs {worst_pick['away_team']}
🎯 {worst_pick['bet_description']} @ {worst_pick['odds']:.2f}
💰 P&L: ${worst_pick['actual_pnl']:+,.2f}
📊 Result: {worst_pick['home_score']}-{worst_pick['away_score']}

📈 MARKET BREAKDOWN:
--------------------
"""
        
        # Market performance
        market_stats = completed_picks.groupby('bet_description').agg({
            'actual_pnl': ['count', 'sum', 'mean'],
            'bet_outcome': lambda x: (x == 'Win').sum()
        }).round(2)
        
        for market in market_stats.index:
            count = market_stats.loc[market, ('actual_pnl', 'count')]
            total_pnl = market_stats.loc[market, ('actual_pnl', 'sum')]
            wins = market_stats.loc[market, ('bet_outcome', '<lambda>')]
            win_rate = (wins / count) * 100
            
            report_content += f"{market}: {count} picks | {win_rate:.1f}% | ${total_pnl:+.2f}\n"
        
        report_content += f"""
⚠️ IMPORTANT NOTES:
-------------------
• Results based on real API data from API-Sports
• Some matches may not have results if not found in API
• Win rates and P&L calculated only for completed matches
• Standard $25 stake used for all calculations

📊 Data Sources:
• Fixtures: API-Sports & FootyStats APIs
• Results: API-Sports historical data
• Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Save report
        report_file = f"./soccer/output reports/backtest_performance_report.txt"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        print(f"📊 Performance report saved: {report_file}")
        print(f"\n{report_content}")

def main():
    """Generate comprehensive backtest report"""
    
    generator = RealBacktestGenerator()
    picks = generator.generate_backtest_report()
    
    print(f"\n✅ Comprehensive backtest report complete!")
    if picks:
        print(f"📊 Check output reports folder for detailed analysis")

if __name__ == "__main__":
    main()