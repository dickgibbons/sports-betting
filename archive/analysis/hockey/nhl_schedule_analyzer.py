#!/usr/bin/env python3
"""
NHL Schedule Situation Analyzer

Analyzes team performance in different schedule situations:
- Back-to-back games
- Three games in four nights
- Home vs Road splits for these situations

Usage:
    python3 nhl_schedule_analyzer.py --start-date 2023-10-01 --end-date 2024-04-30
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import argparse
import sys


class NHLScheduleAnalyzer:
    """Analyze NHL team performance in back-to-back and compressed schedule situations"""

    def __init__(self):
        """Initialize the analyzer"""
        self.nhl_api_base = "https://api-web.nhle.com/v1"
        self.games_data = []
        self.team_schedules = defaultdict(list)
        self.b2b_results = []
        self.three_in_four_results = []

    def fetch_schedule(self, start_date: str, end_date: str):
        """Fetch NHL schedule for date range"""
        print(f"\n{'='*80}")
        print(f"🏒 NHL SCHEDULE SITUATION ANALYZER")
        print(f"{'='*80}")
        print(f"Fetching schedule from {start_date} to {end_date}...")
        print(f"{'='*80}\n")

        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        total_days = (end - current_date).days + 1
        days_processed = 0

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                # Use official NHL API
                url = f"{self.nhl_api_base}/schedule/{date_str}"
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    game_week = data.get('gameWeek', [])

                    for day in game_week:
                        if day.get('date') == date_str:
                            games = day.get('games', [])

                            for game in games:
                                game_state = game.get('gameState', 'UNKNOWN')

                                # Only process finished games
                                if game_state in ['OFF', 'FINAL']:
                                    self._process_game(game, date_str)

                    if days_processed % 10 == 0:
                        progress = (days_processed / total_days) * 100
                        print(f"📅 Progress: {days_processed}/{total_days} days ({progress:.1f}%)")

            except Exception as e:
                print(f"⚠️  Error fetching {date_str}: {e}")

            current_date += timedelta(days=1)
            days_processed += 1

        print(f"\n✅ Schedule fetch complete!")
        print(f"Total games processed: {len(self.games_data)}")
        print(f"{'='*80}\n")

    def _process_game(self, game: Dict, date_str: str):
        """Process a single game"""
        try:
            home_team = game.get('homeTeam', {})
            away_team = game.get('awayTeam', {})

            home_name = home_team.get('abbrev', 'UNK')
            away_name = away_team.get('abbrev', 'UNK')

            home_score = home_team.get('score', 0)
            away_score = away_team.get('score', 0)

            # Determine winner
            if home_score > away_score:
                home_win = True
            elif away_score > home_score:
                home_win = False
            else:
                # Tie (shouldn't happen in modern NHL, but handle it)
                home_win = None

            game_data = {
                'date': date_str,
                'home_team': home_name,
                'away_team': away_name,
                'home_score': home_score,
                'away_score': away_score,
                'home_win': home_win,
                'game_id': game.get('id', 0)
            }

            self.games_data.append(game_data)

            # Add to team schedules
            self.team_schedules[home_name].append({
                'date': date_str,
                'opponent': away_name,
                'home': True,
                'score_for': home_score,
                'score_against': away_score,
                'won': home_win
            })

            self.team_schedules[away_name].append({
                'date': date_str,
                'opponent': home_name,
                'home': False,
                'score_for': away_score,
                'score_against': home_score,
                'won': not home_win if home_win is not None else None
            })

        except Exception as e:
            print(f"⚠️  Error processing game: {e}")

    def identify_back_to_back(self):
        """Identify all back-to-back situations"""
        print(f"\n{'='*80}")
        print(f"🔍 IDENTIFYING BACK-TO-BACK SITUATIONS")
        print(f"{'='*80}\n")

        for team, schedule in self.team_schedules.items():
            # Sort by date
            schedule.sort(key=lambda x: x['date'])

            for i in range(len(schedule) - 1):
                game1 = schedule[i]
                game2 = schedule[i + 1]

                date1 = datetime.strptime(game1['date'], '%Y-%m-%d')
                date2 = datetime.strptime(game2['date'], '%Y-%m-%d')

                # Check if consecutive days
                if (date2 - date1).days == 1:
                    # This is a back-to-back
                    self.b2b_results.append({
                        'team': team,
                        'game1_date': game1['date'],
                        'game1_home': game1['home'],
                        'game1_won': game1['won'],
                        'game1_score_for': game1['score_for'],
                        'game1_score_against': game1['score_against'],
                        'game2_date': game2['date'],
                        'game2_home': game2['home'],
                        'game2_won': game2['won'],
                        'game2_score_for': game2['score_for'],
                        'game2_score_against': game2['score_against']
                    })

        print(f"✅ Found {len(self.b2b_results)} back-to-back situations")
        print(f"{'='*80}\n")

    def identify_three_in_four(self):
        """Identify three games in four nights situations"""
        print(f"\n{'='*80}")
        print(f"🔍 IDENTIFYING THREE-IN-FOUR SITUATIONS")
        print(f"{'='*80}\n")

        for team, schedule in self.team_schedules.items():
            # Sort by date
            schedule.sort(key=lambda x: x['date'])

            for i in range(len(schedule) - 2):
                game1 = schedule[i]
                game2 = schedule[i + 1]
                game3 = schedule[i + 2]

                date1 = datetime.strptime(game1['date'], '%Y-%m-%d')
                date3 = datetime.strptime(game3['date'], '%Y-%m-%d')

                # Check if span is 3 days (inclusive = 4 nights)
                if (date3 - date1).days == 3:
                    # This is three-in-four
                    self.three_in_four_results.append({
                        'team': team,
                        'start_date': game1['date'],
                        'end_date': game3['date'],
                        'game1_home': game1['home'],
                        'game1_won': game1['won'],
                        'game2_home': game2['home'],
                        'game2_won': game2['won'],
                        'game3_home': game3['home'],
                        'game3_won': game3['won'],
                        'total_wins': sum([g['won'] for g in [game1, game2, game3] if g['won'] is not None])
                    })

        print(f"✅ Found {len(self.three_in_four_results)} three-in-four situations")
        print(f"{'='*80}\n")

    def analyze_back_to_back(self) -> pd.DataFrame:
        """Analyze back-to-back performance with home/road splits"""
        print(f"\n{'='*80}")
        print(f"📊 BACK-TO-BACK ANALYSIS")
        print(f"{'='*80}\n")

        if not self.b2b_results:
            print("⚠️  No back-to-back data to analyze")
            return pd.DataFrame()

        df = pd.DataFrame(self.b2b_results)

        # Overall Game 2 performance (the back-to-back game)
        game2_total = len(df)
        game2_wins = df['game2_won'].sum()
        game2_win_pct = (game2_wins / game2_total) * 100 if game2_total > 0 else 0

        print(f"📈 OVERALL BACK-TO-BACK PERFORMANCE (Game 2)")
        print(f"{'─'*80}")
        print(f"Total B2B situations: {game2_total}")
        print(f"Game 2 wins: {game2_wins}")
        print(f"Game 2 win rate: {game2_win_pct:.1f}%")
        print(f"{'─'*80}\n")

        # Home/Road splits for Game 2
        print(f"📊 GAME 2 PERFORMANCE BY LOCATION")
        print(f"{'─'*80}")

        # Game 2 at HOME (after playing game 1)
        home_b2b = df[df['game2_home'] == True]
        if len(home_b2b) > 0:
            home_wins = home_b2b['game2_won'].sum()
            home_win_pct = (home_wins / len(home_b2b)) * 100
            print(f"Game 2 at HOME:")
            print(f"  Games: {len(home_b2b)} | Wins: {home_wins} | Win%: {home_win_pct:.1f}%")
        else:
            print(f"Game 2 at HOME: No data")

        # Game 2 on ROAD (after playing game 1)
        road_b2b = df[df['game2_home'] == False]
        if len(road_b2b) > 0:
            road_wins = road_b2b['game2_won'].sum()
            road_win_pct = (road_wins / len(road_b2b)) * 100
            print(f"Game 2 on ROAD:")
            print(f"  Games: {len(road_b2b)} | Wins: {road_wins} | Win%: {road_win_pct:.1f}%")
        else:
            print(f"Game 2 on ROAD: No data")

        print(f"{'─'*80}\n")

        # Travel patterns
        print(f"📊 BACK-TO-BACK TRAVEL PATTERNS")
        print(f"{'─'*80}")

        # Home-Home
        home_home = df[(df['game1_home'] == True) & (df['game2_home'] == True)]
        if len(home_home) > 0:
            hh_wins = home_home['game2_won'].sum()
            hh_win_pct = (hh_wins / len(home_home)) * 100
            print(f"HOME → HOME:")
            print(f"  Games: {len(home_home)} | Game 2 Wins: {hh_wins} | Win%: {hh_win_pct:.1f}%")

        # Home-Road
        home_road = df[(df['game1_home'] == True) & (df['game2_home'] == False)]
        if len(home_road) > 0:
            hr_wins = home_road['game2_won'].sum()
            hr_win_pct = (hr_wins / len(home_road)) * 100
            print(f"HOME → ROAD:")
            print(f"  Games: {len(home_road)} | Game 2 Wins: {hr_wins} | Win%: {hr_win_pct:.1f}%")

        # Road-Road
        road_road = df[(df['game1_home'] == False) & (df['game2_home'] == False)]
        if len(road_road) > 0:
            rr_wins = road_road['game2_won'].sum()
            rr_win_pct = (rr_wins / len(road_road)) * 100
            print(f"ROAD → ROAD:")
            print(f"  Games: {len(road_road)} | Game 2 Wins: {rr_wins} | Win%: {rr_win_pct:.1f}%")

        # Road-Home
        road_home = df[(df['game1_home'] == False) & (df['game2_home'] == True)]
        if len(road_home) > 0:
            rh_wins = road_home['game2_won'].sum()
            rh_win_pct = (rh_wins / len(road_home)) * 100
            print(f"ROAD → HOME:")
            print(f"  Games: {len(road_home)} | Game 2 Wins: {rh_wins} | Win%: {rh_win_pct:.1f}%")

        print(f"{'─'*80}\n")

        return df

    def analyze_three_in_four(self) -> pd.DataFrame:
        """Analyze three-in-four performance"""
        print(f"\n{'='*80}")
        print(f"📊 THREE-IN-FOUR ANALYSIS")
        print(f"{'='*80}\n")

        if not self.three_in_four_results:
            print("⚠️  No three-in-four data to analyze")
            return pd.DataFrame()

        df = pd.DataFrame(self.three_in_four_results)

        # Overall stats
        total_situations = len(df)
        avg_wins = df['total_wins'].mean()

        print(f"📈 OVERALL THREE-IN-FOUR PERFORMANCE")
        print(f"{'─'*80}")
        print(f"Total situations: {total_situations}")
        print(f"Average wins per 3-in-4: {avg_wins:.2f}")
        print(f"{'─'*80}\n")

        # Win distribution
        print(f"📊 WIN DISTRIBUTION")
        print(f"{'─'*80}")
        for wins in range(4):
            count = (df['total_wins'] == wins).sum()
            pct = (count / total_situations) * 100 if total_situations > 0 else 0
            print(f"{wins} wins: {count} situations ({pct:.1f}%)")
        print(f"{'─'*80}\n")

        return df

    def generate_betting_insights(self, b2b_df: pd.DataFrame):
        """Generate betting insights from back-to-back analysis"""
        print(f"\n{'='*80}")
        print(f"💡 BETTING INSIGHTS - BACK-TO-BACK SITUATIONS")
        print(f"{'='*80}\n")

        if b2b_df.empty:
            print("⚠️  No data for insights")
            return

        # Compare Game 2 home vs road
        home_b2b = b2b_df[b2b_df['game2_home'] == True]
        road_b2b = b2b_df[b2b_df['game2_home'] == False]

        if len(home_b2b) > 0 and len(road_b2b) > 0:
            home_win_pct = (home_b2b['game2_won'].sum() / len(home_b2b)) * 100
            road_win_pct = (road_b2b['game2_won'].sum() / len(road_b2b)) * 100

            print(f"🏠 BACK-TO-BACK ADVANTAGE ANALYSIS")
            print(f"{'─'*80}")
            print(f"Game 2 at HOME win rate: {home_win_pct:.1f}%")
            print(f"Game 2 on ROAD win rate: {road_win_pct:.1f}%")

            diff = home_win_pct - road_win_pct
            print(f"Home advantage: {diff:+.1f} percentage points")

            if abs(diff) > 5:
                if diff > 0:
                    print(f"\n✅ RECOMMENDATION: Teams playing at home on back-to-backs have a {abs(diff):.1f}% advantage")
                    print(f"   Consider betting ON home teams in Game 2 of back-to-backs")
                else:
                    print(f"\n✅ RECOMMENDATION: Teams playing on road on back-to-backs perform {abs(diff):.1f}% better")
                    print(f"   Consider betting ON road teams in Game 2 of back-to-backs")
            else:
                print(f"\n⚠️  HOME/ROAD difference is small ({abs(diff):.1f}%)")
                print(f"   No clear betting edge from back-to-back location alone")

        print(f"{'─'*80}\n")

        # Travel pattern insights
        patterns = {
            'HOME → HOME': b2b_df[(b2b_df['game1_home'] == True) & (b2b_df['game2_home'] == True)],
            'HOME → ROAD': b2b_df[(b2b_df['game1_home'] == True) & (b2b_df['game2_home'] == False)],
            'ROAD → ROAD': b2b_df[(b2b_df['game1_home'] == False) & (b2b_df['game2_home'] == False)],
            'ROAD → HOME': b2b_df[(b2b_df['game1_home'] == False) & (b2b_df['game2_home'] == True)]
        }

        pattern_stats = []
        for pattern_name, pattern_df in patterns.items():
            if len(pattern_df) > 0:
                win_pct = (pattern_df['game2_won'].sum() / len(pattern_df)) * 100
                pattern_stats.append((pattern_name, win_pct, len(pattern_df)))

        if pattern_stats:
            # Sort by win percentage
            pattern_stats.sort(key=lambda x: x[1], reverse=True)

            print(f"📊 BEST/WORST TRAVEL PATTERNS")
            print(f"{'─'*80}")

            for i, (pattern, win_pct, games) in enumerate(pattern_stats, 1):
                print(f"{i}. {pattern}: {win_pct:.1f}% win rate ({games} games)")

            best_pattern, best_pct, _ = pattern_stats[0]
            worst_pattern, worst_pct, _ = pattern_stats[-1]

            print(f"\n🏆 Best: {best_pattern} ({best_pct:.1f}%)")
            print(f"⚠️  Worst: {worst_pattern} ({worst_pct:.1f}%)")
            print(f"{'─'*80}\n")

    def save_results(self, b2b_df: pd.DataFrame, three_in_four_df: pd.DataFrame):
        """Save analysis results to CSV"""
        if not b2b_df.empty:
            b2b_file = "nhl_back_to_back_analysis.csv"
            b2b_df.to_csv(b2b_file, index=False)
            print(f"✅ Back-to-back analysis saved to: {b2b_file}")

        if not three_in_four_df.empty:
            three_file = "nhl_three_in_four_analysis.csv"
            three_in_four_df.to_csv(three_file, index=False)
            print(f"✅ Three-in-four analysis saved to: {three_file}")

        print()

    def run_analysis(self, start_date: str, end_date: str):
        """Run complete analysis"""
        # Fetch schedule
        self.fetch_schedule(start_date, end_date)

        # Identify situations
        self.identify_back_to_back()
        self.identify_three_in_four()

        # Analyze
        b2b_df = self.analyze_back_to_back()
        three_df = self.analyze_three_in_four()

        # Generate insights
        self.generate_betting_insights(b2b_df)

        # Save results
        self.save_results(b2b_df, three_df)

        print(f"{'='*80}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"{'='*80}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Analyze NHL back-to-back and schedule situations')
    parser.add_argument('--start-date', default='2023-10-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', default='2024-04-30', help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    try:
        analyzer = NHLScheduleAnalyzer()
        analyzer.run_analysis(args.start_date, args.end_date)

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
