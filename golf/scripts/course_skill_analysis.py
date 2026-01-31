"""
Course Skill Analysis
Analyzes historical tournament data to determine which strokes-gained categories
predict success at each PGA Tour course. Uses regression analysis to derive
optimal skill weights.
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Add parent directory for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)
sys.path.insert(0, parent_dir)

from datagolf_client import DataGolfClient
from configs.config import DATAGOLF_API_KEY


@dataclass
class CourseSkillWeights:
    """Derived skill weights for a course based on historical analysis"""
    event_id: int
    event_name: str
    course_name: str
    n_tournaments: int
    n_player_rounds: int

    # Regression coefficients (how much each SG category affects finish)
    sg_ott_weight: float
    sg_app_weight: float
    sg_arg_weight: float
    sg_putt_weight: float

    # Normalized weights (sum to 1.0)
    sg_ott_pct: float
    sg_app_pct: float
    sg_arg_pct: float
    sg_putt_pct: float

    # Model fit
    r_squared: float


class CourseSkillAnalyzer:
    """Analyzes historical data to derive course-specific skill weights"""

    def __init__(self, api_key: str):
        self.client = DataGolfClient(api_key)
        self.historical_data: pd.DataFrame = pd.DataFrame()

    def collect_historical_data(
        self,
        event_ids: List[int],
        years: List[int],
        delay: float = 0.5
    ) -> pd.DataFrame:
        """
        Collect historical tournament data for specified events and years

        Args:
            event_ids: List of event IDs to collect
            years: List of years to collect
            delay: Delay between API calls to avoid rate limiting
        """
        all_data = []

        for event_id in event_ids:
            for year in years:
                try:
                    print(f"  Collecting event {event_id} year {year}...")
                    df = self.client.get_historical_event_summary(
                        tour='pga',
                        event_id=str(event_id),
                        year=year
                    )
                    if len(df) > 0:
                        df['year'] = year
                        all_data.append(df)
                        print(f"    Got {len(df)} players")
                    time.sleep(delay)
                except Exception as e:
                    print(f"    Error: {e}")
                    continue

        if all_data:
            self.historical_data = pd.concat(all_data, ignore_index=True)
            print(f"\nTotal: {len(self.historical_data)} player-tournament records")
        return self.historical_data

    def _parse_finish(self, fin_text: str) -> Optional[int]:
        """Convert finish text to numeric position"""
        if pd.isna(fin_text) or fin_text in ['CUT', 'WD', 'DQ', 'MDF']:
            return None

        # Handle ties (T5 -> 5)
        fin = str(fin_text).replace('T', '').strip()
        try:
            return int(fin)
        except ValueError:
            return None

    def analyze_course(self, event_id: int) -> Optional[CourseSkillWeights]:
        """
        Run regression analysis for a specific course/event

        Returns skill weights showing how each SG category predicts finish position
        """
        # Filter data for this event
        df = self.historical_data[self.historical_data['event_id'] == str(event_id)].copy()

        if len(df) < 50:  # Need sufficient data
            print(f"  Insufficient data for event {event_id}: {len(df)} records")
            return None

        # Parse finish positions
        df['finish_pos'] = df['fin_text'].apply(self._parse_finish)
        df = df.dropna(subset=['finish_pos'])

        # Filter to players who made cut (have 4 rounds of SG data)
        df = df[df['rounds_played'] == 4]

        if len(df) < 30:
            print(f"  Insufficient made-cut data for event {event_id}: {len(df)} records")
            return None

        # Prepare features and target
        features = ['sg_ott_avg', 'sg_app_avg', 'sg_arg_avg', 'sg_putt_avg']

        # Check for missing values
        for f in features:
            if f not in df.columns:
                print(f"  Missing feature {f} for event {event_id}")
                return None

        X = df[features].values
        y = df['finish_pos'].values  # Lower is better

        # Standardize features for fair comparison
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Ridge regression to handle collinearity
        model = Ridge(alpha=1.0)
        model.fit(X_scaled, y)

        # Get coefficients (negative means better SG -> better finish)
        coefficients = model.coef_

        # Flip sign so positive = good for performance
        importance = -coefficients

        # Normalize to percentages
        importance_abs = np.abs(importance)
        total = importance_abs.sum()
        if total > 0:
            pcts = importance_abs / total
        else:
            pcts = np.array([0.25, 0.25, 0.25, 0.25])

        # Calculate R-squared
        y_pred = model.predict(X_scaled)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Get event info
        event_name = df['event_name'].iloc[0] if 'event_name' in df.columns else str(event_id)
        n_tournaments = df['year'].nunique()

        return CourseSkillWeights(
            event_id=event_id,
            event_name=event_name,
            course_name=event_name,  # Could be improved with course lookup
            n_tournaments=n_tournaments,
            n_player_rounds=len(df),
            sg_ott_weight=importance[0],
            sg_app_weight=importance[1],
            sg_arg_weight=importance[2],
            sg_putt_weight=importance[3],
            sg_ott_pct=pcts[0],
            sg_app_pct=pcts[1],
            sg_arg_pct=pcts[2],
            sg_putt_pct=pcts[3],
            r_squared=r_squared
        )

    def analyze_all_courses(self, event_ids: List[int]) -> pd.DataFrame:
        """Analyze all courses and return results DataFrame"""
        results = []

        for event_id in event_ids:
            print(f"Analyzing event {event_id}...")
            weights = self.analyze_course(event_id)
            if weights:
                results.append({
                    'event_id': weights.event_id,
                    'event_name': weights.event_name,
                    'n_tournaments': weights.n_tournaments,
                    'n_players': weights.n_player_rounds,
                    'sg_ott_pct': weights.sg_ott_pct,
                    'sg_app_pct': weights.sg_app_pct,
                    'sg_arg_pct': weights.sg_arg_pct,
                    'sg_putt_pct': weights.sg_putt_pct,
                    'r_squared': weights.r_squared
                })

        return pd.DataFrame(results)


# Major PGA Tour events with consistent courses
MAJOR_EVENTS = {
    14: "Masters Tournament",
    26: "U.S. Open",
    100: "The Open Championship",
    33: "PGA Championship",
}

SIGNATURE_EVENTS = {
    11: "THE PLAYERS Championship",
    9: "Arnold Palmer Invitational",
    23: "the Memorial Tournament",
    3: "WM Phoenix Open",
    16: "The Sentry",
}

REGULAR_EVENTS = {
    6: "Sony Open in Hawaii",
    4: "Farmers Insurance Open",
    5: "AT&T Pebble Beach Pro-Am",
    12: "RBC Heritage",
    21: "Charles Schwab Challenge",
    34: "Travelers Championship",
    475: "Valspar Championship",
    27: "FedEx St. Jude Championship",
    13: "Wyndham Championship",
    493: "The RSM Classic",
    60: "TOUR Championship",
}


def main():
    """Run course skill analysis"""
    print("=" * 60)
    print("COURSE SKILL WEIGHT ANALYSIS")
    print("Analyzing historical data to derive optimal weights")
    print("=" * 60)

    analyzer = CourseSkillAnalyzer(DATAGOLF_API_KEY)

    # Collect data for key events across multiple years
    all_events = list(MAJOR_EVENTS.keys()) + list(SIGNATURE_EVENTS.keys()) + list(REGULAR_EVENTS.keys())
    years = [2020, 2021, 2022, 2023, 2024]

    print(f"\nCollecting data for {len(all_events)} events across {len(years)} years...")
    print("This may take a few minutes due to API rate limiting...\n")

    analyzer.collect_historical_data(all_events, years, delay=0.3)

    # Save raw data
    if len(analyzer.historical_data) > 0:
        raw_path = "/Users/dickgibbons/sports-betting/PGA_Bets/data/raw/historical_sg_data.csv"
        analyzer.historical_data.to_csv(raw_path, index=False)
        print(f"\nSaved raw data to {raw_path}")

        # Run analysis
        print("\n" + "=" * 60)
        print("RUNNING REGRESSION ANALYSIS")
        print("=" * 60)

        results = analyzer.analyze_all_courses(all_events)

        if len(results) > 0:
            # Sort by R-squared to show best-fitting models first
            results = results.sort_values('r_squared', ascending=False)

            # Save results
            output_path = "/Users/dickgibbons/sports-betting/PGA_Bets/data/processed/course_skill_weights.csv"
            results.to_csv(output_path, index=False)
            print(f"\nSaved analysis to {output_path}")

            # Display results
            print("\n" + "=" * 60)
            print("COURSE SKILL WEIGHTS (% importance)")
            print("=" * 60)
            print(f"{'Event':<35} {'OTT':>7} {'APP':>7} {'ARG':>7} {'PUTT':>7} {'R²':>7}")
            print("-" * 75)

            for _, row in results.iterrows():
                event_name = row['event_name'][:32] + "..." if len(row['event_name']) > 35 else row['event_name']
                print(f"{event_name:<35} {row['sg_ott_pct']*100:>6.1f}% {row['sg_app_pct']*100:>6.1f}% "
                      f"{row['sg_arg_pct']*100:>6.1f}% {row['sg_putt_pct']*100:>6.1f}% {row['r_squared']:>6.3f}")

            # Summary statistics
            print("\n" + "=" * 60)
            print("SUMMARY: Average importance across all courses")
            print("=" * 60)
            print(f"SG: Off-the-Tee:   {results['sg_ott_pct'].mean()*100:.1f}%")
            print(f"SG: Approach:      {results['sg_app_pct'].mean()*100:.1f}%")
            print(f"SG: Around-Green:  {results['sg_arg_pct'].mean()*100:.1f}%")
            print(f"SG: Putting:       {results['sg_putt_pct'].mean()*100:.1f}%")

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
