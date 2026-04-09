"""
Course History Analysis
Analyzes whether players consistently over/underperform at specific courses
beyond what their skill metrics would predict.

Key metrics:
1. SG vs Expected at course (did they play better/worse than their usual level?)
2. Consistency (low variance = reliable course fit)
3. Sample size (more appearances = more reliable signal)
"""

import sys
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Add parent directory for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)
sys.path.insert(0, parent_dir)


@dataclass
class PlayerCourseHistory:
    """Course history stats for a player at a specific event"""
    player_id: int
    player_name: str
    event_id: int
    event_name: str

    # Appearances
    n_appearances: int
    n_made_cuts: int
    made_cut_pct: float

    # Finish position stats
    avg_finish: float
    best_finish: int
    top5_count: int
    top10_count: int
    top20_count: int
    wins: int

    # Strokes gained relative to their baseline
    avg_sg_total_at_course: float
    avg_sg_total_elsewhere: float
    sg_course_effect: float  # How much better/worse they play here

    # Consistency
    finish_std: float
    sg_std: float

    # Statistical significance
    t_stat: float
    p_value: float


class CourseHistoryAnalyzer:
    """Analyzes player course history patterns"""

    def __init__(self, historical_sg: pd.DataFrame):
        self.historical_sg = historical_sg.copy()
        self._prepare_data()

    def _prepare_data(self):
        """Prepare data for analysis"""
        # Parse finish positions
        def parse_finish(fin):
            if pd.isna(fin) or fin in ['CUT', 'WD', 'DQ', 'MDF']:
                return None
            return int(str(fin).replace('T', ''))

        self.historical_sg['finish_pos'] = self.historical_sg['fin_text'].apply(parse_finish)

        # Flag made cuts
        self.historical_sg['made_cut'] = self.historical_sg['rounds_played'] >= 4

        # Calculate player baseline SG (their average across all events)
        player_baselines = self.historical_sg.groupby('dg_id').agg({
            'sg_total_avg': 'mean',
            'sg_ott_avg': 'mean',
            'sg_app_avg': 'mean',
            'sg_arg_avg': 'mean',
            'sg_putt_avg': 'mean',
            'player_name': 'first'
        }).reset_index()
        player_baselines.columns = ['dg_id', 'baseline_sg_total', 'baseline_sg_ott',
                                    'baseline_sg_app', 'baseline_sg_arg', 'baseline_sg_putt',
                                    'player_name']

        self.player_baselines = player_baselines

        # Merge baselines back
        self.historical_sg = self.historical_sg.merge(
            player_baselines[['dg_id', 'baseline_sg_total']],
            on='dg_id',
            how='left'
        )

        # Calculate SG vs baseline for each tournament
        self.historical_sg['sg_vs_baseline'] = (
            self.historical_sg['sg_total_avg'] - self.historical_sg['baseline_sg_total']
        )

    def analyze_player_at_course(
        self,
        player_id: int,
        event_id: int,
        min_appearances: int = 2
    ) -> Optional[PlayerCourseHistory]:
        """Analyze a specific player's history at a specific course"""

        # Get player's appearances at this course
        course_data = self.historical_sg[
            (self.historical_sg['dg_id'] == player_id) &
            (self.historical_sg['event_id'] == event_id)
        ].copy()

        if len(course_data) < min_appearances:
            return None

        # Get player's data at OTHER courses (for comparison)
        other_data = self.historical_sg[
            (self.historical_sg['dg_id'] == player_id) &
            (self.historical_sg['event_id'] != event_id)
        ].copy()

        if len(other_data) < 5:  # Need baseline from other events
            return None

        player_name = course_data['player_name'].iloc[0]
        event_name = course_data['event_name'].iloc[0]

        # Basic stats
        n_appearances = len(course_data)
        n_made_cuts = course_data['made_cut'].sum()
        made_cut_pct = n_made_cuts / n_appearances if n_appearances > 0 else 0

        # Finish position stats (only for made cuts)
        made_cut_data = course_data[course_data['finish_pos'].notna()]
        if len(made_cut_data) > 0:
            avg_finish = made_cut_data['finish_pos'].mean()
            best_finish = int(made_cut_data['finish_pos'].min())
            top5_count = (made_cut_data['finish_pos'] <= 5).sum()
            top10_count = (made_cut_data['finish_pos'] <= 10).sum()
            top20_count = (made_cut_data['finish_pos'] <= 20).sum()
            wins = (made_cut_data['finish_pos'] == 1).sum()
            finish_std = made_cut_data['finish_pos'].std() if len(made_cut_data) > 1 else 0
        else:
            avg_finish = None
            best_finish = None
            top5_count = 0
            top10_count = 0
            top20_count = 0
            wins = 0
            finish_std = 0

        # SG analysis
        avg_sg_at_course = course_data['sg_total_avg'].mean()
        avg_sg_elsewhere = other_data['sg_total_avg'].mean()
        sg_course_effect = avg_sg_at_course - avg_sg_elsewhere
        sg_std = course_data['sg_total_avg'].std() if len(course_data) > 1 else 0

        # Statistical significance test
        if len(course_data) >= 2 and len(other_data) >= 5:
            t_stat, p_value = stats.ttest_ind(
                course_data['sg_total_avg'].dropna(),
                other_data['sg_total_avg'].dropna()
            )
        else:
            t_stat = 0
            p_value = 1.0

        return PlayerCourseHistory(
            player_id=player_id,
            player_name=player_name,
            event_id=event_id,
            event_name=event_name,
            n_appearances=n_appearances,
            n_made_cuts=n_made_cuts,
            made_cut_pct=made_cut_pct,
            avg_finish=avg_finish if avg_finish else 999,
            best_finish=best_finish if best_finish else 999,
            top5_count=top5_count,
            top10_count=top10_count,
            top20_count=top20_count,
            wins=wins,
            avg_sg_total_at_course=avg_sg_at_course,
            avg_sg_total_elsewhere=avg_sg_elsewhere,
            sg_course_effect=sg_course_effect,
            finish_std=finish_std,
            sg_std=sg_std,
            t_stat=t_stat,
            p_value=p_value
        )

    def find_course_specialists(
        self,
        event_id: int,
        min_appearances: int = 3,
        top_n: int = 20
    ) -> pd.DataFrame:
        """Find players who consistently outperform at a specific course"""

        # Get all players who have played this event
        event_data = self.historical_sg[self.historical_sg['event_id'] == event_id]
        player_ids = event_data['dg_id'].unique()

        results = []
        for player_id in player_ids:
            history = self.analyze_player_at_course(player_id, event_id, min_appearances)
            if history:
                results.append({
                    'player_id': history.player_id,
                    'player_name': history.player_name,
                    'n_appearances': history.n_appearances,
                    'n_made_cuts': history.n_made_cuts,
                    'made_cut_pct': history.made_cut_pct,
                    'avg_finish': history.avg_finish,
                    'best_finish': history.best_finish,
                    'top10_count': history.top10_count,
                    'wins': history.wins,
                    'sg_at_course': history.avg_sg_total_at_course,
                    'sg_elsewhere': history.avg_sg_total_elsewhere,
                    'course_effect': history.sg_course_effect,
                    'p_value': history.p_value
                })

        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)

        # Sort by course effect (players who play best relative to their baseline)
        df = df.sort_values('course_effect', ascending=False)

        return df.head(top_n)

    def find_course_specialists_all_events(
        self,
        min_appearances: int = 3,
        min_course_effect: float = 0.3
    ) -> pd.DataFrame:
        """Find all significant player-course combinations"""

        all_results = []
        event_ids = self.historical_sg['event_id'].unique()

        for event_id in event_ids:
            specialists = self.find_course_specialists(event_id, min_appearances, top_n=50)
            if len(specialists) > 0:
                # Filter to significant course effects
                significant = specialists[
                    (specialists['course_effect'] >= min_course_effect) |
                    (specialists['course_effect'] <= -min_course_effect)
                ]
                all_results.append(significant)

        if not all_results:
            return pd.DataFrame()

        return pd.concat(all_results, ignore_index=True)

    def get_course_effect_summary(self) -> pd.DataFrame:
        """Summarize course history effects across all events"""

        results = []
        event_ids = self.historical_sg['event_id'].unique()

        for event_id in event_ids:
            event_data = self.historical_sg[self.historical_sg['event_id'] == event_id]
            event_name = event_data['event_name'].iloc[0]

            # Calculate how much players deviate from baseline at this course
            course_effects = event_data.groupby('dg_id')['sg_vs_baseline'].mean()

            results.append({
                'event_id': event_id,
                'event_name': event_name,
                'n_players': len(course_effects),
                'avg_course_effect_spread': course_effects.std(),  # High = course rewards specialists
                'max_positive_effect': course_effects.max(),
                'max_negative_effect': course_effects.min(),
            })

        return pd.DataFrame(results).sort_values('avg_course_effect_spread', ascending=False)


