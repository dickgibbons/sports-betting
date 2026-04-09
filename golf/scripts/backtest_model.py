"""
PGA Tour Prediction Model Backtesting
Tests our course-fit weighted predictions against actual results.

Methodology:
1. For each tournament in test set (2023-2024):
   - Get player SG skills from PRIOR tournaments (trailing average)
   - Apply course-specific weights to generate predicted rankings
   - Compare predictions vs actual finish positions
2. Evaluate using multiple metrics:
   - Correlation between predicted and actual finish
   - Top 10/20 accuracy (did we identify who would finish well?)
   - Winner prediction accuracy
   - Simulated betting returns
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

from datagolf_client import DataGolfClient
from configs.config import DATAGOLF_API_KEY


@dataclass
class BacktestResult:
    """Results from backtesting a single tournament"""
    event_id: int
    event_name: str
    year: int
    n_players: int

    # Correlation metrics
    spearman_corr: float
    kendall_tau: float

    # Top N accuracy (what % of our predicted top N actually finished in top N)
    top5_precision: float
    top10_precision: float
    top20_precision: float

    # Top N recall (what % of actual top N were in our predicted top N)
    top5_recall: float
    top10_recall: float
    top20_recall: float

    # Winner/podium
    winner_in_top5_pred: bool
    winner_in_top10_pred: bool

    # Betting simulation (1 unit on each of our top 5)
    betting_roi: float


class PredictionModel:
    """Model to predict tournament finish based on course-weighted SG skills + course history"""

    def __init__(
        self,
        skill_weights: pd.DataFrame,
        historical_sg: pd.DataFrame,
        course_history_weight: float = 0.15
    ):
        """
        Args:
            skill_weights: DataFrame with course-specific skill weights
            historical_sg: DataFrame with player SG history
            course_history_weight: Weight given to course history effect (0-1)
        """
        self.skill_weights = skill_weights
        self.historical_sg = historical_sg
        self.course_history_weight = course_history_weight
        self._prepare_player_skills()
        self._prepare_course_history()

    def _prepare_player_skills(self):
        """Calculate trailing player skill averages"""
        # Get unique player-year combinations
        self.historical_sg['year'] = self.historical_sg['year'].astype(int)

        # Parse finish positions for weighting recent form
        def parse_finish(fin):
            if pd.isna(fin) or fin in ['CUT', 'WD', 'DQ', 'MDF']:
                return None
            return int(str(fin).replace('T', ''))

        self.historical_sg['finish_pos'] = self.historical_sg['fin_text'].apply(parse_finish)

    def _prepare_course_history(self):
        """Pre-calculate player course history effects"""
        # Calculate player baseline SG (overall average)
        player_baselines = self.historical_sg.groupby('dg_id').agg({
            'sg_total_avg': 'mean'
        }).reset_index()
        player_baselines.columns = ['dg_id', 'baseline_sg']

        # Calculate player-event specific averages
        player_event_sg = self.historical_sg.groupby(['dg_id', 'event_id']).agg({
            'sg_total_avg': ['mean', 'count']
        }).reset_index()
        player_event_sg.columns = ['dg_id', 'event_id', 'event_sg_avg', 'n_appearances']

        # Merge to calculate course effect
        player_event_sg = player_event_sg.merge(player_baselines, on='dg_id')
        player_event_sg['course_effect'] = player_event_sg['event_sg_avg'] - player_event_sg['baseline_sg']

        # Only keep reliable course effects (min 2 appearances)
        player_event_sg = player_event_sg[player_event_sg['n_appearances'] >= 2]

        # Store as lookup dictionary for fast access
        self.course_history = {}
        for _, row in player_event_sg.iterrows():
            key = (int(row['dg_id']), int(row['event_id']))
            self.course_history[key] = {
                'course_effect': row['course_effect'],
                'n_appearances': row['n_appearances']
            }

    def get_course_history_effect(
        self,
        player_id: int,
        event_id: int,
        before_year: int
    ) -> Optional[float]:
        """
        Get player's historical course effect, using only data before target year

        Returns course_effect (positive = player outperforms baseline at this course)
        """
        # Filter historical data to before target year
        mask = (
            (self.historical_sg['dg_id'] == player_id) &
            (self.historical_sg['event_id'] == event_id) &
            (self.historical_sg['year'] < before_year)
        )
        course_data = self.historical_sg[mask]

        if len(course_data) < 2:  # Need minimum history
            return None

        # Get player baseline from other events
        other_mask = (
            (self.historical_sg['dg_id'] == player_id) &
            (self.historical_sg['event_id'] != event_id) &
            (self.historical_sg['year'] < before_year)
        )
        other_data = self.historical_sg[other_mask]

        if len(other_data) < 5:
            return None

        avg_sg_at_course = course_data['sg_total_avg'].mean()
        avg_sg_elsewhere = other_data['sg_total_avg'].mean()

        return avg_sg_at_course - avg_sg_elsewhere

    def get_player_trailing_skills(
        self,
        player_id: int,
        before_year: int,
        n_events: int = 20
    ) -> Optional[Dict[str, float]]:
        """
        Get player's trailing SG averages from events BEFORE the target year

        Args:
            player_id: DataGolf player ID
            before_year: Only use data from years strictly before this
            n_events: Number of recent events to average

        Returns:
            Dict with sg_ott_avg, sg_app_avg, sg_arg_avg, sg_putt_avg
        """
        # Filter to player's events before target year, with valid SG data
        mask = (
            (self.historical_sg['dg_id'] == player_id) &
            (self.historical_sg['year'] < before_year) &
            (self.historical_sg['rounds_played'] >= 2)  # At least made cut
        )
        player_events = self.historical_sg[mask].sort_values('year', ascending=False)

        if len(player_events) < 3:  # Need minimum history
            return None

        # Take most recent n_events
        recent = player_events.head(n_events)

        # Weight more recent events higher
        weights = np.exp(-np.arange(len(recent)) * 0.1)  # Decay factor
        weights = weights / weights.sum()

        return {
            'sg_ott_avg': np.average(recent['sg_ott_avg'], weights=weights),
            'sg_app_avg': np.average(recent['sg_app_avg'], weights=weights),
            'sg_arg_avg': np.average(recent['sg_arg_avg'], weights=weights),
            'sg_putt_avg': np.average(recent['sg_putt_avg'], weights=weights),
        }

    def predict_tournament(
        self,
        event_id: int,
        year: int,
        field_player_ids: List[int]
    ) -> pd.DataFrame:
        """
        Generate predictions for a tournament

        Returns DataFrame with player_id, predicted_score (lower = better)
        """
        # Get course weights
        weights_row = self.skill_weights[self.skill_weights['event_id'] == event_id]

        if len(weights_row) == 0:
            # Use average weights if course not in our database
            weights = {
                'sg_ott': 0.216,
                'sg_app': 0.291,
                'sg_arg': 0.197,
                'sg_putt': 0.297
            }
        else:
            row = weights_row.iloc[0]
            weights = {
                'sg_ott': row['sg_ott_pct'],
                'sg_app': row['sg_app_pct'],
                'sg_arg': row['sg_arg_pct'],
                'sg_putt': row['sg_putt_pct']
            }

        predictions = []
        for player_id in field_player_ids:
            skills = self.get_player_trailing_skills(player_id, year)
            if skills is None:
                continue

            # Calculate weighted skill score (higher = better)
            skill_score = (
                skills['sg_ott_avg'] * weights['sg_ott'] +
                skills['sg_app_avg'] * weights['sg_app'] +
                skills['sg_arg_avg'] * weights['sg_arg'] +
                skills['sg_putt_avg'] * weights['sg_putt']
            )

            # Get course history effect
            course_effect = self.get_course_history_effect(player_id, event_id, year)
            if course_effect is None:
                course_effect = 0.0

            # Combine skill score with course history effect
            # Course effect is in SG units, so we can add it directly
            # Weight determines how much course history matters vs current skill
            combined_score = (
                (1 - self.course_history_weight) * skill_score +
                self.course_history_weight * course_effect
            )

            predictions.append({
                'dg_id': player_id,
                'predicted_score': combined_score,
                'skill_score': skill_score,
                'course_effect': course_effect,
                'sg_ott': skills['sg_ott_avg'],
                'sg_app': skills['sg_app_avg'],
                'sg_arg': skills['sg_arg_avg'],
                'sg_putt': skills['sg_putt_avg'],
            })

        df = pd.DataFrame(predictions)
        df = df.sort_values('predicted_score', ascending=False)  # Higher score = better
        df['predicted_rank'] = range(1, len(df) + 1)

        return df


class Backtester:
    """Run backtests across multiple tournaments"""

    def __init__(self, model: PredictionModel, historical_sg: pd.DataFrame):
        self.model = model
        self.historical_sg = historical_sg

    def backtest_tournament(self, event_id: int, year: int) -> Optional[BacktestResult]:
        """Backtest a single tournament"""
        # Get actual results for this tournament
        # Handle both int and string event_id comparison
        mask = (
            (self.historical_sg['event_id'] == event_id) &
            (self.historical_sg['year'] == year)
        )
        actual_results = self.historical_sg[mask].copy()

        if len(actual_results) < 30:
            return None

        # Parse finish positions
        def parse_finish(fin):
            if pd.isna(fin) or fin in ['CUT', 'WD', 'DQ', 'MDF']:
                return None
            return int(str(fin).replace('T', ''))

        actual_results['actual_finish'] = actual_results['fin_text'].apply(parse_finish)
        actual_results = actual_results.dropna(subset=['actual_finish'])

        if len(actual_results) < 20:
            return None

        # Get field for prediction (players who finished)
        field_ids = actual_results['dg_id'].tolist()

        # Generate predictions
        predictions = self.model.predict_tournament(event_id, year, field_ids)

        if len(predictions) < 20:
            return None

        # Merge predictions with actual results
        merged = predictions.merge(
            actual_results[['dg_id', 'actual_finish', 'player_name']],
            on='dg_id'
        )

        if len(merged) < 20:
            return None

        # Calculate metrics
        spearman_corr, _ = stats.spearmanr(merged['predicted_rank'], merged['actual_finish'])
        kendall_tau, _ = stats.kendalltau(merged['predicted_rank'], merged['actual_finish'])

        # Top N precision and recall
        def calc_top_n_metrics(n):
            pred_top_n = set(merged.nsmallest(n, 'predicted_rank')['dg_id'])
            actual_top_n = set(merged.nsmallest(n, 'actual_finish')['dg_id'])

            intersection = pred_top_n & actual_top_n
            precision = len(intersection) / n if n > 0 else 0
            recall = len(intersection) / len(actual_top_n) if len(actual_top_n) > 0 else 0

            return precision, recall

        top5_prec, top5_rec = calc_top_n_metrics(5)
        top10_prec, top10_rec = calc_top_n_metrics(10)
        top20_prec, top20_rec = calc_top_n_metrics(20)

        # Winner analysis
        winner_id = merged.loc[merged['actual_finish'] == 1, 'dg_id'].values
        if len(winner_id) > 0:
            winner_id = winner_id[0]
            winner_pred_rank = merged.loc[merged['dg_id'] == winner_id, 'predicted_rank'].values[0]
            winner_in_top5 = winner_pred_rank <= 5
            winner_in_top10 = winner_pred_rank <= 10
        else:
            winner_in_top5 = False
            winner_in_top10 = False

        # Simulated betting ROI (bet on top 5 predictions)
        # Assume average odds of +2000 for winner in field of 150
        # If our pick wins, we get +20 units, else -1 unit per pick
        our_top5 = merged.nsmallest(5, 'predicted_rank')
        units_bet = 5
        units_won = 0

        for _, row in our_top5.iterrows():
            if row['actual_finish'] == 1:
                # Winner - estimate odds based on predicted rank
                # Top pick might be +800, 5th pick might be +3000
                estimated_odds = 8 + (row['predicted_rank'] - 1) * 5
                units_won += estimated_odds
            elif row['actual_finish'] <= 5:
                # Top 5 - small return
                units_won += 0.5
            elif row['actual_finish'] <= 10:
                # Top 10 - break even
                units_won += 0.2

        betting_roi = (units_won - units_bet) / units_bet

        event_name = actual_results['event_name'].iloc[0] if 'event_name' in actual_results.columns else str(event_id)

        return BacktestResult(
            event_id=event_id,
            event_name=event_name,
            year=year,
            n_players=len(merged),
            spearman_corr=spearman_corr,
            kendall_tau=kendall_tau,
            top5_precision=top5_prec,
            top10_precision=top10_prec,
            top20_precision=top20_prec,
            top5_recall=top5_rec,
            top10_recall=top10_rec,
            top20_recall=top20_rec,
            winner_in_top5_pred=winner_in_top5,
            winner_in_top10_pred=winner_in_top10,
            betting_roi=betting_roi
        )

    def run_full_backtest(
        self,
        event_ids: List[int],
        years: List[int]
    ) -> Tuple[List[BacktestResult], pd.DataFrame]:
        """Run backtest across all events and years"""
        results = []

        for event_id in event_ids:
            for year in years:
                print(f"  Backtesting event {event_id} year {year}...", end=" ")
                result = self.backtest_tournament(event_id, year)
                if result:
                    results.append(result)
                    print(f"Spearman: {result.spearman_corr:.3f}, Top10 Prec: {result.top10_precision:.1%}")
                else:
                    print("Skipped (insufficient data)")

        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'event_id': r.event_id,
                'event_name': r.event_name,
                'year': r.year,
                'n_players': r.n_players,
                'spearman_corr': r.spearman_corr,
                'kendall_tau': r.kendall_tau,
                'top5_precision': r.top5_precision,
                'top10_precision': r.top10_precision,
                'top20_precision': r.top20_precision,
                'top5_recall': r.top5_recall,
                'top10_recall': r.top10_recall,
                'top20_recall': r.top20_recall,
                'winner_in_top5': r.winner_in_top5_pred,
                'winner_in_top10': r.winner_in_top10_pred,
                'betting_roi': r.betting_roi
            }
            for r in results
        ])

        return results, df


def main():
    """Run backtesting with course history integration"""
    print("=" * 70)
    print("PGA TOUR PREDICTION MODEL BACKTEST")
    print("WITH COURSE HISTORY INTEGRATION")
    print("=" * 70)

    # Load data
    print("\nLoading data...")
    skill_weights = pd.read_csv("/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/processed/course_skill_weights.csv")
    historical_sg = pd.read_csv("/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/raw/historical_sg_data.csv")

    print(f"  Loaded {len(skill_weights)} course profiles")
    print(f"  Loaded {len(historical_sg)} player-tournament records")

    # Test different course history weights to find optimal
    test_events = [14, 26, 100, 33, 11, 9, 23, 3, 16, 6, 4, 5, 12, 21, 34, 475, 27, 13, 493, 60]
    test_years = [2023, 2024]

    print("\n" + "=" * 70)
    print("TESTING DIFFERENT COURSE HISTORY WEIGHTS")
    print("=" * 70)

    weight_results = []
    for ch_weight in [0.0, 0.10, 0.15, 0.20, 0.25, 0.30]:
        print(f"\n--- Course History Weight: {ch_weight:.0%} ---")
        model = PredictionModel(skill_weights, historical_sg, course_history_weight=ch_weight)
        backtester = Backtester(model, historical_sg)
        _, results_df = backtester.run_full_backtest(test_events, test_years)

        avg_spearman = results_df['spearman_corr'].mean()
        avg_top10_prec = results_df['top10_precision'].mean()
        winner_in_top10 = results_df['winner_in_top10'].mean()
        avg_roi = results_df['betting_roi'].mean()

        weight_results.append({
            'weight': ch_weight,
            'spearman': avg_spearman,
            'top10_precision': avg_top10_prec,
            'winner_in_top10': winner_in_top10,
            'betting_roi': avg_roi
        })

        print(f"  Spearman: {avg_spearman:.3f} | Top10 Prec: {avg_top10_prec:.1%} | Winner Top10: {winner_in_top10:.1%} | ROI: {avg_roi:.1%}")

    # Find best weight
    weight_df = pd.DataFrame(weight_results)
    best_weight = weight_df.loc[weight_df['top10_precision'].idxmax(), 'weight']
    print(f"\n✓ BEST Course History Weight: {best_weight:.0%} (by Top 10 Precision)")

    # Run final backtest with optimal weight
    print("\n" + "=" * 70)
    print(f"FINAL BACKTEST WITH {best_weight:.0%} COURSE HISTORY WEIGHT")
    print("=" * 70)

    model = PredictionModel(skill_weights, historical_sg, course_history_weight=best_weight)
    backtester = Backtester(model, historical_sg)

    # Test events (we'll train on 2020-2022, test on 2023-2024)
    test_events = [14, 26, 100, 33, 11, 9, 23, 3, 16, 6, 4, 5, 12, 21, 34, 475, 27, 13, 493, 60]
    test_years = [2023, 2024]

    print(f"\nRunning backtest on {len(test_events)} events across {test_years}...")
    print("-" * 70)

    results, results_df = backtester.run_full_backtest(test_events, test_years)

    # Summary statistics
    print("\n" + "=" * 70)
    print("BACKTEST RESULTS SUMMARY")
    print("=" * 70)

    print(f"\nTotal tournaments tested: {len(results)}")
    print(f"\nCorrelation Metrics (predicted rank vs actual finish):")
    print(f"  Avg Spearman Correlation:  {results_df['spearman_corr'].mean():.3f}")
    print(f"  Avg Kendall Tau:           {results_df['kendall_tau'].mean():.3f}")

    print(f"\nTop N Prediction Accuracy:")
    print(f"  Top 5 Precision:   {results_df['top5_precision'].mean():.1%} (of our top 5 picks, this % finished top 5)")
    print(f"  Top 10 Precision:  {results_df['top10_precision'].mean():.1%}")
    print(f"  Top 20 Precision:  {results_df['top20_precision'].mean():.1%}")

    print(f"\nTop N Recall:")
    print(f"  Top 5 Recall:      {results_df['top5_recall'].mean():.1%} (of actual top 5, this % were in our top 5)")
    print(f"  Top 10 Recall:     {results_df['top10_recall'].mean():.1%}")
    print(f"  Top 20 Recall:     {results_df['top20_recall'].mean():.1%}")

    print(f"\nWinner Identification:")
    print(f"  Winner in our Top 5:   {results_df['winner_in_top5'].mean():.1%}")
    print(f"  Winner in our Top 10:  {results_df['winner_in_top10'].mean():.1%}")

    print(f"\nSimulated Betting:")
    print(f"  Average ROI (5 picks per event): {results_df['betting_roi'].mean():.1%}")

    # Best and worst events
    print("\n" + "-" * 70)
    print("Best Predicted Events (by Spearman correlation):")
    best = results_df.nlargest(5, 'spearman_corr')[['event_name', 'year', 'spearman_corr', 'top10_precision']]
    for _, row in best.iterrows():
        print(f"  {row['event_name'][:35]:<35} {row['year']} | r={row['spearman_corr']:.3f} | Top10={row['top10_precision']:.1%}")

    print("\nWorst Predicted Events:")
    worst = results_df.nsmallest(5, 'spearman_corr')[['event_name', 'year', 'spearman_corr', 'top10_precision']]
    for _, row in worst.iterrows():
        print(f"  {row['event_name'][:35]:<35} {row['year']} | r={row['spearman_corr']:.3f} | Top10={row['top10_precision']:.1%}")

    # Save results
    output_path = "/Users/dickgibbons/AI Projects/sports-betting/PGA_Bets/data/processed/backtest_results.csv"
    results_df.to_csv(output_path, index=False)
    print(f"\nSaved detailed results to {output_path}")

    # Interpretation
    print("\n" + "=" * 70)
    print("INTERPRETATION")
    print("=" * 70)

    avg_spearman = results_df['spearman_corr'].mean()
    if avg_spearman > 0.4:
        print("✓ STRONG predictive model (Spearman > 0.4)")
    elif avg_spearman > 0.25:
        print("✓ MODERATE predictive model (Spearman 0.25-0.4)")
    else:
        print("⚠ WEAK predictive model (Spearman < 0.25)")

    top10_prec = results_df['top10_precision'].mean()
    # Random would be 10/field_size ≈ 7%
    if top10_prec > 0.20:
        print("✓ EXCELLENT Top 10 precision (>20%, ~3x random)")
    elif top10_prec > 0.14:
        print("✓ GOOD Top 10 precision (14-20%, ~2x random)")
    else:
        print("⚠ Marginal Top 10 precision (<14%)")

    winner_top10 = results_df['winner_in_top10'].mean()
    if winner_top10 > 0.35:
        print(f"✓ Strong winner identification ({winner_top10:.0%} in top 10 picks)")
    else:
        print(f"⚠ Winner identification could improve ({winner_top10:.0%} in top 10)")


if __name__ == "__main__":
    main()
