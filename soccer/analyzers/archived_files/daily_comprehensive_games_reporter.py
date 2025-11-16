#!/usr/bin/env python3
"""
Daily Comprehensive Games Reporter
Generates daily report showing ALL games for leagues we follow and which ones have betting picks
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import csv
from multi_market_predictor import MultiMarketPredictor
# Removed enhanced fixture generator - now using real API data

class DailyComprehensiveGamesReporter:
    """Generate comprehensive daily games report with pick indicators"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.football_api_base_url = "https://api.football-data-api.com"
        self.predictor = MultiMarketPredictor(api_key)
        # Using real API data integration instead of enhanced fixture generator
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.day_name = datetime.now().strftime('%A')
        
        # Leagues we actively follow
        self.followed_leagues = {
            'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
            'UEFA Champions League', 'UEFA Europa League', 'UEFA Conference League',
            'Championship', 'Serie B', '2. Bundesliga', 'Ligue 2',
            'Eredivisie', 'Primeira Liga', 'Belgian Pro League', 'Scottish Premiership',
            'Brazilian Serie A', 'Brazilian Serie B', 'Argentine Primera División', 'Copa Libertadores',
            'MLS', 'Liga MX',
            'J1 League', 'K League 1', 'Chinese Super League',
            'UEFA Nations League', 'WC Qualification Europe', 'WC Qualification Africa',
            'WC Qualification Asia', 'WC Qualification South America', 'WC Qualification CONCACAF',
            'UEFA Euro Qualifiers', 'Allsvenskan', 'Eliteserien', 'Canadian Premier League'
        }
    
    def fetch_all_todays_fixtures(self):
        """Fetch all fixtures for today using real API data"""
        print(f"📅 Fetching comprehensive fixtures for {self.day_name}, {self.today}...")
        
        # Use real API data integration instead of generated fixtures
        from real_data_integration import RealDataIntegration
        
        try:
            print("🔌 Using Real Data Integration for comprehensive coverage")
            integrator = RealDataIntegration()
            
            # Get all real fixtures (not filtered by followed leagues)
            real_fixtures = integrator.get_real_fixtures_with_odds(self.today)
            
            print(f"✅ Found {len(real_fixtures)} real fixtures from APIs")
            return real_fixtures
            
        except Exception as e:
            print(f"❌ Error fetching real fixtures: {e}")
            print("⚠️ No fixtures available for comprehensive report")
            return []
    
    def format_league_name(self, api_league_name):
        """Format league name from API to our standard format"""
        if not api_league_name:
            return 'Unknown League'
            
        api_name_lower = api_league_name.lower()
        
        # League name mappings
        league_mappings = {
            'premier league': 'Premier League',
            'la liga': 'La Liga',
            'serie a': 'Serie A',
            'bundesliga': 'Bundesliga',
            'ligue 1': 'Ligue 1',
            'champions league': 'UEFA Champions League',
            'europa league': 'UEFA Europa League',
            'conference league': 'UEFA Conference League',
            'championship': 'Championship',
            'serie b': 'Serie B',
            'eredivisie': 'Eredivisie',
            'primeira liga': 'Primeira Liga',
            'brazilian serie a': 'Brazilian Serie A',
            'brasileirao': 'Brazilian Serie A',
            'mls': 'MLS',
            'j1 league': 'J1 League'
        }
        
        for key, value in league_mappings.items():
            if key in api_name_lower:
                return value
        
        return api_league_name
    
    def is_followed_league(self, league_name, country=None):
        """Check if we actively follow this league - strict matching with country verification"""
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
    
    def analyze_match_for_picks(self, match):
        """Analyze a single match to determine if we have betting picks"""
        try:
            # Generate comprehensive odds for this match
            odds = self.predictor.generate_realistic_odds()
            
            # Override with actual odds if available
            if 'odds_home' in match:
                odds.update({
                    'home_ml': match.get('odds_home', 2.0),
                    'draw_ml': match.get('odds_draw', 3.2),
                    'away_ml': match.get('odds_away', 3.5)
                })
            
            # Analyze all markets for this match
            opportunities = self.predictor.analyze_all_markets(odds)
            
            # Filter for quality opportunities
            quality_bets = []
            for opp in opportunities:
                if (opp['edge'] > 0.08 and           # 8%+ edge
                    opp['confidence'] > 0.65 and     # 65%+ confidence  
                    opp['odds'] <= 6.0 and          # Reasonable odds
                    opp['kelly_fraction'] > 0.02):   # Meaningful stake
                    
                    quality_bets.append({
                        'market': opp['market'],
                        'odds': opp['odds'],
                        'edge': opp['edge'],
                        'confidence': opp['confidence']
                    })
            
            return quality_bets
            
        except Exception as e:
            print(f"⚠️ Error analyzing match: {e}")
            return []
    
    def generate_comprehensive_daily_report(self):
        """Generate comprehensive daily games report"""
        
        print(f"📊 GENERATING COMPREHENSIVE DAILY GAMES REPORT")
        print("=" * 60)
        print(f"📅 Date: {self.day_name}, {self.today}")
        
        # Fetch all fixtures
        all_fixtures = self.fetch_all_todays_fixtures()
        
        if not all_fixtures:
            print("❌ No fixtures found for today")
            return None
        
        # Process all fixtures
        processed_games = []
        followed_games = []
        games_with_picks = []
        
        print(f"🔍 Processing {len(all_fixtures)} fixtures...")
        
        for fixture in all_fixtures:
            try:
                # Extract basic match info - handle enhanced fixture format
                league_name = fixture.get('league', 'Unknown League')
                country = fixture.get('country', 'Unknown')
                
                game_info = {
                    'kick_off': fixture.get('kick_off', '15:00'),
                    'home_team': fixture.get('home_team', 'Unknown'),
                    'away_team': fixture.get('away_team', 'Unknown'),
                    'league': league_name,
                    'country': country,
                    'home_odds': fixture.get('home_odds', 'N/A'),
                    'draw_odds': fixture.get('draw_odds', 'N/A'),
                    'away_odds': fixture.get('away_odds', 'N/A'),
                    'source': fixture.get('source', 'Unknown'),
                    'followed_league': self.is_followed_league(league_name, country),
                    'has_picks': False,
                    'pick_count': 0,
                    'best_picks': []
                }
                
                processed_games.append(game_info)
                
                # If we follow this league, check for betting opportunities
                if game_info['followed_league']:
                    followed_games.append(game_info)
                    
                    # Analyze for picks
                    picks = self.analyze_match_for_picks(fixture)
                    if picks:
                        game_info['has_picks'] = True
                        game_info['pick_count'] = len(picks)
                        game_info['best_picks'] = picks[:3]  # Top 3 picks
                        games_with_picks.append(game_info)
                
            except Exception as e:
                print(f"⚠️ Error processing fixture: {e}")
        
        # Generate comprehensive report
        report_data = {
            'date': self.today,
            'day_name': self.day_name,
            'total_games': len(processed_games),
            'followed_games': len(followed_games),
            'games_with_picks': len(games_with_picks),
            'all_games': processed_games,
            'followed_only': followed_games,
            'pick_games': games_with_picks
        }
        
        # Save comprehensive report
        self.save_comprehensive_report(report_data)
        
        return report_data
    
    def save_comprehensive_report(self, report_data):
        """Save comprehensive daily games report"""
        
        date_str = datetime.now().strftime("%Y%m%d")
        
        # Save detailed CSV with ALL games
        csv_filename = f"./soccer/output reports/daily_all_games_{date_str}.csv"
        
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = [
                'date', 'kick_off', 'home_team', 'away_team', 'league', 'country',
                'home_odds', 'draw_odds', 'away_odds', 'followed_league',
                'has_picks', 'pick_count', 'top_pick_markets'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for game in report_data['all_games']:
                # Format top pick markets
                top_markets = ', '.join([pick['market'] for pick in game['best_picks']]) if game['best_picks'] else 'None'
                
                row = {
                    'date': report_data['date'],
                    'kick_off': game['kick_off'],
                    'home_team': game['home_team'],
                    'away_team': game['away_team'],
                    'league': game['league'],
                    'country': game.get('country', 'Unknown'),
                    'home_odds': game['home_odds'],
                    'draw_odds': game['draw_odds'],
                    'away_odds': game['away_odds'],
                    'followed_league': 'Yes' if game['followed_league'] else 'No',
                    'has_picks': 'Yes' if game['has_picks'] else 'No',
                    'pick_count': game['pick_count'],
                    'top_pick_markets': top_markets
                }
                writer.writerow(row)
        
        print(f"💾 All games CSV saved: daily_all_games_{date_str}.csv")
        
        # Generate formatted report
        self.generate_formatted_comprehensive_report(report_data, date_str)
    
    def generate_formatted_comprehensive_report(self, report_data, date_str):
        """Generate human-readable comprehensive games report"""
        
        report_filename = f"./soccer/output reports/daily_games_overview_{date_str}.txt"
        
        with open(report_filename, 'w') as f:
            f.write("⚽ DAILY COMPREHENSIVE GAMES OVERVIEW ⚽\n")
            f.write("=" * 55 + "\n")
            f.write(f"📅 {report_data['day_name']}, {report_data['date']}\n")
            f.write(f"🌍 Total Games Worldwide: {report_data['total_games']}\n")
            f.write(f"👀 Games in Followed Leagues: {report_data['followed_games']}\n")
            f.write(f"🎯 Games with Betting Picks: {report_data['games_with_picks']}\n\n")
            
            # Summary statistics
            pick_rate = (report_data['games_with_picks'] / report_data['followed_games'] * 100) if report_data['followed_games'] > 0 else 0
            f.write("📊 SUMMARY STATISTICS:\n")
            f.write("-" * 25 + "\n")
            f.write(f"   Coverage Rate: {report_data['followed_games']}/{report_data['total_games']} games ({report_data['followed_games']/report_data['total_games']*100:.1f}%)\n")
            f.write(f"   Pick Generation Rate: {pick_rate:.1f}% of followed games\n")
            f.write(f"   Total Betting Opportunities: {sum(game['pick_count'] for game in report_data['pick_games'])}\n\n")
            
            # League breakdown
            league_stats = {}
            for game in report_data['all_games']:
                league = game['league']
                if league not in league_stats:
                    league_stats[league] = {'total': 0, 'followed': 0, 'with_picks': 0}
                
                league_stats[league]['total'] += 1
                if game['followed_league']:
                    league_stats[league]['followed'] += 1
                if game['has_picks']:
                    league_stats[league]['with_picks'] += 1
            
            f.write("🏆 LEAGUE BREAKDOWN:\n")
            f.write("-" * 20 + "\n")
            
            # Sort leagues by number of games with picks, then by total games
            sorted_leagues = sorted(league_stats.items(), 
                                  key=lambda x: (x[1]['with_picks'], x[1]['total']), 
                                  reverse=True)
            
            for league, stats in sorted_leagues:
                followed_indicator = "👀" if stats['followed'] > 0 else "⭕"
                picks_indicator = f"🎯{stats['with_picks']}" if stats['with_picks'] > 0 else "❌"
                
                f.write(f"   {followed_indicator} {league}: {stats['total']} games, {picks_indicator} picks\n")
            
            f.write(f"\n🎯 GAMES WITH BETTING PICKS:\n")
            f.write("=" * 35 + "\n\n")
            
            if report_data['pick_games']:
                # Group games with picks by league
                pick_games_by_league = {}
                for game in report_data['pick_games']:
                    league = game['league']
                    if league not in pick_games_by_league:
                        pick_games_by_league[league] = []
                    pick_games_by_league[league].append(game)
                
                for league, games in pick_games_by_league.items():
                    f.write(f"🏟️ {league}:\n")
                    for game in games:
                        f.write(f"   {game['kick_off']} | {game['home_team']} vs {game['away_team']}\n")
                        f.write(f"   💰 {game['pick_count']} betting opportunities\n")
                        if game['best_picks']:
                            top_picks = ', '.join([f"{pick['market']} ({pick['odds']:.2f})" for pick in game['best_picks']])
                            f.write(f"   🎲 Top picks: {top_picks}\n")
                        f.write("\n")
            else:
                f.write("   No betting opportunities found in followed leagues today.\n\n")
            
            f.write("👀 ALL GAMES IN FOLLOWED LEAGUES:\n")
            f.write("=" * 40 + "\n\n")
            
            if report_data['followed_only']:
                # Group all followed games by league
                followed_by_league = {}
                for game in report_data['followed_only']:
                    league = game['league']
                    if league not in followed_by_league:
                        followed_by_league[league] = []
                    followed_by_league[league].append(game)
                
                for league, games in followed_by_league.items():
                    f.write(f"🏟️ {league} ({len(games)} games):\n")
                    for game in games:
                        pick_indicator = "🎯" if game['has_picks'] else "⚪"
                        f.write(f"   {pick_indicator} {game['kick_off']} | {game['home_team']} vs {game['away_team']}")
                        if game['home_odds'] != 'N/A':
                            f.write(f" | Odds: {game['home_odds']}/{game['draw_odds']}/{game['away_odds']}")
                        f.write("\n")
                    f.write("\n")
            else:
                f.write("   No games found in followed leagues today.\n\n")
            
            f.write("🌍 OTHER LEAGUES (NOT FOLLOWED):\n")
            f.write("=" * 35 + "\n\n")
            
            # Show unfollowed leagues
            unfollowed_games = [game for game in report_data['all_games'] if not game['followed_league']]
            if unfollowed_games:
                unfollowed_by_league = {}
                for game in unfollowed_games:
                    league = game['league']
                    if league not in unfollowed_by_league:
                        unfollowed_by_league[league] = []
                    unfollowed_by_league[league].append(game)
                
                for league, games in unfollowed_by_league.items():
                    f.write(f"   {league}: {len(games)} game{'s' if len(games) > 1 else ''}\n")
            else:
                f.write("   No games in other leagues today.\n")
            
            f.write("\n📈 LEGEND:\n")
            f.write("👀 = League we actively follow\n")
            f.write("⭕ = League not in our follow list\n")
            f.write("🎯 = Game has betting picks\n")
            f.write("⚪ = Game analyzed but no quality picks found\n")
            f.write("❌ = No picks generated\n")
            
            f.write("\n⚠️ NOTES:\n")
            f.write("• Only followed leagues are analyzed for betting opportunities\n")
            f.write("• Pick generation requires minimum edge and confidence thresholds\n")
            f.write("• Unfollowed leagues are listed for completeness only\n")
            f.write("• Times shown in local timezone\n")
        
        print(f"📋 Comprehensive games report saved: daily_games_overview_{date_str}.txt")


def main():
    """Generate comprehensive daily games report"""
    
    API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"
    
    reporter = DailyComprehensiveGamesReporter(API_KEY)
    
    print("🌍 Starting Comprehensive Daily Games Report...")
    
    report_data = reporter.generate_comprehensive_daily_report()
    
    if report_data:
        print(f"\n✅ Comprehensive Games Report Generated Successfully!")
        print(f"🌍 {report_data['total_games']} total games worldwide")
        print(f"👀 {report_data['followed_games']} games in followed leagues") 
        print(f"🎯 {report_data['games_with_picks']} games with betting picks")
        
        date_str = datetime.now().strftime("%Y%m%d")
        print(f"📁 Files created:")
        print(f"   • daily_all_games_{date_str}.csv")
        print(f"   • daily_games_overview_{date_str}.txt")
    else:
        print("❌ Failed to generate comprehensive report")


if __name__ == "__main__":
    main()