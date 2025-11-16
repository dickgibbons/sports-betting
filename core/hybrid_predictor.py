#!/usr/bin/env python3
"""
Hybrid Predictor - Combines ML predictions with Angle-based analysis
Uses a weighted scoring system to identify the highest-value bets
"""

from typing import Dict, List, Optional
from datetime import datetime


class HybridPredictor:
    """Combines ML predictions with angle-based betting analysis"""

    def __init__(self):
        """Initialize hybrid predictor"""
        # Default weights for combining signals (NHL, other sports)
        self.ml_weight = 0.6  # ML predictions weight
        self.angle_weight = 0.4  # Angle analysis weight

        # Sport-specific weights
        self.sport_weights = {
            'NBA': {'ml': 1.0, 'angle': 0.0},  # ML-only for NBA
            'NHL': {'ml': 0.6, 'angle': 0.4},  # Hybrid for NHL
            # Default for other sports
        }

        # Minimum thresholds
        self.min_ml_confidence = 55.0  # ML must be at least 55% confident
        self.min_angle_edge = 5.0  # Angles must provide at least 5% edge
        self.min_hybrid_score = 20.0  # Combined score threshold

        # Agreement bonus
        self.agreement_bonus = 15.0  # Bonus when ML and angles agree

        print("🔬 Hybrid Predictor initialized")
        print(f"   Default ML Weight: {self.ml_weight * 100}%")
        print(f"   Default Angle Weight: {self.angle_weight * 100}%")
        print(f"   NBA: 100% ML (ML-ONLY MODE)")
        print(f"   NHL: 60% ML + 40% Angles (HYBRID MODE)")

    def combine_predictions(self, angle_bet: Dict, ml_prediction: Optional[Dict]) -> Dict:
        """
        Combine angle-based bet with ML prediction

        Args:
            angle_bet: Bet from angle analysis
            ml_prediction: ML prediction (may be None if unavailable)

        Returns:
            Enhanced bet with hybrid score and analysis
        """

        # Get sport-specific weights
        sport = angle_bet.get('sport', 'DEFAULT')
        if sport in self.sport_weights:
            ml_weight = self.sport_weights[sport]['ml']
            angle_weight = self.sport_weights[sport]['angle']
        else:
            ml_weight = self.ml_weight
            angle_weight = self.angle_weight

        # Start with angle-only analysis
        hybrid_bet = angle_bet.copy()
        hybrid_bet['has_ml'] = False
        hybrid_bet['ml_agrees'] = False
        hybrid_bet['ml_confidence'] = 0.0
        hybrid_bet['hybrid_score'] = 0.0
        hybrid_bet['predicted_ev'] = 0.0  # Expected Value
        hybrid_bet['home_ev'] = 0.0
        hybrid_bet['away_ev'] = 0.0

        # Calculate angle contribution to score
        angle_score = angle_bet['expected_edge'] * angle_weight

        if ml_prediction is None:
            # No ML prediction available, use angle-only
            hybrid_bet['hybrid_score'] = angle_score
            hybrid_bet['prediction_type'] = 'ANGLE_ONLY'
            hybrid_bet['confidence'] = self._map_to_confidence(angle_bet['expected_edge'], angle_bet['angle_count'])
            return hybrid_bet

        # ML prediction available
        hybrid_bet['has_ml'] = True
        hybrid_bet['ml_confidence'] = ml_prediction['ml_confidence']

        # Extract Expected Value data
        hybrid_bet['predicted_ev'] = ml_prediction.get('predicted_ev', 0.0)
        hybrid_bet['home_ev'] = ml_prediction.get('home_ev', 0.0)
        hybrid_bet['away_ev'] = ml_prediction.get('away_ev', 0.0)

        # Determine which team angle bet recommends
        bet_text = angle_bet['bet']
        home_team = angle_bet['game'].split(' @ ')[1] if ' @ ' in angle_bet['game'] else ''
        away_team = angle_bet['game'].split(' @ ')[0] if ' @ ' in angle_bet['game'] else ''

        angle_pick_home = home_team in bet_text

        # Determine which team ML recommends
        ml_pick_home = ml_prediction['predicted_winner'] == ml_prediction['home_team']

        # Check agreement
        ml_agrees = (angle_pick_home == ml_pick_home)
        hybrid_bet['ml_agrees'] = ml_agrees

        # Calculate ML contribution
        # For NBA in ML-only mode, use EV instead of just ML confidence
        predicted_ev = ml_prediction.get('predicted_ev', 0.0)

        if predicted_ev > 0:
            # Use EV directly as the ML score (EV is already a good measure of value)
            ml_score = predicted_ev * ml_weight
        else:
            # Fallback to confidence-based scoring
            ml_edge = (ml_prediction['ml_confidence'] - 50.0) * 2
            ml_score = ml_edge * ml_weight

        # Combine scores
        base_score = angle_score + ml_score

        # Add agreement bonus if both agree
        if ml_agrees:
            hybrid_score = base_score + self.agreement_bonus
            hybrid_bet['prediction_type'] = 'HYBRID_AGREEMENT'
        else:
            # Disagreement - use average, penalized
            hybrid_score = base_score * 0.7  # 30% penalty for disagreement
            hybrid_bet['prediction_type'] = 'HYBRID_CONFLICT'

        hybrid_bet['hybrid_score'] = hybrid_score

        # Determine confidence level based on hybrid score
        hybrid_bet['confidence'] = self._calculate_hybrid_confidence(
            hybrid_score,
            ml_agrees,
            angle_bet['angle_count'],
            ml_prediction['ml_confidence'],
            hybrid_bet['predicted_ev']
        )

        return hybrid_bet

    def _calculate_hybrid_confidence(self, hybrid_score: float, ml_agrees: bool,
                                     angle_count: int, ml_confidence: float,
                                     predicted_ev: float = 0.0) -> str:
        """Calculate confidence level for hybrid prediction"""

        # Boost confidence for high positive EV
        if ml_agrees and predicted_ev > 50 and hybrid_score >= 35:
            return 'ELITE'
        elif ml_agrees and hybrid_score >= 40 and angle_count >= 2 and ml_confidence >= 65:
            return 'ELITE'
        elif ml_agrees and predicted_ev > 20 and hybrid_score >= 25:
            return 'HIGH'
        elif ml_agrees and hybrid_score >= 30:
            return 'HIGH'
        elif hybrid_score >= 25:
            return 'MEDIUM'
        elif hybrid_score >= 20:
            return 'LOW'
        else:
            return 'SKIP'

    def _map_to_confidence(self, edge: float, angle_count: int) -> str:
        """Map angle edge to confidence level (fallback when no ML)"""

        if edge >= 15 and angle_count >= 3:
            return 'ELITE'
        elif edge >= 12 and angle_count >= 2:
            return 'HIGH'
        elif edge >= 8:
            return 'MEDIUM'
        elif edge >= 5:
            return 'LOW'
        else:
            return 'SKIP'

    def should_recommend(self, hybrid_bet: Dict) -> bool:
        """Determine if hybrid bet meets recommendation threshold"""

        # CRITICAL: Must have positive Expected Value (for NBA only)
        # This prevents betting on favorites with no value
        # Only enforce EV requirement if ML prediction with EV is available
        sport = hybrid_bet.get('sport', '')
        predicted_ev = hybrid_bet.get('predicted_ev', 0.0)

        # For NBA with ML predictions, require positive EV
        if sport == 'NBA' and hybrid_bet.get('has_ml', False):
            if predicted_ev <= 0:
                return False

        # Must meet minimum hybrid score (relaxed for positive EV bets)
        min_score = 5.0 if predicted_ev > 0 else self.min_hybrid_score
        if hybrid_bet['hybrid_score'] < min_score:
            return False

        # If ML available, must meet ML threshold (unless positive EV overrides)
        if hybrid_bet['has_ml']:
            # For positive EV bets, ignore the ML confidence minimum
            if predicted_ev <= 0 and hybrid_bet['ml_confidence'] < self.min_ml_confidence:
                return False
        else:
            # No ML - must meet angle threshold
            if hybrid_bet['expected_edge'] < self.min_angle_edge:
                return False

        # Skip if confidence is too low
        if hybrid_bet['confidence'] == 'SKIP':
            return False

        return True

    def rank_bets(self, hybrid_bets: List[Dict]) -> List[Dict]:
        """Rank bets by hybrid score"""

        # Filter to recommended bets only
        recommended = [bet for bet in hybrid_bets if self.should_recommend(bet)]

        # Sort by hybrid score (descending)
        ranked = sorted(recommended, key=lambda x: x['hybrid_score'], reverse=True)

        return ranked

    def format_prediction(self, bet: Dict) -> str:
        """Format hybrid prediction for display"""

        lines = []

        # Game and bet
        lines.append(f"{bet['sport']}: {bet['game']}")
        lines.append(f"BET: {bet['bet']}")

        # Expected Value (CRITICAL - show first!)
        ev = bet.get('predicted_ev', 0.0)
        if ev > 0:
            lines.append(f"Expected Value: +{ev:.1f} ✅")
        elif ev < 0:
            lines.append(f"Expected Value: {ev:.1f} ❌")
        else:
            lines.append(f"Expected Value: {ev:.1f}")

        # Hybrid score
        lines.append(f"Hybrid Score: {bet['hybrid_score']:.1f}")

        # ML prediction
        if bet['has_ml']:
            agree_emoji = "✅" if bet['ml_agrees'] else "❌"
            lines.append(f"ML Prediction: {bet['ml_confidence']:.1f}% {agree_emoji}")

        # Angle edge
        lines.append(f"Angle Edge: +{bet['expected_edge']:.1f}%")

        # Prediction type
        type_map = {
            'HYBRID_AGREEMENT': '🔥 ML + Angles AGREE',
            'HYBRID_CONFLICT': '⚠️  ML + Angles CONFLICT',
            'ANGLE_ONLY': '📊 Angle-Based Only'
        }
        lines.append(type_map.get(bet['prediction_type'], bet['prediction_type']))

        # Confidence
        lines.append(f"Confidence: {bet['confidence']}")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test the hybrid predictor
    hybrid = HybridPredictor()

    # Mock angle bet
    angle_bet = {
        'sport': 'NBA',
        'game': 'Charlotte Hornets @ Milwaukee Bucks',
        'bet': 'Milwaukee Bucks ML',
        'expected_edge': 12.0,
        'angle_count': 2,
        'angles': []
    }

    # Mock ML prediction (agrees)
    ml_pred_agree = {
        'home_team': 'Milwaukee Bucks',
        'away_team': 'Charlotte Hornets',
        'predicted_winner': 'Milwaukee Bucks',
        'ml_confidence': 68.5
    }

    # Mock ML prediction (disagrees)
    ml_pred_conflict = {
        'home_team': 'Milwaukee Bucks',
        'away_team': 'Charlotte Hornets',
        'predicted_winner': 'Charlotte Hornets',
        'ml_confidence': 62.3
    }

    print("\n" + "="*80)
    print("TEST 1: ML + Angles AGREE")
    print("="*80)
    result1 = hybrid.combine_predictions(angle_bet, ml_pred_agree)
    print(hybrid.format_prediction(result1))

    print("\n" + "="*80)
    print("TEST 2: ML + Angles CONFLICT")
    print("="*80)
    result2 = hybrid.combine_predictions(angle_bet, ml_pred_conflict)
    print(hybrid.format_prediction(result2))

    print("\n" + "="*80)
    print("TEST 3: Angle-Only (No ML)")
    print("="*80)
    result3 = hybrid.combine_predictions(angle_bet, None)
    print(hybrid.format_prediction(result3))
