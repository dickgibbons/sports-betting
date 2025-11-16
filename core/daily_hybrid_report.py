#!/usr/bin/env python3
"""
Daily Hybrid Betting Report - EXPERIMENTAL
Combines ML predictions with angle-based analysis for NBA games
"""

import sys
import argparse
from datetime import datetime

# Import components
from daily_betting_report import DailyBettingReport
from ml_predictor_wrapper import MLPredictorWrapper
from hybrid_predictor import HybridPredictor


class DailyHybridReport(DailyBettingReport):
    """Extended report that adds ML predictions to angle analysis"""

    def __init__(self, use_ml: bool = True, **kwargs):
        """Initialize hybrid report"""
        super().__init__(**kwargs)

        self.use_ml = use_ml

        if use_ml:
            self.ml_predictor = MLPredictorWrapper()
            self.hybrid_predictor = HybridPredictor()
            print("🔬 Hybrid Mode: ML + Angles")
        else:
            self.ml_predictor = None
            self.hybrid_predictor = None
            print("📊 Angle-Only Mode")

    def generate_daily_report(self):
        """Generate hybrid daily report"""

        print(f"\n{'='*80}")
        print(f"📊 DAILY {'HYBRID ' if self.use_ml else ''}BETTING REPORT - {self.date}")
        print(f"{'='*80}\n")

        # 1. Collect ALL betting opportunities from all sources
        print("🔄 Analyzing all betting opportunities...")

        # NHL opportunities (angle-only, no ML for NHL yet)
        nhl_bets = self._collect_nhl_bets()
        print(f"   ✅ NHL: {len(nhl_bets)} opportunities")

        # Enhance NHL with hybrid predictor (no ML, just standardize format)
        if self.use_ml and nhl_bets:
            nhl_bets = [self.hybrid_predictor.combine_predictions(bet, None) for bet in nhl_bets]

        self.all_bets.extend(nhl_bets)

        # NBA opportunities (with ML integration)
        if self.use_ml:
            print(f"   🤖 Fetching ML predictions for NBA...")
            nba_bets = self._collect_nba_ml_first()
        else:
            nba_bets = self._collect_nba_bets()

        self.all_bets.extend(nba_bets)
        print(f"   ✅ NBA: {len(nba_bets)} opportunities")

        # Soccer opportunities (angle-only)
        if self.include_soccer:
            soccer_bets = self._collect_soccer_bets()
            print(f"   ✅ Soccer: {len(soccer_bets)} opportunities")

            # Enhance Soccer with hybrid predictor (no ML, just standardize format)
            if self.use_ml and soccer_bets:
                soccer_bets = [self.hybrid_predictor.combine_predictions(bet, None) for bet in soccer_bets]

            self.all_bets.extend(soccer_bets)

        # NCAA opportunities (angle-only)
        if self.include_ncaa:
            ncaa_bets = self._collect_ncaa_bets()
            print(f"   ✅ NCAA: {len(ncaa_bets)} opportunities")

            # Enhance NCAA with hybrid predictor (no ML, just standardize format)
            if self.use_ml and ncaa_bets:
                ncaa_bets = [self.hybrid_predictor.combine_predictions(bet, None) for bet in ncaa_bets]

            self.all_bets.extend(ncaa_bets)

        print(f"\n   📊 Total opportunities analyzed: {len(self.all_bets)}\n")

        # 2. Rank ALL bets
        if self.use_ml and self.hybrid_predictor:
            # Use hybrid ranking
            ranked_bets = self.hybrid_predictor.rank_bets(self.all_bets)
        else:
            # Use standard ranking
            ranked_bets = self._rank_all_bets()

        # 3. Display top bets
        self._display_hybrid_bets(ranked_bets)

        # 4. Log bets to tracker
        if self.track_bets:
            self._log_bets_to_tracker(ranked_bets[:10])

        return ranked_bets[:10]

    def _collect_nba_ml_first(self):
        """
        Collect NBA bets starting from ML predictions (ML-first approach)
        This ensures we evaluate ALL games with ML, not just those with angles
        """

        # Get ALL ML predictions
        ml_predictions = self.ml_predictor.get_predictions()

        if not ml_predictions:
            print("   ⚠️  No ML predictions available, falling back to angles only")
            return self._collect_nba_bets()

        print(f"   ✅ Got {len(ml_predictions)} ML predictions")

        # Also get angle opportunities (may be 0-2 games)
        nba_angle_bets = self._collect_nba_bets()
        print(f"   📊 Found {len(nba_angle_bets)} angle-based opportunities")

        # Create a lookup for angle bets by game
        angle_lookup = {}
        for angle_bet in nba_angle_bets:
            angle_lookup[angle_bet['game']] = angle_bet

        # For each ML prediction, create a hybrid bet
        hybrid_bets = []

        for game_key, ml_pred in ml_predictions.items():
            # Create game string
            away_team = ml_pred['away_team']
            home_team = ml_pred['home_team']
            game_str = f"{away_team} @ {home_team}"

            # Check if this game also has angle support
            angle_bet = angle_lookup.get(game_str)

            if angle_bet:
                # Has both ML and angles - combine them
                hybrid_bet = self.hybrid_predictor.combine_predictions(angle_bet, ml_pred)
            else:
                # ML only - create a minimal angle bet structure
                winner = ml_pred['predicted_winner']
                minimal_angle_bet = {
                    'sport': 'NBA',
                    'date': self.date,
                    'game': game_str,
                    'bet': f"{winner} ML",
                    'bet_type': 'ML',  # Moneyline bet
                    'expected_edge': 0.0,  # No angle edge
                    'angle_count': 0,
                    'angles': []
                }
                hybrid_bet = self.hybrid_predictor.combine_predictions(minimal_angle_bet, ml_pred)

            hybrid_bets.append(hybrid_bet)

        return hybrid_bets

    def _enhance_with_ml(self, nba_bets):
        """Enhance NBA bets with ML predictions"""

        # Get ML predictions
        ml_predictions = self.ml_predictor.get_predictions()

        if not ml_predictions:
            print("   ⚠️  No ML predictions available, using angles only")
            return nba_bets

        print(f"   ✅ Got {len(ml_predictions)} ML predictions")

        # Enhance each NBA bet with ML
        enhanced_bets = []

        for bet in nba_bets:
            # Extract team names
            game_parts = bet['game'].split(' @ ')
            if len(game_parts) == 2:
                away_team, home_team = game_parts

                # Find matching ML prediction
                ml_pred = self.ml_predictor.get_prediction_for_game(home_team, away_team)

                # Combine with hybrid predictor
                enhanced_bet = self.hybrid_predictor.combine_predictions(bet, ml_pred)
                enhanced_bets.append(enhanced_bet)
            else:
                # Can't parse game, keep original
                enhanced_bets.append(bet)

        return enhanced_bets

    def _display_hybrid_bets(self, ranked_bets):
        """Display top hybrid bets"""

        if not ranked_bets:
            print("\n⚠️  No bets meet the recommendation criteria today\n")
            return

        top_bets = ranked_bets[:10]

        # Group by confidence
        by_confidence = {
            'ELITE': [],
            'HIGH': [],
            'MEDIUM': [],
            'LOW': []
        }

        for bet in top_bets:
            conf = bet.get('confidence', 'LOW')
            if conf in by_confidence:
                by_confidence[conf].append(bet)

        print(f"\n{'='*80}")
        print(f"🏆 TOP 10 {'HYBRID ' if self.use_ml else ''}BETS TODAY - {self.date}")
        print(f"{'='*80}\n")

        print(f"📊 BREAKDOWN:")
        print(f"   🔥 ELITE: {len(by_confidence['ELITE'])} bets")
        print(f"   ✅ HIGH: {len(by_confidence['HIGH'])} bets")
        print(f"   💡 MEDIUM: {len(by_confidence['MEDIUM'])} bets")
        print(f"   ⚪ LOW: {len(by_confidence['LOW'])} bets")

        print(f"\n{'─'*80}\n")

        # Display each bet
        for i, bet in enumerate(top_bets, 1):
            self._display_single_hybrid_bet(i, bet)

    def _display_single_hybrid_bet(self, rank: int, bet: dict):
        """Display a single hybrid bet"""

        conf_emoji = {
            'ELITE': '🔥🔥🔥',
            'HIGH': '✅',
            'MEDIUM': '💡',
            'LOW': '⚪'
        }

        emoji = conf_emoji.get(bet.get('confidence', 'LOW'), '⚪')

        print(f"{emoji} #{rank} {bet['sport']}: {bet['game']}")
        print(f"   BET: {bet['bet']}")

        # Show Expected Value (CRITICAL!)
        ev = bet.get('predicted_ev', 0.0)
        if ev > 0:
            print(f"   💰 Expected Value: +{ev:.1f} ✅")
        elif ev < 0:
            print(f"   ⚠️  Expected Value: {ev:.1f} ❌")

        # Show hybrid score if available
        if 'hybrid_score' in bet and bet['hybrid_score'] > 0:
            print(f"   Hybrid Score: {bet['hybrid_score']:.1f}")

            # Show ML prediction if available
            if bet.get('has_ml'):
                agree_status = "AGREE ✅" if bet.get('ml_agrees') else "CONFLICT ❌"
                print(f"   ML Prediction: {bet['ml_confidence']:.1f}% ({agree_status})")

            # Show angle edge
            print(f"   Angle Edge: +{bet['expected_edge']:.1f}%")

            # Show prediction type
            if bet.get('prediction_type') == 'HYBRID_AGREEMENT':
                print(f"   🔥 ML + Angles AGREE - High Confidence!")
            elif bet.get('prediction_type') == 'HYBRID_CONFLICT':
                print(f"   ⚠️  ML and Angles disagree - use caution")

        else:
            # Standard display
            if bet.get('odds'):
                print(f"   ODDS: {bet['odds']:+d} | True EV: {bet.get('true_ev', 0):.1f}%")
            else:
                print(f"   Expected Edge: +{bet['expected_edge']:.1f}%")

        # Show angles
        print(f"   Angles ({len(bet['angles'])}):")
        for angle in bet['angles'][:3]:  # Show top 3
            print(f"   {angle['reason']}")

        print(f"   💰 RECOMMENDED: Bet {self._get_stake_recommendation(bet['confidence'])}")
        print()


    def _get_stake_recommendation(self, confidence: str) -> str:
        """Get stake recommendation by confidence"""
        stakes = {
            'ELITE': '2-3% of bankroll',
            'HIGH': '1-2% of bankroll',
            'MEDIUM': '0.5-1% of bankroll',
            'LOW': '0.5% of bankroll (optional)'
        }
        return stakes.get(confidence, '0.5% of bankroll')


