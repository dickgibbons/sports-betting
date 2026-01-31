#!/usr/bin/env python3
"""
Consolidated Daily Selections CSV Generator
Creates/updates a single CSV file with all selections from every sport
Updates with results from previous day and adds new selections
"""

import os
import re
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests


PROJECT_DIR = "/Users/dickgibbons/sports-betting"
REPORTS_DIR = f"{PROJECT_DIR}/reports"
DAILY_REPORTS = "/Users/dickgibbons/Daily Reports"
CONSOLIDATED_CSV = f"{PROJECT_DIR}/daily_selections_consolidated.csv"


class ConsolidatedSelectionsTracker:
    """Track all selections across all sports in one CSV"""

    def __init__(self):
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.columns = [
            'Date', 'Sport', 'League', 'Home_Team', 'Away_Team', 
            'Selection', 'Bet_Type', 'Odds', 'Confidence', 'Status', 
            'Result', 'Score', 'Profit', 'Notes'
        ]

    def load_existing_csv(self) -> pd.DataFrame:
        """Load existing consolidated CSV if it exists"""
        if os.path.exists(CONSOLIDATED_CSV):
            try:
                df = pd.read_csv(CONSOLIDATED_CSV)
                # Ensure all columns exist
                for col in self.columns:
                    if col not in df.columns:
                        df[col] = ''
                return df
            except Exception as e:
                print(f"⚠️  Error loading existing CSV: {e}")
                return pd.DataFrame(columns=self.columns)
        return pd.DataFrame(columns=self.columns)

    def parse_nhl_ml_totals(self, date_str: str) -> List[Dict]:
        """Parse NHL ML totals report"""
        selections = []
        file_path = f"{REPORTS_DIR}/{date_str}/nhl_ml_totals_{date_str}.txt"
        
        if not os.path.exists(file_path):
            return selections

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse game sections
            game_pattern = r'GAME #\d+: (.+?)\n(.*?)(?=GAME #\d+:|$)'
            games = re.findall(game_pattern, content, re.DOTALL)

            for game_match, game_content in games:
                # Extract teams (e.g., "Sharks @ Red Wings")
                if ' @ ' in game_match:
                    away, home = game_match.split(' @ ')
                else:
                    continue

                # Parse ML predicted total
                ml_match = re.search(r'ML Predicted Total:\s*([\d.]+)', game_content)
                if ml_match:
                    predicted_total = float(ml_match.group(1))
                    selections.append({
                        'Date': date_str,
                        'Sport': 'NHL',
                        'League': 'NHL',
                        'Home_Team': home.strip(),
                        'Away_Team': away.strip(),
                        'Selection': f'Over {predicted_total:.2f}',
                        'Bet_Type': 'OVER',
                        'Odds': '',
                        'Confidence': '',
                        'Status': 'PENDING',
                        'Result': '',
                        'Score': '',
                        'Profit': '',
                        'Notes': 'ML Predicted Total'
                    })

                # Parse first period probabilities
                # Team over 0.5
                for team_name in [home, away]:
                    prob_match = re.search(
                        rf'{re.escape(team_name.strip())}\s+over 0\.5 goals: ([\d.]+)%',
                        game_content
                    )
                    if prob_match and float(prob_match.group(1)) >= 55:
                        selections.append({
                            'Date': date_str,
                            'Sport': 'NHL',
                            'League': 'NHL',
                            'Home_Team': home.strip(),
                            'Away_Team': away.strip(),
                            'Selection': f'{team_name.strip()} Over 0.5 (1P)',
                            'Bet_Type': '1P Team Over',
                            'Odds': '',
                            'Confidence': prob_match.group(1) + '%',
                            'Status': 'PENDING',
                            'Result': '',
                            'Score': '',
                            'Profit': '',
                            'Notes': 'First Period Team Over 0.5'
                        })

                # 1P Total Over 1.5
                prob_match = re.search(
                    r'1st Period Total over 1\.5 goals: ([\d.]+)%',
                    game_content
                )
                if prob_match and float(prob_match.group(1)) >= 55:
                    selections.append({
                        'Date': date_str,
                        'Sport': 'NHL',
                        'League': 'NHL',
                        'Home_Team': home.strip(),
                        'Away_Team': away.strip(),
                        'Selection': '1P Total Over 1.5',
                        'Bet_Type': '1P Total Over',
                        'Odds': '',
                        'Confidence': prob_match.group(1) + '%',
                        'Status': 'PENDING',
                        'Result': '',
                        'Score': '',
                        'Profit': '',
                        'Notes': 'First Period Total Over 1.5'
                    })

        except Exception as e:
            print(f"⚠️  Error parsing NHL ML totals: {e}")

        return selections

    def parse_nhl_top5_picks(self, date_str: str) -> List[Dict]:
        """Parse NHL top 5 picks report"""
        selections = []
        file_path = f"{REPORTS_DIR}/{date_str}/nhl_top5_picks_{date_str}.txt"
        
        if not os.path.exists(file_path):
            return selections

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Pattern: RANK #1, GAME: Away @ Home, BET: selection, etc.
            pick_pattern = r'RANK #(\d+).*?GAME:\s*(.+?)\n.*?BET:\s*(.+?)\n.*?EDGE:\s*([\d.]+)%'
            picks = re.findall(pick_pattern, content, re.DOTALL)

            for rank, game, bet, edge in picks:
                if ' @ ' in game:
                    away, home = game.split(' @ ')
                else:
                    continue

                # Determine bet type
                bet_type = 'ML'
                if 'Over' in bet:
                    bet_type = 'OVER'
                elif 'Under' in bet:
                    bet_type = 'UNDER'
                elif '1P' in bet or '1st Period' in bet:
                    bet_type = '1P Total Over' if 'Over' in bet else '1P Total Under'

                selections.append({
                    'Date': date_str,
                    'Sport': 'NHL',
                    'League': 'NHL',
                    'Home_Team': home.strip(),
                    'Away_Team': away.strip(),
                    'Selection': bet.strip(),
                    'Bet_Type': bet_type,
                    'Odds': '',
                    'Confidence': f'{edge}%',
                    'Status': 'PENDING',
                    'Result': '',
                    'Score': '',
                    'Profit': '',
                    'Notes': f'Top 5 Pick #{rank}'
                })

        except Exception as e:
            print(f"⚠️  Error parsing NHL top 5 picks: {e}")

        return selections

    def parse_nhl_1p_analysis_json(self, date_str: str) -> List[Dict]:
        """Parse NHL 1P analysis JSON for selections"""
        selections = []
        file_path = f"{REPORTS_DIR}/{date_str}/nhl_1p_analysis_{date_str}.json"
        
        if not os.path.exists(file_path):
            return selections

        # This JSON has team stats, not direct picks
        # We'll use this for context but not extract direct selections
        # The actual picks are in the text reports
        return selections

    def parse_soccer_profitable_angles(self, date_str: str) -> List[Dict]:
        """Parse soccer profitable angles report"""
        selections = []
        file_path = f"{REPORTS_DIR}/{date_str}/soccer_profitable_angles_{date_str}.txt"
        
        if not os.path.exists(file_path):
            return selections

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check if no games found
            if 'No fixtures found' in content:
                return selections

            # Parse game sections - pattern varies, try multiple
            # Pattern 1: League/Game format
            game_pattern = r'([A-Z][a-z\s]+?)\s+-\s+(.+?)\s+vs\s+(.+?)\n.*?BET:\s*(.+?)\n.*?CONFIDENCE:\s*([\d.]+)%'
            matches = re.findall(game_pattern, content, re.MULTILINE)

            for league, home, away, bet, confidence in matches:
                # Determine bet type
                bet_type = 'OVER'
                if 'Over 2.5' in bet or 'Over 3.5' in bet:
                    bet_type = 'OVER'
                elif 'Under' in bet:
                    bet_type = 'UNDER'
                elif 'BTTS' in bet:
                    bet_type = 'BTTS'
                elif '1H Over' in bet or '1H Under' in bet:
                    bet_type = '1H Total'

                selections.append({
                    'Date': date_str,
                    'Sport': 'Soccer',
                    'League': league.strip(),
                    'Home_Team': home.strip(),
                    'Away_Team': away.strip(),
                    'Selection': bet.strip(),
                    'Bet_Type': bet_type,
                    'Odds': '',
                    'Confidence': f'{confidence}%',
                    'Status': 'PENDING',
                    'Result': '',
                    'Score': '',
                    'Profit': '',
                    'Notes': 'Profitable Angles Analysis'
                })

            # Pattern 2: League section format (e.g., "📊 SERIE A")
            if not matches:
                lines = content.split('\n')
                current_league = ''
                i = 0
                
                while i < len(lines):
                    line = lines[i]
                    
                    # Detect league header (e.g., "📊 SERIE A" or "📊 BUNDESLIGA")
                    league_match = re.search(r'📊\s*([A-Z\s]+)', line)
                    if league_match:
                        current_league = league_match.group(1).strip()
                    
                    # Detect match line (e.g., "⚽ AS Roma vs Genoa")
                    match_match = re.search(r'⚽\s*(.+?)\s+vs\s+(.+?)$', line)
                    if match_match:
                        home = match_match.group(1).strip()
                        away = match_match.group(2).strip()
                        
                        # Look ahead for RECOMMEND markers (lines with "---" indicate not recommended)
                        # Look for lines with actual recommendations
                        j = i + 1
                        while j < len(lines) and j < i + 10:
                            bet_line = lines[j]
                            
                            # Skip header lines
                            if 'BET TYPE' in bet_line or '---' in bet_line:
                                j += 1
                                continue
                            
                            # Look for recommended bets (not marked with "---")
                            # Format: "Over 2.5 Goals    |  51.2%     | +4.8%          |    ---"
                            # If last column is "---", skip it
                            if '|' in bet_line and '---' not in bet_line:
                                parts = [p.strip() for p in bet_line.split('|')]
                                if len(parts) >= 3:
                                    bet_name = parts[0].strip()
                                    confidence_str = parts[1].strip()
                                    roi_str = parts[2].strip() if len(parts) > 2 else ''
                                    
                                    # Extract confidence percentage
                                    conf_match = re.search(r'([\d.]+)%', confidence_str)
                                    if conf_match:
                                        confidence = conf_match.group(1)
                                        
                                        # Only include if ROI > 5% (positive recommendation)
                                        roi_match = re.search(r'\+?([\d.]+)%', roi_str)
                                        if roi_match and float(roi_match.group(1)) >= 5:
                                            # Determine bet type
                                            bet_type = 'OVER'
                                            if 'Over 2.5' in bet_name or 'Over 3.5' in bet_name:
                                                bet_type = 'OVER'
                                            elif 'Under' in bet_name:
                                                bet_type = 'UNDER'
                                            elif 'BTTS' in bet_name:
                                                bet_type = 'BTTS'
                                            elif '1H Over' in bet_name or '1H Under' in bet_name:
                                                bet_type = '1H Total'
                                            
                                            selections.append({
                                                'Date': date_str,
                                                'Sport': 'Soccer',
                                                'League': current_league or 'Unknown',
                                                'Home_Team': home,
                                                'Away_Team': away,
                                                'Selection': bet_name,
                                                'Bet_Type': bet_type,
                                                'Odds': '',
                                                'Confidence': f'{confidence}%',
                                                'Status': 'PENDING',
                                                'Result': '',
                                                'Score': '',
                                                'Profit': '',
                                                'Notes': f'Profitable Angles (ROI: {roi_str})'
                                            })
                            j += 1
                        
                        # Move past this match block
                        while i < len(lines) and not (lines[i].startswith('⚽') and i > 0):
                            i += 1
                        continue
                    
                    i += 1

        except Exception as e:
            print(f"⚠️  Error parsing soccer profitable angles: {e}")

        return selections

    def fetch_nhl_result(self, date_str: str, home_team: str, away_team: str) -> Optional[Dict]:
        """Fetch NHL game result"""
        try:
            url = f"https://api-web.nhle.com/v1/schedule/{date_str}"
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                return None

            data = response.json()
            for day in data.get("gameWeek", []):
                if day.get("date") == date_str:
                    for game in day.get("games", []):
                        game_home = game.get("homeTeam", {}).get("abbrev", "")
                        game_away = game.get("awayTeam", {}).get("abbrev", "")
                        
                        if (game_home.lower() == home_team.lower() and 
                            game_away.lower() == away_team.lower()):
                            status = game.get("gameState", "")
                            if status == "OFF":
                                home_score = game.get("homeTeam", {}).get("score", 0)
                                away_score = game.get("awayTeam", {}).get("score", 0)
                                
                                # Get period scores for 1P bets
                                periods = game.get("periodDescriptor", {}).get("number", 0)
                                
                                return {
                                    'home_score': home_score,
                                    'away_score': away_score,
                                    'completed': True,
                                    'total': home_score + away_score
                                }
        except Exception as e:
            print(f"⚠️  Error fetching NHL result: {e}")

        return None

    def update_results_for_date(self, df: pd.DataFrame, date_str: str) -> pd.DataFrame:
        """Update results for a specific date's selections"""
        updated_count = 0
        
        # Get pending selections for this date
        pending = df[(df['Date'] == date_str) & (df['Status'] == 'PENDING')]
        
        for idx, row in pending.iterrows():
            sport = row['Sport']
            home = row['Home_Team']
            away = row['Away_Team']
            selection = row['Selection']
            bet_type = row['Bet_Type']

            result = None
            if sport == 'NHL':
                result = self.fetch_nhl_result(date_str, home, away)
            elif sport == 'Soccer':
                # Soccer results fetching would go here
                # For now, skip
                continue

            if result and result.get('completed'):
                # Determine if bet won
                won = False
                if bet_type == 'OVER':
                    line_match = re.search(r'Over ([\d.]+)', selection)
                    if line_match:
                        line = float(line_match.group(1))
                        won = result['total'] > line
                elif bet_type == 'UNDER':
                    line_match = re.search(r'Under ([\d.]+)', selection)
                    if line_match:
                        line = float(line_match.group(1))
                        won = result['total'] < line
                elif bet_type in ['1P Team Over', '1P Total Over']:
                    # Would need period scores - simplified for now
                    pass

                # Update row
                df.at[idx, 'Status'] = 'WON' if won else 'LOST'
                df.at[idx, 'Result'] = 'WON' if won else 'LOST'
                df.at[idx, 'Score'] = f"{away} {result['away_score']} @ {home} {result['home_score']}"
                
                updated_count += 1

        if updated_count > 0:
            print(f"   ✅ Updated {updated_count} results for {date_str}")

        return df

    def generate_consolidated_csv(self):
        """Generate consolidated CSV with all selections"""
        print("\n" + "=" * 80)
        print("📊 CONSOLIDATED DAILY SELECTIONS CSV GENERATOR")
        print("=" * 80)

        # Load existing CSV
        print(f"\n📁 Loading existing selections...")
        df = self.load_existing_csv()
        existing_count = len(df)
        print(f"   Found {existing_count} existing selections")

        # Update yesterday's results
        print(f"\n🔄 Updating results for {self.yesterday}...")
        df = self.update_results_for_date(df, self.yesterday)

        # Parse today's selections
        print(f"\n📋 Parsing selections for {self.today}...")
        all_selections = []

        # NHL selections
        print("   🏒 Parsing NHL reports...")
        nhl_selections = []
        nhl_selections.extend(self.parse_nhl_ml_totals(self.today))
        nhl_selections.extend(self.parse_nhl_top5_picks(self.today))
        print(f"      Found {len(nhl_selections)} NHL selections")

        # Soccer selections
        print("   ⚽ Parsing Soccer reports...")
        soccer_selections = self.parse_soccer_profitable_angles(self.today)
        print(f"      Found {len(soccer_selections)} Soccer selections")

        all_selections = nhl_selections + soccer_selections

        # Remove duplicates (same date, sport, teams, selection)
        print(f"\n🔍 Processing {len(all_selections)} new selections...")
        
        if not df.empty:
            # Create unique key for deduplication
            df['_key'] = df['Date'].astype(str) + '|' + df['Sport'] + '|' + df['Home_Team'] + '|' + df['Away_Team'] + '|' + df['Selection']
            
            for sel in all_selections:
                key = f"{sel['Date']}|{sel['Sport']}|{sel['Home_Team']}|{sel['Away_Team']}|{sel['Selection']}"
                
                # Check if already exists
                if key not in df['_key'].values:
                    df = pd.concat([df, pd.DataFrame([sel])], ignore_index=True)
            
            df = df.drop('_key', axis=1)
        else:
            df = pd.DataFrame(all_selections)

        # Ensure proper column order
        for col in self.columns:
            if col not in df.columns:
                df[col] = ''

        df = df[self.columns]

        # Save CSV
        print(f"\n💾 Saving consolidated CSV...")
        df.to_csv(CONSOLIDATED_CSV, index=False)
        new_count = len(df)
        added = new_count - existing_count

        print(f"   ✅ Saved {new_count} total selections ({added} new)")
        print(f"   📁 File: {CONSOLIDATED_CSV}")

        return df


def main():
    """Main entry point"""
    tracker = ConsolidatedSelectionsTracker()
    df = tracker.generate_consolidated_csv()
    
    print("\n" + "=" * 80)
    print("✅ CONSOLIDATED CSV GENERATION COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
