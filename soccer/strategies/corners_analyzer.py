#!/usr/bin/env python3
"""
Corners Data Analyzer - Over/Under 9.5 Corners Analysis

Analyzes historical corners data to identify betting opportunities
for over/under 9.5 corners per game.

Usage:
    python3 corners_analyzer.py --start-date 2023-10-01 --end-date 2025-10-24
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
from footystats_api import FootyStatsAPI

# FootyStats API Key
API_KEY = "ceb338b9bcb82a452efc114fb2d3cccac67f58be1569e7b5acf1d2195adeae11"


class CornersAnalyzer:
    """Analyze corners data for over/under 9.5 betting opportunities"""

    def __init__(self, api_key: str):
        """Initialize with FootyStats API"""
        self.api = FootyStatsAPI(api_key)
        self.matches_data = []

    def fetch_historical_data(self, start_date: str, end_date: str):
        """Fetch historical match data with corners"""
        print(f"\n{'='*80}")
        print(f"📊 CORNERS DATA ANALYSIS")
        print(f"{'='*80}")
        print(f"Fetching data from {start_date} to {end_date}")
        print(f"{'='*80}\n")

        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        total_days = (end - current_date).days + 1
        days_processed = 0

        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')

            try:
                matches = self.api.get_matches_by_date(date_str)

                if matches:
                    # Filter matches with corners data
                    matches_with_corners = [m for m in matches if m.get('total_corners', 0) > 0]
                    self.matches_data.extend(matches_with_corners)

                    if matches_with_corners:
                        print(f"✅ {date_str}: {len(matches_with_corners)} matches with corners data")

            except Exception as e:
                print(f"⚠️  {date_str}: Error - {str(e)}")

            current_date += timedelta(days=1)
            days_processed += 1

            # Progress indicator
            if days_processed % 10 == 0:
                progress = (days_processed / total_days) * 100
                print(f"\n📈 Progress: {days_processed}/{total_days} days ({progress:.1f}%)\n")

        print(f"\n{'='*80}")
        print(f"✅ Data fetch complete!")
        print(f"Total matches with corners data: {len(self.matches_data)}")
        print(f"{'='*80}\n")

    def analyze_corners_data(self) -> pd.DataFrame:
        """Analyze corners data and generate statistics"""
        if not self.matches_data:
            print("⚠️  No data to analyze")
            return pd.DataFrame()

        print(f"\n{'='*80}")
        print(f"📊 ANALYZING CORNERS DATA")
        print(f"{'='*80}\n")

        # Create DataFrame
        df = pd.DataFrame(self.matches_data)

        # Overall statistics
        total_matches = len(df)
        avg_corners = df['total_corners'].mean()
        median_corners = df['total_corners'].median()

        over_9_5_count = (df['total_corners'] > 9.5).sum()
        over_9_5_pct = (over_9_5_count / total_matches) * 100

        under_9_5_count = (df['total_corners'] <= 9.5).sum()
        under_9_5_pct = (under_9_5_count / total_matches) * 100

        print(f"📈 OVERALL CORNERS STATISTICS")
        print(f"{'─'*80}")
        print(f"Total Matches: {total_matches}")
        print(f"Average Corners per Game: {avg_corners:.2f}")
        print(f"Median Corners per Game: {median_corners:.1f}")
        print(f"\nOver 9.5 Corners: {over_9_5_count} matches ({over_9_5_pct:.1f}%)")
        print(f"Under 9.5 Corners: {under_9_5_count} matches ({under_9_5_pct:.1f}%)")
        print(f"{'─'*80}\n")

        # League-specific analysis
        print(f"\n📊 LEAGUE-SPECIFIC ANALYSIS")
        print(f"{'─'*80}")

        league_stats = df.groupby('league').agg({
            'total_corners': ['count', 'mean', 'median'],
            'over_9_5_corners': ['sum', 'mean']
        }).round(2)

        for league in league_stats.index:
            matches_count = int(league_stats.loc[league, ('total_corners', 'count')])
            avg_corners_league = league_stats.loc[league, ('total_corners', 'mean')]
            median_corners_league = league_stats.loc[league, ('total_corners', 'median')]
            over_9_5_league = int(league_stats.loc[league, ('over_9_5_corners', 'sum')])
            over_9_5_pct_league = league_stats.loc[league, ('over_9_5_corners', 'mean')] * 100

            print(f"\n{league}:")
            print(f"  Matches: {matches_count}")
            print(f"  Avg Corners: {avg_corners_league:.2f} | Median: {median_corners_league:.1f}")
            print(f"  Over 9.5: {over_9_5_league} ({over_9_5_pct_league:.1f}%)")
            print(f"  Under 9.5: {matches_count - over_9_5_league} ({100 - over_9_5_pct_league:.1f}%)")

        print(f"{'─'*80}\n")

        # Corner distribution
        print(f"\n📊 CORNERS DISTRIBUTION")
        print(f"{'─'*80}")

        bins = [0, 5, 7, 9, 11, 13, 15, 100]
        labels = ['0-5', '6-7', '8-9', '10-11', '12-13', '14-15', '16+']
        df['corners_range'] = pd.cut(df['total_corners'], bins=bins, labels=labels, include_lowest=True)

        distribution = df['corners_range'].value_counts().sort_index()

        for corner_range, count in distribution.items():
            pct = (count / total_matches) * 100
            print(f"{corner_range} corners: {count} matches ({pct:.1f}%)")

        print(f"{'─'*80}\n")

        return df

    def generate_betting_insights(self, df: pd.DataFrame):
        """Generate betting insights for over/under 9.5 corners"""
        if df.empty:
            return

        print(f"\n{'='*80}")
        print(f"💡 BETTING INSIGHTS - OVER/UNDER 9.5 CORNERS")
        print(f"{'='*80}\n")

        # Find leagues with highest over 9.5 rates
        league_over_rates = df.groupby('league').agg({
            'total_corners': 'count',
            'over_9_5_corners': 'mean'
        }).sort_values('over_9_5_corners', ascending=False)

        print(f"🔥 BEST LEAGUES FOR OVER 9.5 CORNERS:")
        print(f"{'─'*80}")

        for idx, (league, row) in enumerate(league_over_rates.head(5).iterrows(), 1):
            matches = int(row['total_corners'])
            over_rate = row['over_9_5_corners'] * 100
            print(f"{idx}. {league}: {over_rate:.1f}% over rate ({matches} matches)")

        print(f"\n❄️  BEST LEAGUES FOR UNDER 9.5 CORNERS:")
        print(f"{'─'*80}")

        for idx, (league, row) in enumerate(league_over_rates.tail(5).iterrows(), 1):
            matches = int(row['total_corners'])
            under_rate = (1 - row['over_9_5_corners']) * 100
            print(f"{idx}. {league}: {under_rate:.1f}% under rate ({matches} matches)")

        print(f"{'─'*80}\n")

        # Recommendation
        overall_over_rate = df['over_9_5_corners'].mean() * 100

        print(f"\n📌 RECOMMENDATIONS:")
        print(f"{'─'*80}")

        if overall_over_rate > 55:
            print(f"✅ OVER 9.5 corners appears favorable (hit rate: {overall_over_rate:.1f}%)")
            print(f"   Focus on high-scoring leagues with >60% over rate")
        elif overall_over_rate < 45:
            print(f"✅ UNDER 9.5 corners appears favorable (hit rate: {100-overall_over_rate:.1f}%)")
            print(f"   Focus on low-scoring leagues with <40% over rate")
        else:
            print(f"⚠️  Market is balanced (over rate: {overall_over_rate:.1f}%)")
            print(f"   Be selective - focus on leagues with clear tendencies")

        print(f"{'─'*80}\n")

    def save_results(self, df: pd.DataFrame, output_file: str = "corners_analysis.csv"):
        """Save analysis results to CSV"""
        if df.empty:
            return

        df_output = df[[
            'date', 'league', 'home_team', 'away_team',
            'home_corners', 'away_corners', 'total_corners', 'over_9_5_corners'
        ]].copy()

        df_output.to_csv(output_file, index=False)
        print(f"✅ Results saved to: {output_file}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Analyze corners data for over/under 9.5 betting')
    parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', default='corners_analysis.csv', help='Output CSV file')

    args = parser.parse_args()

    try:
        # Initialize analyzer
        analyzer = CornersAnalyzer(API_KEY)

        # Fetch historical data
        analyzer.fetch_historical_data(args.start_date, args.end_date)

        # Analyze data
        df = analyzer.analyze_corners_data()

        # Generate insights
        analyzer.generate_betting_insights(df)

        # Save results
        analyzer.save_results(df, args.output)

        print(f"\n{'='*80}")
        print(f"✅ ANALYSIS COMPLETE!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