def main():
    parser = argparse.ArgumentParser(description='Daily Hybrid Betting Report')
    parser.add_argument('--no-ml', action='store_true', help='Run without ML predictions (angle-only)')
    parser.add_argument('--no-soccer', action='store_true', help='Exclude soccer from analysis')
    parser.add_argument('--no-ncaa', action='store_true', help='Exclude NCAA basketball from analysis')
    args = parser.parse_args()

    # First, auto-update results from previous days
    print("\n🔄 Checking for completed games from previous days...")
    try:
        from auto_update_results import AutoResultsUpdater
        updater = AutoResultsUpdater()
        updater.update_all_pending_bets()
    except Exception as e:
        print(f"   ⚠️  Could not auto-update results: {e}")

    # Second, learn from performance and adjust angle weights
    print("\n🧠 Learning from bet performance...")
    try:
        from angle_performance_learner import AnglePerformanceLearner
        learner = AnglePerformanceLearner()
        learner.analyze_and_adjust()
    except Exception as e:
        print(f"   ⚠️  Could not run performance learning: {e}")

    # Generate today's report
    report = DailyHybridReport(
        use_ml=not args.no_ml,
        include_soccer=not args.no_soccer,
        include_ncaa=not args.no_ncaa
    )

    top_bets = report.generate_daily_report()
    report.save_report(top_bets)

    # Show cumulative performance summary
    print("\n" + "="*80)
    print("📊 CUMULATIVE PERFORMANCE SUMMARY")
    print("="*80)

    try:
        summary = report.bet_tracker.get_performance_summary()

        if 'error' not in summary:
            print(f"\n💰 OVERALL STATS:")
            print(f"   Record: {summary['wins']}-{summary['losses']}-{summary['pushes']}")
            print(f"   Win Rate: {summary['win_rate']:.1f}%")
            print(f"   Bankroll: ${summary['current_bankroll']:,.2f} (started ${report.bet_tracker.starting_bankroll:,.2f})")
            print(f"   Total Profit: ${summary['total_profit']:+,.2f}")
            print(f"   ROI: {summary['roi']:.1f}%")
            print(f"   Pending Bets: {summary['pending_bets']}")

    except Exception as e:
        print(f"⚠️  Could not load performance summary: {e}")

    print(f"\n{'='*80}\n")
    print("✅ Daily hybrid report complete!")

    if args.no_ml:
        print("   Ran in ANGLE-ONLY mode")
    else:
        print("   Ran in HYBRID mode (ML + Angles)")

    print(f"   Run with --no-ml for angle-only mode")
    print(f"   Run with --no-soccer to exclude soccer")
    print(f"   Run with --no-ncaa to exclude NCAA basketball")
    print(f"\n💡 For detailed performance breakdown, run: python3 bet_tracker.py")


if __name__ == "__main__":
    main()