def main():
    """Run course history analysis"""
    print("=" * 70)
    print("COURSE HISTORY ANALYSIS")
    print("Identifying players who over/underperform at specific courses")
    print("=" * 70)

    # Load historical data
    historical_sg = pd.read_csv("/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/raw/historical_sg_data.csv")
    print(f"\nLoaded {len(historical_sg)} player-tournament records")

    analyzer = CourseHistoryAnalyzer(historical_sg)

    # Analyze each major event
    events_to_analyze = [
        (14, "Masters"),
        (11, "THE PLAYERS"),
        (12, "RBC Heritage"),
        (6, "Sony Open"),
        (3, "WM Phoenix Open"),
        (4, "Farmers Insurance"),
        (5, "Pebble Beach"),
        (21, "Charles Schwab"),
        (34, "Travelers"),
        (60, "Tour Championship"),
    ]

    all_specialists = []

    for event_id, event_name in events_to_analyze:
        print(f"\n{'='*70}")
        print(f"COURSE SPECIALISTS: {event_name}")
        print("="*70)

        specialists = analyzer.find_course_specialists(event_id, min_appearances=3, top_n=15)

        if len(specialists) > 0:
            specialists['event_name'] = event_name
            all_specialists.append(specialists)

            print(f"\n{'Player':<25} {'Apps':>4} {'Cuts':>4} {'AvgFin':>7} {'Best':>5} {'T10':>4} {'Wins':>4} {'Course+':>8}")
            print("-" * 75)

            for _, row in specialists.head(10).iterrows():
                effect_str = f"+{row['course_effect']:.2f}" if row['course_effect'] > 0 else f"{row['course_effect']:.2f}"
                print(f"{row['player_name'][:25]:<25} {row['n_appearances']:>4} {row['n_made_cuts']:>4} "
                      f"{row['avg_finish']:>7.1f} {row['best_finish']:>5} {row['top10_count']:>4} "
                      f"{row['wins']:>4} {effect_str:>8}")

            # Also show course "kryptonite" (players who underperform)
            underperformers = specialists.nsmallest(5, 'course_effect')
            print(f"\nPlayers who STRUGGLE at {event_name}:")
            for _, row in underperformers.iterrows():
                effect_str = f"{row['course_effect']:.2f}"
                print(f"  {row['player_name'][:25]:<25} Course Effect: {effect_str}")

    # Save all specialists data
    if all_specialists:
        all_df = pd.concat(all_specialists, ignore_index=True)
        output_path = "/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/processed/course_specialists.csv"
        all_df.to_csv(output_path, index=False)
        print(f"\n\nSaved course specialists data to {output_path}")

    # Course effect summary
    print("\n" + "=" * 70)
    print("COURSE EFFECT SUMMARY")
    print("(Higher spread = course rewards specialists more)")
    print("=" * 70)

    summary = analyzer.get_course_effect_summary()
    summary = summary.head(15)

    print(f"\n{'Event':<40} {'Effect Spread':>14} {'Max Boost':>10}")
    print("-" * 70)
    for _, row in summary.iterrows():
        print(f"{row['event_name'][:40]:<40} {row['avg_course_effect_spread']:>14.3f} {row['max_positive_effect']:>10.2f}")

    # Save summary
    summary_path = "/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/processed/course_effect_summary.csv"
    summary.to_csv(summary_path, index=False)
    print(f"\nSaved course effect summary to {summary_path}")


if __name__ == "__main__":
    main()
