#!/usr/bin/env python3
"""
Realistic Daily Fixtures Generator
Generates appropriate matches based on current day and season
"""

from datetime import datetime
import random

class RealisticFixturesGenerator:
    """Generate realistic fixtures based on current date and season"""
    
    def __init__(self):
        self.current_date = datetime.now()
        self.day_of_week = self.current_date.weekday()  # 0=Monday, 6=Sunday
        self.month = self.current_date.month
        
    def get_todays_matches(self):
        """Get realistic matches for today"""
        
        print(f"📅 Generating fixtures for {self.current_date.strftime('%A, %B %d, %Y')}")
        
        # Check if it's football season (August-May)
        if self.month in [8, 9, 10, 11, 12, 1, 2, 3, 4, 5]:
            return self.get_season_matches()
        else:
            print("⚠️ Off-season period - international and friendly matches only")
            return self.get_summer_matches()
    
    def get_season_matches(self):
        """Get matches appropriate for football season"""
        
        if self.day_of_week == 5:  # Saturday
            return self.get_saturday_matches()
        elif self.day_of_week == 6:  # Sunday  
            return self.get_sunday_matches()
        elif self.day_of_week == 1:  # Tuesday (Champions League)
            return self.get_tuesday_matches()
        elif self.day_of_week == 2:  # Wednesday (Champions/Europa League)
            return self.get_wednesday_matches()
        else:
            return self.get_weekday_matches()
    
    def get_saturday_matches(self):
        """Saturday fixtures - typical Premier League day"""
        return [
            {
                'kick_off': '12:30',
                'home_team': 'Arsenal',
                'away_team': 'Chelsea',
                'league': 'Premier League',
                'home_odds': 2.1,
                'draw_odds': 3.4,
                'away_odds': 3.2
            },
            {
                'kick_off': '15:00',
                'home_team': 'Manchester United',
                'away_team': 'Tottenham',
                'league': 'Premier League', 
                'home_odds': 1.9,
                'draw_odds': 3.6,
                'away_odds': 3.8
            },
            {
                'kick_off': '17:30',
                'home_team': 'Liverpool',
                'away_team': 'Newcastle',
                'league': 'Premier League',
                'home_odds': 1.4,
                'draw_odds': 4.5,
                'away_odds': 7.0
            },
            {
                'kick_off': '15:15',
                'home_team': 'Bayern Munich',
                'away_team': 'Borussia Dortmund',
                'league': 'Bundesliga',
                'home_odds': 1.8,
                'draw_odds': 3.8,
                'away_odds': 4.2
            },
            {
                'kick_off': '18:00',
                'home_team': 'Real Madrid',
                'away_team': 'Atletico Madrid',
                'league': 'La Liga',
                'home_odds': 2.0,
                'draw_odds': 3.2,
                'away_odds': 3.6
            }
        ]
    
    def get_sunday_matches(self):
        """Sunday fixtures - Generate plausible matches for current date"""
        # Check if we're in off-season (June-July typically)
        if self.month in [6, 7]:
            return self.get_summer_matches()
            
        # Generate realistic matchups with random selection to avoid repetition
        premier_teams = ['Arsenal', 'Chelsea', 'Liverpool', 'Manchester United', 'Manchester City', 'Tottenham', 'Newcastle', 'Brighton', 'West Ham', 'Aston Villa']
        serie_a_teams = ['Juventus', 'Inter Milan', 'AC Milan', 'Roma', 'Napoli', 'Atalanta', 'Lazio', 'Fiorentina']
        la_liga_teams = ['Real Madrid', 'Barcelona', 'Atletico Madrid', 'Sevilla', 'Valencia', 'Villarreal', 'Real Betis', 'Athletic Bilbao']
        
        # Randomly select teams for today's matches
        random.seed(self.current_date.day + self.current_date.month)  # Consistent for the day
        
        matches = []
        
        # Premier League Sunday match (1-2 matches typical)
        if len(premier_teams) >= 4:
            home1, away1, home2, away2 = random.sample(premier_teams, 4)
            matches.append({
                'kick_off': '14:00',
                'home_team': home1,
                'away_team': away1,
                'league': 'Premier League',
                'home_odds': round(random.uniform(1.4, 3.5), 2),
                'draw_odds': round(random.uniform(3.0, 4.5), 1),
                'away_odds': round(random.uniform(1.8, 6.0), 2)
            })
            matches.append({
                'kick_off': '16:30',
                'home_team': home2,
                'away_team': away2,
                'league': 'Premier League',
                'home_odds': round(random.uniform(1.8, 3.0), 2),
                'draw_odds': round(random.uniform(3.0, 3.8), 1),
                'away_odds': round(random.uniform(2.0, 4.0), 2)
            })
        
        # Serie A Sunday matches (2-3 typical)
        if len(serie_a_teams) >= 6:
            serie_selection = random.sample(serie_a_teams, 6)
            matches.extend([
                {
                    'kick_off': '15:00',
                    'home_team': serie_selection[0],
                    'away_team': serie_selection[1],
                    'league': 'Serie A',
                    'home_odds': round(random.uniform(1.6, 2.8), 2),
                    'draw_odds': round(random.uniform(3.2, 3.8), 1),
                    'away_odds': round(random.uniform(2.0, 4.5), 2)
                },
                {
                    'kick_off': '18:00',
                    'home_team': serie_selection[2],
                    'away_team': serie_selection[3],
                    'league': 'Serie A',
                    'home_odds': round(random.uniform(1.5, 2.5), 2),
                    'draw_odds': round(random.uniform(3.4, 4.0), 1),
                    'away_odds': round(random.uniform(2.2, 5.0), 2)
                },
                {
                    'kick_off': '20:45',
                    'home_team': serie_selection[4],
                    'away_team': serie_selection[5],
                    'league': 'Serie A',
                    'home_odds': round(random.uniform(1.7, 3.0), 2),
                    'draw_odds': round(random.uniform(3.0, 4.2), 1),
                    'away_odds': round(random.uniform(1.8, 4.5), 2)
                }
            ])
        
        # La Liga Sunday match (1 typical)
        if len(la_liga_teams) >= 2:
            la_liga_selection = random.sample(la_liga_teams, 2)
            matches.append({
                'kick_off': '21:00',
                'home_team': la_liga_selection[0],
                'away_team': la_liga_selection[1],
                'league': 'La Liga',
                'home_odds': round(random.uniform(1.4, 2.8), 2),
                'draw_odds': round(random.uniform(3.2, 4.5), 1),
                'away_odds': round(random.uniform(2.0, 6.0), 2)
            })
        
        return matches
    
    def get_tuesday_matches(self):
        """Tuesday - Champions League night"""
        return [
            {
                'kick_off': '20:00',
                'home_team': 'Manchester City',
                'away_team': 'PSG',
                'league': 'UEFA Champions League',
                'home_odds': 1.8,
                'draw_odds': 3.6,
                'away_odds': 4.0
            },
            {
                'kick_off': '20:00',
                'home_team': 'Real Madrid',
                'away_team': 'Bayern Munich',
                'league': 'UEFA Champions League',
                'home_odds': 2.2,
                'draw_odds': 3.3,
                'away_odds': 3.1
            },
            {
                'kick_off': '20:00',
                'home_team': 'Arsenal',
                'away_team': 'Barcelona',
                'league': 'UEFA Champions League',
                'home_odds': 3.0,
                'draw_odds': 3.4,
                'away_odds': 2.3
            }
        ]
    
    def get_wednesday_matches(self):
        """Wednesday - Champions League and Europa League"""
        return [
            {
                'kick_off': '20:00',
                'home_team': 'Liverpool',
                'away_team': 'AC Milan',
                'league': 'UEFA Champions League',
                'home_odds': 1.9,
                'draw_odds': 3.5,
                'away_odds': 3.8
            },
            {
                'kick_off': '18:45',
                'home_team': 'Tottenham',
                'away_team': 'Roma',
                'league': 'UEFA Europa League',
                'home_odds': 2.1,
                'draw_odds': 3.3,
                'away_odds': 3.4
            },
            {
                'kick_off': '18:45',
                'home_team': 'West Ham',
                'away_team': 'Sevilla',
                'league': 'UEFA Europa League',
                'home_odds': 2.8,
                'draw_odds': 3.2,
                'away_odds': 2.5
            }
        ]
    
    def get_weekday_matches(self):
        """Weekday matches - cup competitions or makeup games"""
        day_name = self.current_date.strftime('%A')
        
        if self.month in [1, 2]:  # Winter cup season
            return [
                {
                    'kick_off': '19:45',
                    'home_team': 'Chelsea',
                    'away_team': 'Liverpool',
                    'league': 'EFL Cup',
                    'home_odds': 2.3,
                    'draw_odds': 3.1,
                    'away_odds': 3.0
                },
                {
                    'kick_off': '20:00',
                    'home_team': 'Manchester United',
                    'away_team': 'Arsenal',
                    'league': 'FA Cup',
                    'home_odds': 2.0,
                    'draw_odds': 3.4,
                    'away_odds': 3.5
                }
            ]
        
        return [
            {
                'kick_off': '19:30',
                'home_team': 'Brighton',
                'away_team': 'Crystal Palace',
                'league': 'Premier League',
                'home_odds': 2.2,
                'draw_odds': 3.2,
                'away_odds': 3.3
            }
        ]
    
    def get_summer_matches(self):
        """Summer matches - internationals and friendlies"""
        return [
            {
                'kick_off': '20:00',
                'home_team': 'England',
                'away_team': 'Germany',
                'league': 'International Friendly',
                'home_odds': 2.4,
                'draw_odds': 3.1,
                'away_odds': 2.9
            },
            {
                'kick_off': '18:00',
                'home_team': 'Spain',
                'away_team': 'Italy',
                'league': 'UEFA Nations League',
                'home_odds': 2.0,
                'draw_odds': 3.3,
                'away_odds': 3.5
            }
        ]

def main():
    """Test the realistic fixtures generator"""
    generator = RealisticFixturesGenerator()
    matches = generator.get_todays_matches()
    
    print(f"\n⚽ TODAY'S MATCHES:")
    print("=" * 40)
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['kick_off']} | {match['league']}")
        print(f"   {match['home_team']} vs {match['away_team']}")
        print(f"   Odds: {match['home_odds']} / {match['draw_odds']} / {match['away_odds']}")
        print()
    
    print(f"Total matches: {len(matches)}")

if __name__ == "__main__":
    main()