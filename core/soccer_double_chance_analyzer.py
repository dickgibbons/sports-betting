#!/usr/bin/env python3
"""
Soccer Double Chance Bet Analyzer
Calculates and compares expected value for standard moneyline vs double chance bets
"""

from typing import Dict, Optional, Tuple, List
import json


class SoccerDoubleChanceAnalyzer:
    """
    Analyzes double chance betting opportunities for soccer matches

    Double Chance bets cover 2 of 3 possible outcomes:
    - 1X: Home Win OR Draw
    - X2: Draw OR Away Win
    - 12: Home Win OR Away Win (no draw)
    """

    def __init__(self):
        """Initialize double chance analyzer"""
        self.min_edge = 3.0  # Minimum 3% edge for recommendation
        print("⚽ Soccer Double Chance Analyzer initialized")

    def calculate_double_chance_probabilities(self,
                                             home_win_prob: float,
                                             draw_prob: float,
                                             away_win_prob: float) -> Dict[str, float]:
        """
        Calculate double chance probabilities from match outcome probabilities

        Args:
            home_win_prob: Probability of home win (0-1)
            draw_prob: Probability of draw (0-1)
            away_win_prob: Probability of away win (0-1)

        Returns:
            Dictionary with double chance probabilities
        """
        # Normalize probabilities to ensure they sum to 1.0
        total = home_win_prob + draw_prob + away_win_prob
        if total > 0:
            home_win_prob /= total
            draw_prob /= total
            away_win_prob /= total

        return {
            # Standard outcomes
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,

            # Double chance outcomes
            '1X': home_win_prob + draw_prob,  # Home OR Draw
            'X2': draw_prob + away_win_prob,  # Draw OR Away
            '12': home_win_prob + away_win_prob  # Home OR Away (no draw)
        }

    def calculate_expected_value(self, probability: float, odds: float) -> float:
        """
        Calculate expected value for a bet

        Args:
            probability: Win probability (0-1)
            odds: Decimal odds (e.g., 1.50, 2.00)

        Returns:
            Expected value as percentage
        """
        if odds <= 1.0:
            return 0.0

        # EV = (probability * (odds - 1)) - (1 - probability)
        # Simplified: EV = (probability * odds) - 1
        ev = (probability * odds) - 1.0
        return ev * 100  # Convert to percentage

    def analyze_match(self,
                     home_win_prob: float,
                     draw_prob: float,
                     away_win_prob: float,
                     odds: Dict[str, float]) -> Dict:
        """
        Analyze all betting options for a match (ML + DC)

        Args:
            home_win_prob: ML home win probability
            draw_prob: ML draw probability
            away_win_prob: ML away win probability
            odds: Dictionary with all available odds:
                  {'home': 2.10, 'draw': 3.40, 'away': 3.50,
                   '1X': 1.30, 'X2': 1.75, '12': 1.40}

        Returns:
            Analysis dictionary with best bet recommendation
        """
        # Calculate all probabilities
        probs = self.calculate_double_chance_probabilities(
            home_win_prob, draw_prob, away_win_prob
        )

        # Calculate EV for all bet types
        bet_analysis = []

        # Moneyline bets
        if 'home' in odds:
            ev = self.calculate_expected_value(probs['home_win'], odds['home'])
            bet_analysis.append({
                'bet_type': 'Home Win (1)',
                'probability': probs['home_win'],
                'odds': odds['home'],
                'expected_value': ev,
                'bet_class': 'moneyline'
            })

        if 'draw' in odds:
            ev = self.calculate_expected_value(probs['draw'], odds['draw'])
            bet_analysis.append({
                'bet_type': 'Draw (X)',
                'probability': probs['draw'],
                'odds': odds['draw'],
                'expected_value': ev,
                'bet_class': 'moneyline'
            })

        if 'away' in odds:
            ev = self.calculate_expected_value(probs['away_win'], odds['away'])
            bet_analysis.append({
                'bet_type': 'Away Win (2)',
                'probability': probs['away_win'],
                'odds': odds['away'],
                'expected_value': ev,
                'bet_class': 'moneyline'
            })

        # Double chance bets
        if '1X' in odds:
            ev = self.calculate_expected_value(probs['1X'], odds['1X'])
            bet_analysis.append({
                'bet_type': 'Home/Draw (1X)',
                'probability': probs['1X'],
                'odds': odds['1X'],
                'expected_value': ev,
                'bet_class': 'double_chance'
            })

        if 'X2' in odds:
            ev = self.calculate_expected_value(probs['X2'], odds['X2'])
            bet_analysis.append({
                'bet_type': 'Draw/Away (X2)',
                'probability': probs['X2'],
                'odds': odds['X2'],
                'expected_value': ev,
                'bet_class': 'double_chance'
            })

        if '12' in odds:
            ev = self.calculate_expected_value(probs['12'], odds['12'])
            bet_analysis.append({
                'bet_type': 'Home/Away (12)',
                'probability': probs['12'],
                'odds': odds['12'],
                'expected_value': ev,
                'bet_class': 'double_chance'
            })

        # Sort by expected value (highest first)
        bet_analysis.sort(key=lambda x: x['expected_value'], reverse=True)

        # Determine best bet
        best_bet = bet_analysis[0] if bet_analysis else None

        # Determine confidence level
        confidence = 'NONE'
        if best_bet and best_bet['expected_value'] >= self.min_edge:
            if best_bet['expected_value'] >= 10.0:
                confidence = 'HIGH'
            elif best_bet['expected_value'] >= 6.0:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

        return {
            'probabilities': probs,
            'all_bets': bet_analysis,
            'best_bet': best_bet,
            'confidence': confidence,
            'has_value': best_bet and best_bet['expected_value'] >= self.min_edge
        }

    def compare_moneyline_vs_double_chance(self,
                                          home_win_prob: float,
                                          draw_prob: float,
                                          away_win_prob: float,
                                          ml_odds: Dict[str, float],
                                          dc_odds: Dict[str, float]) -> Dict:
        """
        Direct comparison between moneyline and double chance betting

        Args:
            home_win_prob: Home win probability
            draw_prob: Draw probability
            away_win_prob: Away win probability
            ml_odds: {'home': 2.10, 'draw': 3.40, 'away': 3.50}
            dc_odds: {'1X': 1.30, 'X2': 1.75, '12': 1.40}

        Returns:
            Comparison analysis with recommendation
        """
        # Combine all odds
        all_odds = {**ml_odds, **dc_odds}

        # Run full analysis
        analysis = self.analyze_match(
            home_win_prob, draw_prob, away_win_prob, all_odds
        )

        # Separate ML and DC options
        ml_bets = [b for b in analysis['all_bets'] if b['bet_class'] == 'moneyline']
        dc_bets = [b for b in analysis['all_bets'] if b['bet_class'] == 'double_chance']

        best_ml = ml_bets[0] if ml_bets else None
        best_dc = dc_bets[0] if dc_bets else None

        # Determine recommendation
        recommendation = None
        if best_ml and best_dc:
            if best_ml['expected_value'] > best_dc['expected_value']:
                recommendation = {
                    'choice': 'moneyline',
                    'reason': f"ML has {best_ml['expected_value']:.1f}% EV vs DC {best_dc['expected_value']:.1f}% EV",
                    'bet': best_ml
                }
            else:
                recommendation = {
                    'choice': 'double_chance',
                    'reason': f"DC has {best_dc['expected_value']:.1f}% EV vs ML {best_ml['expected_value']:.1f}% EV",
                    'bet': best_dc
                }
        elif best_ml:
            recommendation = {'choice': 'moneyline', 'bet': best_ml}
        elif best_dc:
            recommendation = {'choice': 'double_chance', 'bet': best_dc}

        return {
            **analysis,
            'best_moneyline': best_ml,
            'best_double_chance': best_dc,
            'recommendation': recommendation
        }

    def format_analysis_for_report(self, analysis: Dict,
                                   home_team: str, away_team: str) -> str:
        """
        Format analysis for daily betting report

        Args:
            analysis: Analysis dictionary from analyze_match()
            home_team: Home team name
            away_team: Away team name

        Returns:
            Formatted string for report
        """
        if not analysis.get('has_value'):
            return ""

        best = analysis['best_bet']

        output = f"\n{'='*70}\n"
        output += f"{away_team} @ {home_team}\n"
        output += f"{'='*70}\n\n"

        output += f"RECOMMENDED BET: {best['bet_type']}\n"
        output += f"  Odds: {best['odds']:.2f}\n"
        output += f"  Win Probability: {best['probability']*100:.1f}%\n"
        output += f"  Expected Value: {best['expected_value']:+.2f}%\n"
        output += f"  Confidence: {analysis['confidence']}\n\n"

        # Show all options
        output += "ALL BETTING OPTIONS:\n"
        output += f"{'Bet Type':<20} {'Prob':<8} {'Odds':<8} {'EV':<10}\n"
        output += f"{'-'*50}\n"

        for bet in analysis['all_bets']:
            output += f"{bet['bet_type']:<20} "
            output += f"{bet['probability']*100:>6.1f}% "
            output += f"{bet['odds']:>6.2f} "
            output += f"{bet['expected_value']:>+8.2f}%\n"

        return output


