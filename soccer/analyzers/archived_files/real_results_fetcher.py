#!/usr/bin/env python3
"""
Real Results Fetcher

Fetches actual match results from API-Sports instead of using simulated data
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import time

class RealResultsFetcher:
    """Fetch real match results from API-Sports"""
    
    def __init__(self, api_key: str = "960c628e1c91c4b1f125e1eec52ad862"):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {'x-apisports-key': api_key}
        
    def search_fixture_by_teams(self, home_team: str, away_team: str, match_date: str) -> Optional[Dict]:
        """Search for a specific fixture by team names and date"""
        
        print(f"🔍 Searching API-Sports for: {home_team} vs {away_team} on {match_date}")
        
        try:
            # First, try to get fixtures for the specific date
            url = f"{self.base_url}/fixtures"
            params = {
                'date': match_date,
                'timezone': 'UTC'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ API error: {response.status_code}")
                return None
            
            data = response.json()
            fixtures = data.get('response', [])
            
            print(f"📊 Found {len(fixtures)} fixtures on {match_date}")
            
            # Search for matching teams
            for fixture in fixtures:
                fixture_teams = fixture.get('teams', {})
                home = fixture_teams.get('home', {}).get('name', '').lower()
                away = fixture_teams.get('away', {}).get('name', '').lower()
                
                # Check for team name matches (flexible matching)
                home_match = self.team_name_match(home_team.lower(), home)
                away_match = self.team_name_match(away_team.lower(), away)
                
                if home_match and away_match:
                    print(f"✅ Found match: {fixture_teams.get('home', {}).get('name')} vs {fixture_teams.get('away', {}).get('name')}")
                    return fixture
            
            print(f"❌ No match found for {home_team} vs {away_team}")
            return None
            
        except Exception as e:
            print(f"❌ Error searching fixture: {e}")
            return None
    
    def team_name_match(self, search_name: str, api_name: str) -> bool:
        """Check if team names match (flexible matching)"""
        
        # Direct match
        if search_name in api_name or api_name in search_name:
            return True
        
        # Common team name variations
        search_parts = search_name.split()
        api_parts = api_name.split()
        
        # Check if any significant word matches
        for search_part in search_parts:
            if len(search_part) > 3:  # Skip short words like "FC", "vs"
                for api_part in api_parts:
                    if search_part in api_part or api_part in search_part:
                        return True
        
        return False
    
    def get_match_result(self, home_team: str, away_team: str, match_date: str) -> Optional[Dict]:
        """Get actual match result from API-Sports"""
        
        fixture = self.search_fixture_by_teams(home_team, away_team, match_date)
        
        if not fixture:
            return None
        
        # Extract match result data
        fixture_info = fixture.get('fixture', {})
        teams = fixture.get('teams', {})
        goals = fixture.get('goals', {})
        score = fixture.get('score', {})
        statistics = fixture.get('statistics', [])
        
        status = fixture_info.get('status', {}).get('short', 'NS')
        
        # Only return results for finished matches
        if status not in ['FT', 'AET', 'PEN']:
            print(f"⏳ Match not finished yet (Status: {status})")
            return {
                'status': status,
                'finished': False,
                'home_team': teams.get('home', {}).get('name'),
                'away_team': teams.get('away', {}).get('name')
            }
        
        home_score = goals.get('home', 0) or 0
        away_score = goals.get('away', 0) or 0
        
        # Try to get corner statistics
        home_corners = 0
        away_corners = 0
        
        if statistics:
            for team_stats in statistics:
                team_id = team_stats.get('team', {}).get('id')
                stats = team_stats.get('statistics', [])
                
                for stat in stats:
                    if stat.get('type') == 'Corner Kicks':
                        corners = stat.get('value') or 0
                        try:
                            corners = int(corners)
                            if team_id == teams.get('home', {}).get('id'):
                                home_corners = corners
                            elif team_id == teams.get('away', {}).get('id'):
                                away_corners = corners
                        except:
                            pass
        
        total_corners = home_corners + away_corners
        total_goals = home_score + away_score
        btts = home_score > 0 and away_score > 0
        
        result = {
            'status': status,
            'finished': True,
            'home_team': teams.get('home', {}).get('name'),
            'away_team': teams.get('away', {}).get('name'),
            'home_score': home_score,
            'away_score': away_score,
            'total_goals': total_goals,
            'home_corners': home_corners,
            'away_corners': away_corners,
            'total_corners': total_corners,
            'btts': btts,
            'fixture_date': fixture_info.get('date'),
            'league': fixture.get('league', {}).get('name'),
            'match_status': 'Completed'
        }
        
        print(f"✅ Real result: {result['home_team']} {home_score}-{away_score} {result['away_team']}")
        print(f"   📊 {total_goals} goals, {total_corners} corners, BTTS: {btts}")
        
        return result
    
    def update_tracker_with_real_results(self, tracker_file: str) -> int:
        """Update cumulative tracker with real match results"""
        
        import pandas as pd
        
        print("🔄 Updating tracker with real match results...")
        
        df = pd.read_csv(tracker_file)
        updates_made = 0
        
        # Process each match that currently has simulated results
        for index, row in df.iterrows():
            # Skip if already verified as real result
            if row.get('verified_result') == True:
                continue
            
            match_date = row['date']
            home_team = row['home_team']
            away_team = row['away_team']
            
            print(f"\n📅 Checking: {home_team} vs {away_team} ({match_date})")
            
            # Get real result
            real_result = self.get_match_result(home_team, away_team, match_date)
            
            if real_result and real_result['finished']:
                # Update with real result
                df.loc[index, 'home_score'] = real_result['home_score']
                df.loc[index, 'away_score'] = real_result['away_score']
                df.loc[index, 'total_goals'] = real_result['total_goals']
                df.loc[index, 'total_corners'] = real_result['total_corners']
                df.loc[index, 'btts'] = real_result['btts']
                df.loc[index, 'verified_result'] = True
                
                # Re-evaluate bet outcome based on real result
                bet_outcome = self.evaluate_bet_outcome(row['bet_description'], real_result)
                old_outcome = row['bet_outcome']
                
                if bet_outcome != old_outcome:
                    print(f"   🔄 Bet outcome changed: {old_outcome} → {bet_outcome}")
                    df.loc[index, 'bet_outcome'] = bet_outcome
                    
                    # Recalculate P&L
                    odds = row['odds']
                    if bet_outcome == 'Win':
                        new_pnl = (odds - 1) * 25.0
                    else:
                        new_pnl = -25.0
                    
                    df.loc[index, 'actual_pnl'] = new_pnl
                    print(f"   💰 P&L updated: ${row['actual_pnl']:.2f} → ${new_pnl:.2f}")
                
                updates_made += 1
                
            elif real_result and not real_result['finished']:
                print(f"   ⏳ Match not finished yet")
                df.loc[index, 'match_status'] = f"Scheduled ({real_result['status']})"
            else:
                print(f"   ❌ Could not find match result")
            
            # Rate limiting
            time.sleep(1)
        
        # Recalculate running totals if any updates were made
        if updates_made > 0:
            print(f"\n🔄 Recalculating running totals for {updates_made} updated matches...")
            self.recalculate_running_totals(df)
            
            # Save updated tracker
            df.to_csv(tracker_file, index=False)
            print(f"💾 Tracker updated with {updates_made} real results")
            
            # Show updated statistics
            self.show_tracker_statistics(df)
        
        return updates_made
    
    def evaluate_bet_outcome(self, bet_description: str, match_data: Dict) -> str:
        """Evaluate bet outcome based on real match data"""
        
        bet_lower = bet_description.lower()
        home_score = match_data['home_score']
        away_score = match_data['away_score']
        total_goals = match_data['total_goals']
        total_corners = match_data['total_corners']
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
        elif 'over 11.5' in bet_lower and 'corners' in bet_lower:
            return 'Win' if total_corners > 11.5 else 'Loss'
        elif 'under 11.5' in bet_lower and 'corners' in bet_lower:
            return 'Win' if total_corners < 11.5 else 'Loss'
        
        # Team goal markets
        elif 'home under 1.5' in bet_lower:
            return 'Win' if home_score < 1.5 else 'Loss'
        elif 'away under 1.5' in bet_lower:
            return 'Win' if away_score < 1.5 else 'Loss'
        elif 'home/away' in bet_lower:
            return 'Win' if home_score != away_score else 'Loss'
        elif 'draw/away' in bet_lower:
            return 'Win' if home_score <= away_score else 'Loss'
        elif 'home/draw' in bet_lower:
            return 'Win' if home_score >= away_score else 'Loss'
        
        # Default: return current outcome
        return 'Loss'
    
    def recalculate_running_totals(self, df):
        """Recalculate running totals and win rates"""
        
        running_total = 0
        for i in range(len(df)):
            running_total += df.loc[i, 'actual_pnl']
            df.loc[i, 'running_total'] = running_total
            
            # Calculate win rate
            wins_so_far = len(df[:i+1][df[:i+1]['bet_outcome'] == 'Win'])
            total_picks = i + 1
            win_rate = (wins_so_far / total_picks) * 100
            df.loc[i, 'win_rate'] = win_rate
    
    def show_tracker_statistics(self, df):
        """Show updated tracker statistics"""
        
        total_picks = len(df)
        total_wins = len(df[df['bet_outcome'] == 'Win'])
        total_losses = len(df[df['bet_outcome'] == 'Loss'])
        final_total = df.iloc[-1]['running_total']
        final_win_rate = df.iloc[-1]['win_rate']
        
        print(f"\n📊 Updated Tracker Statistics:")
        print(f"   🎯 Total Picks: {total_picks}")
        print(f"   ✅ Wins: {total_wins}")
        print(f"   ❌ Losses: {total_losses}")
        print(f"   💰 Final P&L: ${final_total:+.2f}")
        print(f"   📈 Win Rate: {final_win_rate:.1f}%")

def main():
    """Update tracker with real results"""
    
    tracker_file = "./soccer/output reports/cumulative_picks_tracker.csv"
    
    fetcher = RealResultsFetcher()
    updates_made = fetcher.update_tracker_with_real_results(tracker_file)
    
    print(f"\n✅ Update complete! {updates_made} matches updated with real results.")

if __name__ == "__main__":
    main()