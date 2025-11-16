#!/usr/bin/env python3
"""
Daily Betting Report Generator

Generates today's best betting picks using the multi-market prediction system
"""

from multi_market_predictor import MultiMarketPredictor
from daily_comprehensive_games_reporter import DailyComprehensiveGamesReporter
from enhanced_daily_fixtures_generator import EnhancedDailyFixturesGenerator
from cumulative_picks_tracker import CumulativePicksTracker
from high_confidence_all_leagues_reporter import HighConfidenceAllLeaguesReporter
import pandas as pd
from datetime import datetime, timedelta
import random
import csv
import numpy as np
import requests
import json

class DailyBettingReportGenerator:
    """Generate daily betting reports with best picks"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.predictor = MultiMarketPredictor(api_key)
        self.comprehensive_reporter = DailyComprehensiveGamesReporter(api_key)
        self.enhanced_fixture_generator = EnhancedDailyFixturesGenerator(api_key)
        self.cumulative_tracker = CumulativePicksTracker(api_key)
        # Use actual current date
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.day_name = datetime.now().strftime('%A')
        
        # Football Data API configuration
        self.football_api_base_url = "https://api.football-data-api.com"
        
    def generate_todays_fixtures(self):
        """Get today's real fixtures from API-Sports"""
        
        print(f"📅 Getting real fixtures for {self.day_name}, {self.today}...")
        
        # Get real fixtures from API-Sports
        real_fixtures = self.get_real_api_fixtures()
        
        print(f"✅ Real fixture retrieval complete")
        print(f"🌍 Total real fixtures available: {len(real_fixtures)}")
        
        return real_fixtures
    
    def get_real_api_fixtures(self):
        """Get real fixtures with real odds from our integration system"""
        
        # Import and use our real data integration
        from real_data_integration import RealDataIntegration
        
        try:
            print(f"🔌 Using Real Data Integration for {self.today}")
            integrator = RealDataIntegration()
            
            # Get real fixtures with real odds from both APIs
            real_fixtures = integrator.update_daily_system_with_real_data(self.today)
            
            print(f"✅ Retrieved {len(real_fixtures)} total real fixtures")
            
            # Get our followed leagues list
            followed_leagues = self.get_followed_leagues()
            print(f"📋 Following {len(followed_leagues)} leagues")
            
            # Filter for followed leagues only
            filtered_fixtures = []
            league_counts = {}
            excluded_counts = {}
            
            for fixture in real_fixtures:
                league = fixture['league']
                country = fixture.get('country', 'Unknown')
                if self.is_followed_league(league, followed_leagues, country):
                    filtered_fixtures.append(fixture)
                    league_counts[league] = league_counts.get(league, 0) + 1
                else:
                    excluded_counts[f"{league} ({country})"] = excluded_counts.get(f"{league} ({country})", 0) + 1
            
            print(f"✅ Filtered to {len(filtered_fixtures)} matches in followed leagues")
            
            if league_counts:
                print(f"🏆 Followed leagues active today:")
                for league, count in sorted(league_counts.items()):
                    print(f"   📊 {league}: {count} match{'es' if count > 1 else ''}")
            else:
                print(f"⚠️ No matches found in followed leagues today")
                print(f"📊 Available leagues (excluded):")
                for league, count in sorted(excluded_counts.items()):
                    print(f"   ❌ {league}: {count} match{'es' if count > 1 else ''}")
            
            return filtered_fixtures
            
        except Exception as e:
            print(f"❌ Error getting real fixtures with integration: {e}")
            return []
    
    def get_followed_leagues(self):
        """Get list of leagues we follow from our database"""
        try:
            df = pd.read_csv('/Users/dickgibbons/soccer-betting-python/soccer/output reports/UPDATED_supported_leagues_database.csv')
            return df['league_name'].tolist()
        except Exception as e:
            print(f"⚠️ Could not load leagues database: {e}")
            print("📊 Using fallback leagues list")
            # Fallback list of major leagues
            return [
                'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
                'Championship', 'Serie B', 'Eredivisie', 'Scottish Premiership',
                'MLS', 'Liga MX', 'Brazilian Serie A', 'Brazilian Serie B',
                'Argentine Primera División', 'UEFA Champions League', 'UEFA Europa League',
                'WC Qualification Europe', 'WC Qualification Africa', 'WC Qualification Asia',
                'Copa Libertadores', 'J1 League', 'K League 1'
            ]
    
    def is_followed_league(self, league_name, followed_leagues, country=None):
        """Check if a league is one we follow - STRICT database-only matching"""
        
        # ONLY use leagues from our database - no fallback logic
        if league_name in followed_leagues:
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
        
        # Check for exact matches with common variations
        league_variations = {
            'Ekstraklasa': ['ekstraklasa'],
            'La Liga': ['la liga', 'primera division'],
            'Serie A': ['serie a'],
            'Bundesliga': ['bundesliga'], 
            'Premier League': ['premier league'],
            'Ligue 1': ['ligue 1'],
            'Championship': ['championship'],
            'MLS': ['mls', 'major league soccer'],
            'Liga MX': ['liga mx'],
            'Brazil Serie A': ['brazilian serie a', 'brazil serie a'],
            'Brazil Serie B': ['brazilian serie b', 'brazil serie b'],
            'UEFA Champions League': ['uefa champions league', 'champions league'],
            'UEFA Europa League': ['uefa europa league', 'europa league'],
            'WC Qualification Europe': ['wc qualification europe', 'world cup qualification europe'],
            'WC Qualification Africa': ['wc qualification africa', 'world cup qualification africa'],
            'WC Qualification Asia': ['wc qualification asia', 'world cup qualification asia']
        }
        
        league_lower = league_name.lower()
        
        # Check for variations of followed leagues
        for followed_league in followed_leagues:
            variations = league_variations.get(followed_league, [followed_league.lower()])
            if league_lower in variations:
                return True
        
        # REJECT everything else - no fallback to hardcoded lists
        return False
    
    def format_league_name(self, api_league_name):
        """Format league name from API to our standard format"""
        league_mapping = {
            'premier-league': 'Premier League',
            'la-liga': 'La Liga',
            'serie-a': 'Serie A',
            'bundesliga': 'Bundesliga',
            'ligue-1': 'Ligue 1',
            'champions-league': 'UEFA Champions League',
            'europa-league': 'UEFA Europa League'
        }
        return league_mapping.get(api_league_name.lower(), api_league_name)
    
    
    def analyze_todays_matches(self, matches):
        """Analyze all today's matches for betting opportunities"""
        
        print(f"🔍 Analyzing {len(matches)} matches for betting opportunities...")
        
        all_opportunities = []
        
        for match in matches:
            # Generate comprehensive odds for this match
            odds = self.predictor.generate_realistic_odds()
            
            # Override with the main market odds we have, ensuring no zero odds
            odds.update({
                'home_ml': max(match['home_odds'], 1.01),
                'draw_ml': max(match['draw_odds'], 1.01), 
                'away_ml': max(match['away_odds'], 1.01)
            })
            
            # Analyze all markets
            opportunities = self.predictor.analyze_all_markets(odds)
            
            # Add match context to each opportunity
            for opp in opportunities:
                opp.update({
                    'kick_off': match['kick_off'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'league': match['league'],
                    'country': match.get('country', 'Unknown')
                })
                all_opportunities.append(opp)
        
        # Sort by expected value
        all_opportunities.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return all_opportunities
    
    def generate_daily_report(self):
        """Generate comprehensive daily betting report"""
        
        print(f"📅 Generating Daily Betting Report for {self.day_name}, {self.today}")
        print("=" * 60)
        
        # Load or train models
        try:
            model_file = "/Users/dickgibbons/soccer-betting-python/soccer/multi_market_models.pkl"
            self.predictor.market_models = {}  # Reset to force training with new data
        except:
            pass
        
        # Generate today's fixtures
        todays_matches = self.generate_todays_fixtures()
        print(f"⚽ Found {len(todays_matches)} matches scheduled for today")
        
        # Analyze all matches
        opportunities = self.analyze_todays_matches(todays_matches)
        
        if not opportunities:
            print("❌ No betting opportunities found for today")
            return None
        
        print(f"💎 Found {len(opportunities)} potential value bets")
        
        # Filter for best opportunities only
        best_opportunities = self.filter_best_opportunities(opportunities)
        
        # Create daily report
        daily_report = {
            'date': self.today,
            'day_name': self.day_name,
            'total_matches': len(todays_matches),
            'total_opportunities': len(opportunities),
            'recommended_bets': len(best_opportunities),
            'matches': todays_matches,
            'best_bets': best_opportunities
        }
        
        # Save report
        self.save_daily_report(daily_report)
        
        # Generate high confidence favorites report
        print(f"\n🎯 Generating high confidence Over 1.5 Goals favorites report...")
        self.generate_favorites_report(opportunities)
        
        # Also generate comprehensive games overview
        print(f"\n🌍 Generating comprehensive games overview...")
        comprehensive_data = self.comprehensive_reporter.generate_comprehensive_daily_report()
        
        if comprehensive_data:
            print(f"📊 Comprehensive overview: {comprehensive_data['total_games']} total games, {comprehensive_data['followed_games']} in followed leagues")
        
        # Generate high confidence all-leagues report
        print(f"\n🌍 Generating high confidence all-leagues report...")
        all_leagues_reporter = HighConfidenceAllLeaguesReporter(self.api_key)
        all_leagues_data = all_leagues_reporter.generate_daily_high_confidence_report()
        
        if all_leagues_data and all_leagues_data['picks']:
            print(f"🎯 High confidence all-leagues: {len(all_leagues_data['picks'])} opportunities from {all_leagues_data['total_leagues']} leagues")
        else:
            print(f"⚠️ No high confidence opportunities found across all leagues")
        
        # Generate separate high confidence low odds report  
        print(f"\n🎯 Generating high confidence low odds report...")
        from high_confidence_reporter import HighConfidenceReporter
        high_conf_reporter = HighConfidenceReporter(self.api_key)
        high_conf_report = high_conf_reporter.generate_high_confidence_report(opportunities)
        
        if high_conf_report and high_conf_report.get('high_confidence_picks') > 0:
            print(f"✅ High confidence picks: {high_conf_report['high_confidence_picks']} safe bets found")
        else:
            print(f"⚠️ No high confidence picks found today")
        
        return daily_report
    
    def filter_best_opportunities(self, opportunities, max_bets=None):
        """Filter for today's best betting opportunities using improved backtest-based strategy"""
        
        print(f"⚖️ Using BALANCED STRATEGY to generate daily picks...")
        
        # Import our balanced strategy (generates picks while avoiding worst performers)
        from balanced_betting_strategy import BalancedBettingStrategy
        
        # Apply balanced filtering
        balanced_strategy = BalancedBettingStrategy()
        filtered_opportunities = balanced_strategy.apply_balanced_filtering(opportunities)
        
        if not filtered_opportunities:
            print("❌ No opportunities passed balanced filtering criteria")
            return []
        
        # Sort by balanced score (highest first)  
        filtered_opportunities.sort(key=lambda x: x.get('balanced_score', 0), reverse=True)
        
        # Apply max_bets limit if specified
        if max_bets and len(filtered_opportunities) > max_bets:
            filtered_opportunities = filtered_opportunities[:max_bets]
            print(f"📊 Limited to top {max_bets} opportunities")
        
        print(f"✅ {len(filtered_opportunities)} opportunities selected with balanced strategy")
        
        return filtered_opportunities
        
        # Apply enhanced selection strategy
        strategy = EnhancedSelectionStrategy()
        enhanced_picks = strategy.filter_enhanced_picks(formatted_predictions)
        
        # Convert back to original format
        quality_bets = []
        for pick in enhanced_picks:
            # Find original opportunity
            original_opp = None
            for opp in opportunities:
                if (opp.get('home_team', '') == pick['home_team'] and 
                    opp.get('away_team', '') == pick['away_team'] and
                    abs(opp.get('odds', 0) - pick['odds']) < 0.01):
                    original_opp = opp.copy()
                    break
            
            if original_opp:
                # Add enhanced metrics
                original_opp['enhanced_quality'] = pick['enhanced_quality']
                original_opp['tier'] = pick['tier']
                original_opp['position_size'] = pick['position_size']
                original_opp['stake_pct'] = pick['position_size']  # Use enhanced position sizing
                
                # Recalculate quality score with enhanced method
                original_opp['quality_score'] = pick['enhanced_quality']
                
                quality_bets.append(original_opp)
        
        print(f"🚀 Enhanced selection: {len(quality_bets)} premium opportunities identified")
        
        # Show tier distribution
        if quality_bets:
            tier_counts = {}
            for bet in quality_bets:
                tier = bet.get('tier', 'Unknown')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            print(f"   🏆 Tier distribution: {dict(tier_counts)}")
        
        return quality_bets
    
    def generate_favorites_report(self, opportunities):
        """Generate high confidence Over 1.5 Goals favorites report"""
        
        from high_confidence_favorites_report import HighConfidenceFavoritesReport
        
        try:
            favorites_generator = HighConfidenceFavoritesReport()
            favorites = favorites_generator.generate_favorites_report(opportunities)
            
            if favorites:
                print(f"   ✅ Generated favorites report with {len(favorites)} high-confidence Over 1.5 Goals picks")
            else:
                print(f"   ⚠️ No qualifying high-confidence favorites found today")
                
        except Exception as e:
            print(f"   ❌ Error generating favorites report: {e}")
    
    def save_daily_report(self, daily_report):
        """Save daily report to files"""
        
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Save detailed CSV
        csv_filename = f"/Users/dickgibbons/soccer-betting-python/soccer/output reports/daily_picks_{date_str}.csv"
        
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = [
                'date', 'kick_off', 'home_team', 'away_team', 'league', 'country',
                'market', 'bet_description', 'odds', 'recommended_stake_pct',
                'edge_percent', 'confidence_percent', 'expected_value',
                'quality_score', 'risk_level'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for bet in daily_report['best_bets']:
                # Get bet description
                bet_description = self.get_bet_description(bet['market'])
                risk_level = self.get_risk_level(bet['odds'])
                
                row = {
                    'date': daily_report['date'],
                    'kick_off': bet['kick_off'],
                    'home_team': bet['home_team'],
                    'away_team': bet['away_team'],
                    'league': bet['league'],
                    'country': bet.get('country', 'Unknown'),
                    'market': bet['market'],
                    'bet_description': bet_description,
                    'odds': bet['odds'],
                    'recommended_stake_pct': round(bet['kelly_fraction'] * 100, 1),
                    'edge_percent': round(bet['edge'] * 100, 1),
                    'confidence_percent': round(bet['confidence'] * 100, 1),
                    'expected_value': round(bet['expected_value'], 3),
                    'quality_score': round(bet.get('quality_score', bet.get('balanced_score', 0)), 3),
                    'risk_level': risk_level
                }
                writer.writerow(row)
        
        print(f"💾 Daily picks saved: daily_picks_{date_str}.csv")
        
        # Generate formatted report
        self.generate_formatted_report(daily_report, date_str)
        
        # Generate CSV version of the formatted report
        self.generate_formatted_report_csv(daily_report, date_str)
    
    def generate_formatted_report(self, daily_report, date_str):
        """Generate human-readable daily report"""
        
        report_filename = f"/Users/dickgibbons/soccer-betting-python/soccer/output reports/daily_report_{date_str}.txt"
        
        with open(report_filename, 'w') as f:
            f.write("⚽ DAILY SOCCER BETTING REPORT ⚽\n")
            f.write("=" * 50 + "\n")
            f.write(f"📅 {daily_report['day_name']}, {daily_report['date']}\n")
            f.write(f"🏟️ {daily_report['total_matches']} matches analyzed\n")
            f.write(f"🎯 {daily_report['recommended_bets']} high-value bets recommended\n\n")
            
            if daily_report['best_bets']:
                f.write("🌟 TODAY'S BEST BETS:\n")
                f.write("=" * 30 + "\n\n")
                
                for i, bet in enumerate(daily_report['best_bets'], 1):
                    bet_desc = self.get_bet_description(bet['market'])
                    
                    f.write(f"#{i} - {bet['kick_off']} | {bet['league']}\n")
                    f.write(f"   {bet['home_team']} vs {bet['away_team']}\n")
                    f.write(f"   🎯 BET: {bet_desc}\n")
                    f.write(f"   📊 ODDS: {bet['odds']:.2f}\n")
                    f.write(f"   💰 STAKE: {bet['kelly_fraction']*100:.1f}% of bankroll\n")
                    f.write(f"   📈 EDGE: {bet['edge']*100:.1f}%\n")
                    f.write(f"   🎪 CONFIDENCE: {bet['confidence']*100:.1f}%\n")
                    quality_score = bet.get('quality_score', bet.get('balanced_score', 0))
                    f.write(f"   ⭐ QUALITY: {quality_score:.3f}\n\n")
                
                f.write("📊 BETTING SUMMARY:\n")
                f.write("-" * 20 + "\n")
                
                total_edge = sum(bet['edge'] for bet in daily_report['best_bets'])
                avg_confidence = np.mean([bet['confidence'] for bet in daily_report['best_bets']])
                total_stake = sum(bet['kelly_fraction'] for bet in daily_report['best_bets'])
                
                f.write(f"Total Portfolio Edge: {total_edge*100:.1f}%\n")
                f.write(f"Average Confidence: {avg_confidence*100:.1f}%\n")
                f.write(f"Total Bankroll Risk: {total_stake*100:.1f}%\n")
                
                # Market breakdown
                f.write(f"\n📈 MARKETS COVERED:\n")
                markets = {}
                for bet in daily_report['best_bets']:
                    market_cat = self.classify_market_category(bet['market'])
                    markets[market_cat] = markets.get(market_cat, 0) + 1
                
                for market, count in markets.items():
                    f.write(f"   {market}: {count} bet{'s' if count > 1 else ''}\n")
            
            else:
                f.write("❌ No high-quality betting opportunities found today.\n")
                f.write("💡 Recommendation: Wait for better value opportunities.\n")
            
            f.write(f"\n⚠️ IMPORTANT REMINDERS:\n")
            f.write("• Only bet what you can afford to lose\n")
            f.write("• These are model predictions, not guarantees\n") 
            f.write("• Consider external factors (injuries, weather, team news)\n")
            f.write("• Use proper bankroll management\n")
            f.write("• Past performance doesn't guarantee future results\n")
        
        print(f"📋 Formatted report saved: daily_report_{date_str}.txt")
    
    def generate_formatted_report_csv(self, daily_report, date_str):
        """Generate CSV version of the formatted daily report"""
        
        csv_report_filename = f"/Users/dickgibbons/soccer-betting-python/soccer/output reports/daily_report_{date_str}.csv"
        
        with open(csv_report_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header information
            writer.writerow(['Report Type', 'Value'])
            writer.writerow(['Date', f"{daily_report['day_name']}, {daily_report['date']}"])
            writer.writerow(['Total Matches Analyzed', daily_report['total_matches']])
            writer.writerow(['High-Value Bets Recommended', daily_report['recommended_bets']])
            writer.writerow([])  # Empty row
            
            # Best bets header
            writer.writerow(['Rank', 'Kick Off', 'League', 'Country', 'Home Team', 'Away Team', 'Bet Type', 'Odds', 'Stake %', 'Edge %', 'Confidence %', 'Quality Score'])
            
            if daily_report['best_bets']:
                for i, bet in enumerate(daily_report['best_bets'], 1):
                    bet_desc = self.get_bet_description(bet['market'])
                    
                    writer.writerow([
                        f"#{i}",
                        bet['kick_off'],
                        bet['league'],
                        bet.get('country', 'Unknown'),
                        bet['home_team'],
                        bet['away_team'],
                        bet_desc,
                        f"{bet['odds']:.2f}",
                        f"{bet['kelly_fraction']*100:.1f}%",
                        f"{bet['edge']*100:.1f}%",
                        f"{bet['confidence']*100:.1f}%",
                        f"{bet.get('quality_score', bet.get('balanced_score', 0)):.3f}"
                    ])
                
                writer.writerow([])  # Empty row
                
                # Betting summary
                total_edge = sum(bet['edge'] for bet in daily_report['best_bets'])
                avg_confidence = np.mean([bet['confidence'] for bet in daily_report['best_bets']])
                total_stake = sum(bet['kelly_fraction'] for bet in daily_report['best_bets'])
                
                writer.writerow(['Summary Metric', 'Value'])
                writer.writerow(['Total Portfolio Edge', f"{total_edge*100:.1f}%"])
                writer.writerow(['Average Confidence', f"{avg_confidence*100:.1f}%"])
                writer.writerow(['Total Bankroll Risk', f"{total_stake*100:.1f}%"])
                writer.writerow([])  # Empty row
                
                # Market breakdown
                markets = {}
                for bet in daily_report['best_bets']:
                    market_cat = self.classify_market_category(bet['market'])
                    markets[market_cat] = markets.get(market_cat, 0) + 1
                
                writer.writerow(['Market Category', 'Number of Bets'])
                for market, count in markets.items():
                    writer.writerow([market, f"{count} bet{'s' if count > 1 else ''}"])
            
            else:
                writer.writerow(['No high-quality betting opportunities found today'])
                writer.writerow(['Recommendation: Wait for better value opportunities'])
        
        print(f"📊 CSV report saved: daily_report_{date_str}.csv")
    
    def get_bet_description(self, market):
        """Get human-readable bet description"""
        descriptions = {
            'Home': 'Home Team Win',
            'Draw': 'Match Draw', 
            'Away': 'Away Team Win',
            'Over 1.5': 'Over 1.5 Goals',
            'Under 1.5': 'Under 1.5 Goals',
            'Over 2.5': 'Over 2.5 Goals',
            'Under 2.5': 'Under 2.5 Goals',
            'Over 3.5': 'Over 3.5 Goals',
            'Under 3.5': 'Under 3.5 Goals',
            'BTTS Yes': 'Both Teams to Score - Yes',
            'BTTS No': 'Both Teams to Score - No',
            'Over 9.5 Corners': 'Over 9.5 Total Corners',
            'Under 9.5 Corners': 'Under 9.5 Total Corners',
            'Over 11.5 Corners': 'Over 11.5 Total Corners',
            'Under 11.5 Corners': 'Under 11.5 Total Corners',
            'Home/Draw': 'Home Win or Draw',
            'Home/Away': 'Home Win or Away Win (No Draw)',
            'Draw/Away': 'Draw or Away Win',
            'Home Over 1.5': 'Home Team Over 1.5 Goals',
            'Home Under 1.5': 'Home Team Under 1.5 Goals',
            'Away Over 1.5': 'Away Team Over 1.5 Goals',
            'Away Under 1.5': 'Away Team Under 1.5 Goals',
            'Home +1': 'Home Team +1 Handicap',
            'Away +1': 'Away Team +1 Handicap'
        }
        return descriptions.get(market, market)
    
    def get_risk_level(self, odds):
        """Classify risk level"""
        if odds <= 1.8:
            return 'Low Risk'
        elif odds <= 3.0:
            return 'Medium Risk'
        else:
            return 'High Risk'
    
    def classify_market_category(self, market):
        """Classify market category"""
        if market in ['Home', 'Draw', 'Away']:
            return 'Match Result'
        elif 'Over' in market or 'Under' in market:
            if 'Corner' in market:
                return 'Corners'
            else:
                return 'Goals'
        elif 'BTTS' in market:
            return 'Both Teams to Score'
        elif '/' in market:
            return 'Double Chance'
        else:
            return 'Special'


def main():
    """Generate today's daily betting report"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    generator = DailyBettingReportGenerator(API_KEY)
    
    print("🎯 Starting Daily Betting Report Generation...")
    
    daily_report = generator.generate_daily_report()
    
    if daily_report:
        print(f"\n✅ Daily Report Generated Successfully!")
        print(f"📊 {daily_report['recommended_bets']} high-quality bets recommended for today")
        print(f"📁 Files created:")
        date_str = datetime.now().strftime("%Y%m%d")
        print(f"   • daily_picks_{date_str}.csv")
        print(f"   • daily_report_{date_str}.txt")
        
        # Update cumulative tracker
        print(f"\n📈 Updating cumulative picks tracker...")
        generator.cumulative_tracker.update_tracker_for_date(date_str)
        
    else:
        print("❌ No report generated")


if __name__ == "__main__":
    main()