def test_double_chance_analyzer():
    """Test the double chance analyzer with example scenarios"""

    analyzer = SoccerDoubleChanceAnalyzer()

    print("\n" + "="*80)
    print("SCENARIO 1: Heavy Favorite (Man City vs Sheffield Utd)")
    print("="*80)

    # Man City heavily favored
    analysis1 = analyzer.analyze_match(
        home_win_prob=0.75,
        draw_prob=0.15,
        away_win_prob=0.10,
        odds={
            'home': 1.30,   # Man City ML
            'draw': 6.50,
            'away': 11.00,
            '1X': 1.10,     # Man City or Draw
            'X2': 4.20,
            '12': 1.20      # Someone wins
        }
    )

    print(analyzer.format_analysis_for_report(
        analysis1, "Man City", "Sheffield Utd"
    ))

    print("\n" + "="*80)
    print("SCENARIO 2: Even Match (Liverpool vs Arsenal)")
    print("="*80)

    # Evenly matched teams
    analysis2 = analyzer.analyze_match(
        home_win_prob=0.40,
        draw_prob=0.30,
        away_win_prob=0.30,
        odds={
            'home': 2.40,   # Liverpool
            'draw': 3.30,
            'away': 2.90,   # Arsenal
            '1X': 1.44,     # Liverpool or Draw
            'X2': 1.62,     # Draw or Arsenal
            '12': 1.36      # No draw
        }
    )

    print(analyzer.format_analysis_for_report(
        analysis2, "Liverpool", "Arsenal"
    ))

    print("\n" + "="*80)
    print("SCENARIO 3: Comparison Test")
    print("="*80)

    comparison = analyzer.compare_moneyline_vs_double_chance(
        home_win_prob=0.55,
        draw_prob=0.25,
        away_win_prob=0.20,
        ml_odds={'home': 1.85, 'draw': 3.60, 'away': 4.50},
        dc_odds={'1X': 1.25, 'X2': 1.90, '12': 1.30}
    )

    if comparison['recommendation']:
        rec = comparison['recommendation']
        print(f"\nRECOMMENDATION: {rec['choice'].upper()}")
        print(f"Reason: {rec['reason']}")
        print(f"\nBet: {rec['bet']['bet_type']}")
        print(f"  Odds: {rec['bet']['odds']:.2f}")
        print(f"  Expected Value: {rec['bet']['expected_value']:+.2f}%")


if __name__ == "__main__":
    test_double_chance_analyzer()
