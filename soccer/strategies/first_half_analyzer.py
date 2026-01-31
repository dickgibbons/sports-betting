#!/usr/bin/env python3
"""
First Half Goals Analyzer

Analyzes team tendencies to score in the first half (Over/Under 0.5 H1 Goals)
and identifies betting opportunities when both teams have high first-half scoring rates.

Usage:
    python3 first_half_analyzer.py --date 2025-10-25
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
import sys
from collections import defaultdict


class FirstHalfAnalyzer:
    """Analyze first half scoring patterns for soccer teams"""

    def __init__(self, api_key: str):
        """Initialize with FootyStats API key"""
        self.api_key = api_key
        self.base_url = "https://api.footystats.org"
        self.session = requests.Session()

        # League season IDs
        self.season_ids = {
            'Premier League': 12325,
            'La Liga': 12316,
            'Serie A': 12530,
            'Bundesliga': 12529,
            'Ligue 1': 12337,
            'Brazil Serie A': 11321,
        }

        # Team first half statistics
        self.team_h1_stats = defaultdict(lambda: {
            'games': 0,
            'h1_scored': 0,  # Games where team scored in H1
            'h1_conceded': 0,  # Games where team conceded in H1
            'h1_over_0_5': 0,  # Games with over 0.5 H1 goals (either team)
        })

    def fetch_team_h1_stats(self, league_name: str, season_id: int):
        """Fetch first half statistics for all teams in a league"""
        print(f"\n📊 Fetching {league_name} first half stats...")

        url = f"{self.base_url}/league-matches"
        params = {
            'key': self.api_key,
            'season_id': season_id
        }

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if 'data' not in data:
                print(f"   ⚠️  No data for {league_name}")
                return

            matches = data['data']
            completed_matches = [m for m in matches if m.get('status') == 'complete']

            print(f"   ✅ Processing {len(completed_matches)} completed matches")

            # Process each match
            for match in completed_matches:
                home_team = match.get('home_name', '')
                away_team = match.get('away_name', '')

                # Get halftime score
                halftime_score = match.get('halftime_score', '')
                if not halftime_score or '-' not in halftime_score:
                    continue

                try:
                    h1_home, h1_away = map(int, halftime_score.split('-'))
                except:
                    continue

                h1_total = h1_home + h1_away

                # Update home team stats
                self.team_h1_stats[home_team]['games'] += 1
                if h1_home > 0:
                    self.team_h1_stats[home_team]['h1_scored'] += 1
                if h1_away > 0:
                    self.team_h1_stats[home_team]['h1_conceded'] += 1
                if h1_total > 0:
                    self.team_h1_stats[home_team]['h1_over_0_5'] += 1

                # Update away team stats
                self.team_h1_stats[away_team]['games'] += 1
                if h1_away > 0:
                    self.team_h1_stats[away_team]['h1_scored'] += 1
                if h1_home > 0:
                    self.team_h1_stats[away_team]['h1_conceded'] += 1
                if h1_total > 0:
                    self.team_h1_stats[away_team]['h1_over_0_5'] += 1

        except Exception as e:
            print(f"   ⚠️  Error: {e}")

    def build_team_database(self):
        """Build first half statistics database for all teams"""
        print(f"\n{'='*80}")
        print(f"⚽ BUILDING FIRST HALF STATISTICS DATABASE")
        print(f"{'='*80}")

        for league_name, season_id in self.season_ids.items():
            self.fetch_team_h1_stats(league_name, season_id)

        print(f"\n✅ Database built: {len(self.team_h1_stats)} teams analyzed")
        print(f"{'='*80}\n")

    def get_team_h1_rate(self, team_name: str) -> Optional[Dict]:
        """Get first half scoring rate for a team"""
        stats = self.team_h1_stats.get(team_name)

        if not stats or stats['games'] == 0:
            return None

        return {
            'team': team_name,
            'games': stats['games'],
            'h1_scored_pct': (stats['h1_scored'] / stats['games']) * 100,
            'h1_conceded_pct': (stats['h1_conceded'] / stats['games']) * 100,
            'h1_over_0_5_pct': (stats['h1_over_0_5'] / stats['games']) * 100,
            'h1_scored': stats['h1_scored'],
            'h1_over_0_5': stats['h1_over_0_5']
        }

    def analyze_todays_matches(self, date_str: str = None):
        """Analyze today's matches for first half betting opportunities"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')

        print(f"\n{'='*80}")
        print(f"⚽ FIRST HALF GOALS ANALYSIS - {date_str}")
        print(f"{'='*80}\n")

        # Get today's matches (you'll need to implement this based on your API)
        # For now, using a placeholder
        print("📊 Fetching today's matches...")

        # Placeholder - you would fetch today's schedule here
        todays_matches = []

        print(f"   Found {len(todays_matches)} matches\n")

        if not todays_matches:
            print("⚠️  No matches to analyze")
            return

        # Analyze each match
        opportunities = []

        for match in todays_matches:
            home_team = match.get('home_team')
            away_team = match.get('away_team')

            home_stats = self.get_team_h1_rate(home_team)
            away_stats = self.get_team_h1_rate(away_team)

            if not home_stats or not away_stats:
                continue

            # Calculate combined probability of H1 Over 0.5
            # If both teams score in H1 frequently, H1 Over 0.5 is likely
            home_h1_scored_pct = home_stats['h1_scored_pct']
            away_h1_scored_pct = away_stats['h1_scored_pct']

            # Average of both teams' H1 scoring rates
            combined_h1_rate = (home_h1_scored_pct + away_h1_scored_pct) / 2

            # Also look at each team's games with H1 goals
            home_h1_over_pct = home_stats['h1_over_0_5_pct']
            away_h1_over_pct = away_stats['h1_over_0_5_pct']
            avg_h1_over_pct = (home_h1_over_pct + away_h1_over_pct) / 2

            opportunities.append({
                'home_team': home_team,
                'away_team': away_team,
                'home_h1_scored_pct': home_h1_scored_pct,
                'away_h1_scored_pct': away_h1_scored_pct,
                'combined_h1_rate': combined_h1_rate,
                'avg_h1_over_pct': avg_h1_over_pct,
                'home_games': home_stats['games'],
                'away_games': away_stats['games']
            })

        # Sort by combined H1 rate
        opportunities.sort(key=lambda x: x['combined_h1_rate'], reverse=True)

        # Display results
        self.display_opportunities(opportunities)

    def display_opportunities(self, opportunities: List[Dict]):
        """Display first half betting opportunities"""
        print(f"{'='*80}")
        print(f"🎯 FIRST HALF OVER 0.5 GOALS OPPORTUNITIES")
        print(f"{'='*80}\n")

        if not opportunities:
            print("⚠️  No betting opportunities found\n")
            return

        print(f"📊 Found {len(opportunities)} matches analyzed\n")

        # Strong opportunities (both teams score in H1 >60% of the time)
        strong_opps = [o for o in opportunities if o['combined_h1_rate'] >= 60]

        if strong_opps:
            print(f"🔥 STRONG OPPORTUNITIES (Combined H1 Rate >= 60%)")
            print(f"{'─'*80}")
            print(f"Both teams frequently score in first half")
            print(f"{'─'*80}\n")

            for idx, opp in enumerate(strong_opps, 1):
                self.display_opportunity(opp, idx, 'STRONG')

        # Good opportunities (combined rate 50-60%)
        good_opps = [o for o in opportunities if 50 <= o['combined_h1_rate'] < 60]

        if good_opps:
            print(f"\n✅ GOOD OPPORTUNITIES (Combined H1 Rate 50-60%)")
            print(f"{'─'*80}\n")

            for idx, opp in enumerate(good_opps, 1):
                self.display_opportunity(opp, idx, 'GOOD')

        # Summary
        print(f"\n{'='*80}")
        print(f"📈 SUMMARY")
        print(f"{'='*80}")
        print(f"🔥 Strong opportunities: {len(strong_opps)}")
        print(f"✅ Good opportunities: {len(good_opps)}")
        print(f"📊 Total analyzed: {len(opportunities)}")
        print(f"{'='*80}\n")

    def display_opportunity(self, opp: Dict, idx: int, level: str):
        """Display a single betting opportunity"""
        print(f"{idx}. {opp['home_team']} vs {opp['away_team']}")
        print(f"   Home H1 Scoring Rate: {opp['home_h1_scored_pct']:.1f}% ({opp['home_games']} games)")
        print(f"   Away H1 Scoring Rate: {opp['away_h1_scored_pct']:.1f}% ({opp['away_games']} games)")
        print(f"   Combined H1 Rate: {opp['combined_h1_rate']:.1f}%")
        print(f"   Avg H1 Over 0.5: {opp['avg_h1_over_pct']:.1f}%")

        if level == 'STRONG':
            print(f"   💰 BET: First Half Over 0.5 Goals (Strong edge)")
        elif level == 'GOOD':
            print(f"   💰 BET: First Half Over 0.5 Goals (Good edge)")

        print()

    def display_team_stats(self, min_games: int = 5):
        """Display top teams by first half scoring rate"""
        print(f"\n{'='*80}")
        print(f"📊 TEAM FIRST HALF STATISTICS")
        print(f"{'='*80}\n")

        # Convert to list and filter by minimum games
        teams_list = []
        for team, stats in self.team_h1_stats.items():
            if stats['games'] >= min_games:
                teams_list.append({
                    'team': team,
                    'games': stats['games'],
                    'h1_scored_pct': (stats['h1_scored'] / stats['games']) * 100,
                    'h1_over_0_5_pct': (stats['h1_over_0_5'] / stats['games']) * 100
                })

        # Sort by H1 scoring percentage
        teams_list.sort(key=lambda x: x['h1_scored_pct'], reverse=True)

        print(f"🔥 TOP 10 TEAMS - First Half Scoring Rate")
        print(f"{'─'*80}")

        for idx, team in enumerate(teams_list[:10], 1):
            print(f"{idx:2d}. {team['team']:<30} {team['h1_scored_pct']:5.1f}% ({team['games']} games)")

        print(f"\n❄️  BOTTOM 10 TEAMS - First Half Scoring Rate")
        print(f"{'─'*80}")

        for idx, team in enumerate(teams_list[-10:], 1):
            print(f"{idx:2d}. {team['team']:<30} {team['h1_scored_pct']:5.1f}% ({team['games']} games)")

        print(f"{'='*80}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Analyze first half goals patterns')
    parser.add_argument('--date', help='Date to analyze (YYYY-MM-DD)')
    parser.add_argument('--show-teams', action='store_true', help='Show team statistics')

    args = parser.parse_args()

    # FootyStats API key
    api_key = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"

    try:
        analyzer = FirstHalfAnalyzer(api_key)

        # Build team statistics database
        analyzer.build_team_database()

        # Show team statistics if requested
        if args.show_teams:
            analyzer.display_team_stats()

        # Analyze today's matches
        analyzer.analyze_todays_matches(args.date)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
