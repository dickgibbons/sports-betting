#!/usr/bin/env python3
"""
Model Calibration - Fix Overconfidence Issues

This script recalibrates the form-enhanced models using:
1. Platt Scaling (logistic regression on model outputs)
2. Isotonic Regression (non-parametric monotonic fit)

The goal is to align predicted probabilities with actual win rates.

Usage:
    python3 calibrate_models.py --backtest-csv backtest_2024_relaxed_detailed.csv
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.calibration import CalibratedClassifierCV
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple

class ModelCalibrator:
    """Calibrate overconfident models using historical predictions"""

    def __init__(self, backtest_results_path: str):
        """Initialize with backtest results CSV"""
        self.backtest_df = pd.read_csv(backtest_results_path)
        self.calibrators = {}

        print(f"📊 Loaded {len(self.backtest_df)} historical predictions")
        print(f"   Markets: {self.backtest_df['market'].unique()}")

    def analyze_calibration(self) -> pd.DataFrame:
        """Analyze current calibration by market"""
        print(f"\n{'='*80}")
        print(f"📈 CALIBRATION ANALYSIS")
        print(f"{'='*80}\n")

        calibration_stats = []

        for market in self.backtest_df['market'].unique():
            market_df = self.backtest_df[self.backtest_df['market'] == market]

            # Calculate statistics
            total_bets = len(market_df)
            wins = market_df['correct'].sum()
            win_rate = wins / total_bets if total_bets > 0 else 0
            avg_confidence = market_df['confidence'].mean()

            # Calibration error (predicted - actual)
            calibration_error = avg_confidence - win_rate

            calibration_stats.append({
                'market': market,
                'bets': total_bets,
                'wins': wins,
                'actual_win_rate': win_rate,
                'avg_predicted_conf': avg_confidence,
                'calibration_error': calibration_error,
                'abs_error': abs(calibration_error)
            })

            print(f"{market}:")
            print(f"   Bets: {total_bets} | Wins: {wins} ({win_rate:.1%})")
            print(f"   Avg Predicted: {avg_confidence:.1%} | Actual: {win_rate:.1%}")
            print(f"   Calibration Error: {calibration_error:+.1%}")
            print()

        return pd.DataFrame(calibration_stats)

    def create_reliability_diagram(self, market: str, save_path: str = None):
        """Create reliability diagram showing predicted vs. actual probabilities"""
        market_df = self.backtest_df[self.backtest_df['market'] == market]

        # Bin predictions into deciles
        bins = np.linspace(0, 1, 11)
        bin_centers = (bins[:-1] + bins[1:]) / 2

        actual_rates = []
        predicted_rates = []
        bin_counts = []

        for i in range(len(bins) - 1):
            bin_mask = (market_df['confidence'] >= bins[i]) & (market_df['confidence'] < bins[i+1])
            bin_df = market_df[bin_mask]

            if len(bin_df) > 0:
                actual_rates.append(bin_df['correct'].mean())
                predicted_rates.append(bin_df['confidence'].mean())
                bin_counts.append(len(bin_df))
            else:
                actual_rates.append(np.nan)
                predicted_rates.append(np.nan)
                bin_counts.append(0)

        # Plot
        plt.figure(figsize=(10, 8))

        # Perfect calibration line
        plt.plot([0, 1], [0, 1], 'k--', linewidth=2, label='Perfect Calibration', alpha=0.7)

        # Actual calibration
        valid_mask = ~np.isnan(actual_rates)
        plt.scatter(
            np.array(predicted_rates)[valid_mask],
            np.array(actual_rates)[valid_mask],
            s=np.array(bin_counts)[valid_mask] * 2,
            alpha=0.6,
            c='red',
            label='Actual Calibration'
        )

        plt.xlabel('Predicted Probability', fontsize=12)
        plt.ylabel('Actual Win Rate', fontsize=12)
        plt.title(f'Reliability Diagram - {market}\n(Dot size = number of bets)', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=10)
        plt.xlim([0, 1])
        plt.ylim([0, 1])

        # Add statistics
        total = market_df.shape[0]
        win_rate = market_df['correct'].mean()
        avg_conf = market_df['confidence'].mean()
        error = avg_conf - win_rate

        stats_text = f"Total Bets: {total}\n"
        stats_text += f"Win Rate: {win_rate:.1%}\n"
        stats_text += f"Avg Confidence: {avg_conf:.1%}\n"
        stats_text += f"Calibration Error: {error:+.1%}"

        plt.text(0.05, 0.95, stats_text, transform=plt.gca().transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"✅ Saved reliability diagram: {save_path}")

        plt.close()

    def calibrate_platt(self, market: str) -> Tuple[float, float]:
        """
        Calibrate using Platt scaling (logistic regression)

        Returns: (a, b) parameters for: p_calibrated = 1 / (1 + exp(a * p + b))
        """
        market_df = self.backtest_df[self.backtest_df['market'] == market]

        # Transform predictions to logit space
        confidences = market_df['confidence'].values
        # Clip to avoid log(0) or log(1)
        confidences = np.clip(confidences, 0.001, 0.999)
        logits = np.log(confidences / (1 - confidences)).reshape(-1, 1)

        # Fit logistic regression
        lr = LogisticRegression()
        lr.fit(logits, market_df['correct'].values)

        a = lr.coef_[0][0]
        b = lr.intercept_[0]

        print(f"\n{market} - Platt Scaling:")
        print(f"   Parameters: a={a:.4f}, b={b:.4f}")

        # Calculate calibrated predictions
        calibrated_probs = 1 / (1 + np.exp(a * logits.flatten() + b))
        calibrated_avg = calibrated_probs.mean()
        actual_rate = market_df['correct'].mean()

        print(f"   Before: {confidences.mean():.1%} predicted → {actual_rate:.1%} actual")
        print(f"   After:  {calibrated_avg:.1%} predicted → {actual_rate:.1%} actual")

        return (a, b)

    def calibrate_isotonic(self, market: str) -> IsotonicRegression:
        """
        Calibrate using isotonic regression (non-parametric)

        Returns: IsotonicRegression model
        """
        market_df = self.backtest_df[self.backtest_df['market'] == market]

        confidences = market_df['confidence'].values
        actuals = market_df['correct'].values

        # Fit isotonic regression
        iso = IsotonicRegression(out_of_bounds='clip')
        iso.fit(confidences, actuals)

        print(f"\n{market} - Isotonic Regression:")

        # Calculate calibrated predictions
        calibrated_probs = iso.predict(confidences)
        calibrated_avg = calibrated_probs.mean()
        actual_rate = actuals.mean()

        print(f"   Before: {confidences.mean():.1%} predicted → {actual_rate:.1%} actual")
        print(f"   After:  {calibrated_avg:.1%} predicted → {actual_rate:.1%} actual")

        return iso

    def save_calibration_parameters(self, output_path: str = 'models/calibration_params.pkl'):
        """Save calibration parameters for production use"""

        calibration_data = {
            'platt_scaling': {},
            'isotonic': {},
            'metadata': {
                'training_period': f"{self.backtest_df['date'].min()} to {self.backtest_df['date'].max()}",
                'total_bets': len(self.backtest_df),
                'markets': list(self.backtest_df['market'].unique())
            }
        }

        # Calibrate each market
        for market in self.backtest_df['market'].unique():
            if self.backtest_df[self.backtest_df['market'] == market].shape[0] >= 10:
                # Platt scaling
                a, b = self.calibrate_platt(market)
                calibration_data['platt_scaling'][market] = {'a': a, 'b': b}

                # Isotonic regression
                iso = self.calibrate_isotonic(market)
                calibration_data['isotonic'][market] = iso

        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        joblib.dump(calibration_data, output_path)
        print(f"\n✅ Saved calibration parameters: {output_path}")

        return calibration_data

    def apply_calibration(self, confidence: float, market: str, method: str = 'platt') -> float:
        """
        Apply calibration to a new prediction

        Args:
            confidence: Original model confidence (0-1)
            market: Market type ('Home Win', 'Under 2.5', 'BTTS Yes', etc.)
            method: 'platt' or 'isotonic'

        Returns:
            Calibrated probability (0-1)
        """
        if market not in self.calibrators:
            print(f"⚠️  No calibration available for {market}, returning original confidence")
            return confidence

        if method == 'platt':
            a, b = self.calibrators['platt_scaling'][market]
            confidence = np.clip(confidence, 0.001, 0.999)
            logit = np.log(confidence / (1 - confidence))
            calibrated = 1 / (1 + np.exp(a * logit + b))
        elif method == 'isotonic':
            iso = self.calibrators['isotonic'][market]
            calibrated = iso.predict([confidence])[0]
        else:
            raise ValueError(f"Unknown calibration method: {method}")

        return float(calibrated)

    def create_all_diagrams(self, output_dir: str = 'calibration_plots'):
        """Create reliability diagrams for all markets"""
        os.makedirs(output_dir, exist_ok=True)

        for market in self.backtest_df['market'].unique():
            safe_market_name = market.replace(' ', '_').replace('.', '')
            output_path = os.path.join(output_dir, f'reliability_{safe_market_name}.png')
            self.create_reliability_diagram(market, output_path)

        print(f"\n✅ Created {len(self.backtest_df['market'].unique())} reliability diagrams in {output_dir}/")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Calibrate overconfident models')
    parser.add_argument('--backtest-csv', default='backtest_2024_relaxed_detailed.csv',
                       help='Path to backtest results CSV')
    parser.add_argument('--output', default='models/calibration_params.pkl',
                       help='Output path for calibration parameters')
    parser.add_argument('--plot-dir', default='calibration_plots',
                       help='Directory for reliability diagrams')

    args = parser.parse_args()

    # Check if backtest file exists
    if not os.path.exists(args.backtest_csv):
        print(f"❌ Backtest results not found: {args.backtest_csv}")
        print(f"   Please run backtest first to generate calibration data")
        sys.exit(1)

    try:
        # Initialize calibrator
        calibrator = ModelCalibrator(args.backtest_csv)

        # Analyze current calibration
        print(f"\n{'='*80}")
        print(f"STEP 1: Analyze Current Calibration")
        print(f"{'='*80}")
        calibration_stats = calibrator.analyze_calibration()

        # Create reliability diagrams
        print(f"\n{'='*80}")
        print(f"STEP 2: Create Reliability Diagrams")
        print(f"{'='*80}")
        calibrator.create_all_diagrams(args.plot_dir)

        # Calibrate models
        print(f"\n{'='*80}")
        print(f"STEP 3: Calibrate Models")
        print(f"{'='*80}")
        calibration_data = calibrator.save_calibration_parameters(args.output)

        # Summary
        print(f"\n{'='*80}")
        print(f"✅ CALIBRATION COMPLETE")
        print(f"{'='*80}")
        print(f"\nCalibration files created:")
        print(f"  📊 Parameters: {args.output}")
        print(f"  📈 Diagrams: {args.plot_dir}/")
        print(f"\nNext steps:")
        print(f"  1. Review reliability diagrams to verify calibration")
        print(f"  2. Update soccer_best_bets_daily.py to load calibration params")
        print(f"  3. Apply calibration to model predictions before thresholding")
        print(f"  4. Re-run backtest with calibrated predictions")

    except Exception as e:
        print(f"\n❌ Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
