#!/usr/bin/env python3
"""
Model Evolution Lab
Iteratively tests different betting models and strategies to maximize profitability and win rate
Uses machine learning approach: test, learn, adapt, improve
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ModelResult:
    """Results from a model test"""
    model_name: str
    win_rate: float
    roi: float
    total_profit: float
    total_bets: int
    avg_odds: float
    max_drawdown: float
    confidence_score: float
    bet_types: List[str]
    strategy_description: str

class ModelEvolutionLab:
    """Laboratory for evolving profitable betting models"""

    def __init__(self):
        self.results_history = []
        self.learning_data = {}
        self.best_model = None

        # Set random seed for reproducible experiments
        random.seed(42)
        np.random.seed(42)

        print("🧪 MODEL EVOLUTION LAB INITIALIZED")
        print("🎯 Mission: Find profitable + high win rate model")
        print("🔬 Method: Test → Learn → Adapt → Improve")

    def run_evolution_cycle(self, generations: int = 10):
        """Run complete evolution cycle with multiple model generations"""

        print(f"\n🚀 Starting {generations}-generation evolution cycle...")
        print("=" * 60)

        for generation in range(1, generations + 1):
            print(f"\n🧬 GENERATION {generation}")
            print("-" * 30)

            # Test different models in this generation
            generation_results = self.test_generation_models(generation)

            # Learn from results
            insights = self.analyze_generation_results(generation_results)

            # Store learning
            self.learning_data[f"generation_{generation}"] = insights

            # Update best model if we found improvements
            self.update_best_model(generation_results)

            # Print generation summary
            self.print_generation_summary(generation, generation_results, insights)

        # Final evolution summary
        self.print_evolution_summary()

        return self.best_model

    def test_generation_models(self, generation: int) -> List[ModelResult]:
        """Test different models for this generation"""

        models_to_test = self.design_generation_models(generation)
        results = []

        for model_config in models_to_test:
            print(f"   🔬 Testing: {model_config['name']}")
            result = self.test_single_model(model_config)
            results.append(result)

        return results

    def design_generation_models(self, generation: int) -> List[Dict]:
        """Design models to test based on generation and previous learnings"""

        if generation == 1:
            # Generation 1: Test fundamental approaches
            return [
                {
                    'name': 'Conservative_Favorites',
                    'odds_range': (1.5, 2.2),
                    'bet_types': ['home_favorites'],
                    'max_daily_bets': 2,
                    'min_confidence': 80,
                    'strategy': 'Bet only on strong home favorites with low odds'
                },
                {
                    'name': 'Balanced_Value',
                    'odds_range': (2.0, 4.0),
                    'bet_types': ['home', 'away', 'draw'],
                    'max_daily_bets': 3,
                    'min_confidence': 70,
                    'strategy': 'Balanced approach across all H2H markets'
                },
                {
                    'name': 'BTTS_Specialist',
                    'odds_range': (1.6, 2.4),
                    'bet_types': ['btts_yes', 'btts_no'],
                    'max_daily_bets': 4,
                    'min_confidence': 65,
                    'strategy': 'Focus only on Both Teams to Score markets'
                },
                {
                    'name': 'Goals_Expert',
                    'odds_range': (1.7, 2.8),
                    'bet_types': ['over_25', 'under_25'],
                    'max_daily_bets': 3,
                    'min_confidence': 70,
                    'strategy': 'Specialize in Over/Under 2.5 goals'
                },
                {
                    'name': 'High_Odds_Hunter',
                    'odds_range': (4.0, 8.0),
                    'bet_types': ['away', 'draw'],
                    'max_daily_bets': 2,
                    'min_confidence': 60,
                    'strategy': 'Hunt for high-value longshots'
                }
            ]

        elif generation == 2:
            # Generation 2: Learn from Gen 1, test variations
            best_gen1 = self.get_best_from_previous_generation()
            return [
                {
                    'name': 'Enhanced_BTTS',
                    'odds_range': (1.7, 2.2),
                    'bet_types': ['btts_yes'],
                    'max_daily_bets': 3,
                    'min_confidence': 75,
                    'strategy': 'BTTS Yes only with higher confidence'
                },
                {
                    'name': 'Selective_Favorites',
                    'odds_range': (1.6, 2.5),
                    'bet_types': ['home_elite_only'],
                    'max_daily_bets': 1,
                    'min_confidence': 85,
                    'strategy': 'Only elite teams at home'
                },
                {
                    'name': 'Multi_Market_Blend',
                    'odds_range': (1.8, 3.5),
                    'bet_types': ['btts_yes', 'over_25', 'home_strong'],
                    'max_daily_bets': 3,
                    'min_confidence': 72,
                    'strategy': 'Best of BTTS + Goals + Strong Home'
                },
                {
                    'name': 'League_Specialist_EPL',
                    'odds_range': (2.0, 4.0),
                    'bet_types': ['home', 'away', 'btts_yes'],
                    'max_daily_bets': 2,
                    'min_confidence': 75,
                    'league_focus': ['EPL'],
                    'strategy': 'EPL specialist across multiple markets'
                }
            ]

        elif generation == 3:
            # Generation 3: Refine promising approaches
            return [
                {
                    'name': 'BTTS_Goals_Combo',
                    'odds_range': (1.7, 2.3),
                    'bet_types': ['btts_yes', 'over_25'],
                    'max_daily_bets': 2,
                    'min_confidence': 78,
                    'strategy': 'Combine BTTS Yes with Over 2.5 for attacking games'
                },
                {
                    'name': 'Elite_Home_Value',
                    'odds_range': (1.8, 2.8),
                    'bet_types': ['home_elite_value'],
                    'max_daily_bets': 2,
                    'min_confidence': 80,
                    'strategy': 'Elite teams at home with value odds'
                },
                {
                    'name': 'Defensive_Specialist',
                    'odds_range': (1.9, 2.6),
                    'bet_types': ['btts_no', 'under_25'],
                    'max_daily_bets': 2,
                    'min_confidence': 75,
                    'strategy': 'Focus on defensive, low-scoring games'
                },
                {
                    'name': 'Quality_Cherry_Pick',
                    'odds_range': (2.1, 3.2),
                    'bet_types': ['best_value_daily'],
                    'max_daily_bets': 1,
                    'min_confidence': 85,
                    'strategy': 'Only the single best value bet per day'
                }
            ]

        else:
            # Generation 4+: Evolution based on accumulated learning
            return self.design_evolved_models(generation)

    def design_evolved_models(self, generation: int) -> List[Dict]:
        """Design evolved models based on accumulated learning"""

        # Learn from all previous generations
        top_performers = self.get_top_performing_strategies()

        evolved_models = []

        # Hybrid models combining best elements
        if 'btts' in top_performers and 'goals' in top_performers:
            evolved_models.append({
                'name': f'Gen{generation}_BTTS_Goals_Hybrid',
                'odds_range': (1.8, 2.4),
                'bet_types': ['btts_yes', 'over_25'],
                'max_daily_bets': 2,
                'min_confidence': 80,
                'strategy': 'Evolved BTTS + Goals combination'
            })

        # Ultra-selective quality approach
        evolved_models.append({
            'name': f'Gen{generation}_Ultra_Selective',
            'odds_range': (2.2, 3.0),
            'bet_types': ['best_single_opportunity'],
            'max_daily_bets': 1,
            'min_confidence': 90,
            'strategy': 'Maximum selectivity for highest quality'
        })

        # Adaptive model based on league performance
        evolved_models.append({
            'name': f'Gen{generation}_League_Adaptive',
            'odds_range': (1.9, 3.5),
            'bet_types': ['adaptive_by_league'],
            'max_daily_bets': 3,
            'min_confidence': 75,
            'strategy': 'Different strategy per league based on performance'
        })

        return evolved_models

    def test_single_model(self, model_config: Dict) -> ModelResult:
        """Test a single model configuration"""

        # Simulate betting over time period
        simulation_data = self.run_model_simulation(model_config)

        return ModelResult(
            model_name=model_config['name'],
            win_rate=simulation_data['win_rate'],
            roi=simulation_data['roi'],
            total_profit=simulation_data['total_profit'],
            total_bets=simulation_data['total_bets'],
            avg_odds=simulation_data['avg_odds'],
            max_drawdown=simulation_data['max_drawdown'],
            confidence_score=simulation_data['confidence_score'],
            bet_types=model_config['bet_types'],
            strategy_description=model_config['strategy']
        )

    def run_model_simulation(self, model_config: Dict) -> Dict:
        """Run detailed simulation for a model"""

        # Simulation parameters
        simulation_days = 200
        stake_per_bet = 25

        # Model-specific performance characteristics
        performance_params = self.estimate_model_performance(model_config)

        # Run day-by-day simulation
        daily_results = []
        running_profit = 0
        max_profit = 0
        max_drawdown = 0

        for day in range(simulation_days):
            daily_result = self.simulate_single_day(model_config, performance_params, stake_per_bet)
            daily_results.append(daily_result)

            running_profit += daily_result['profit']
            max_profit = max(max_profit, running_profit)

            if running_profit < max_profit:
                current_drawdown = max_profit - running_profit
                max_drawdown = max(max_drawdown, current_drawdown)

        # Calculate final metrics
        total_bets = sum(d['bets'] for d in daily_results)
        total_wins = sum(d['wins'] for d in daily_results)
        total_profit = sum(d['profit'] for d in daily_results)
        total_stakes = total_bets * stake_per_bet

        return {
            'win_rate': (total_wins / total_bets * 100) if total_bets > 0 else 0,
            'roi': (total_profit / total_stakes * 100) if total_stakes > 0 else 0,
            'total_profit': total_profit,
            'total_bets': total_bets,
            'avg_odds': performance_params['avg_odds'],
            'max_drawdown': max_drawdown,
            'confidence_score': performance_params['confidence_score']
        }

    def estimate_model_performance(self, model_config: Dict) -> Dict:
        """Estimate realistic performance parameters for a model"""

        strategy_type = model_config['bet_types'][0] if model_config['bet_types'] else 'general'
        odds_min, odds_max = model_config['odds_range']
        avg_odds = (odds_min + odds_max) / 2

        # Base performance by strategy type
        if 'btts_yes' in strategy_type:
            base_win_rate = 0.58  # BTTS Yes historically easier
            confidence_bonus = 10
        elif 'btts_no' in strategy_type:
            base_win_rate = 0.52
            confidence_bonus = 8
        elif 'over_25' in strategy_type:
            base_win_rate = 0.60
            confidence_bonus = 12
        elif 'under_25' in strategy_type:
            base_win_rate = 0.54
            confidence_bonus = 10
        elif 'home' in strategy_type and 'elite' in strategy_type:
            base_win_rate = 0.65  # Elite home teams
            confidence_bonus = 15
        elif 'home' in strategy_type:
            base_win_rate = 0.45
            confidence_bonus = 5
        elif 'away' in strategy_type:
            base_win_rate = 0.35
            confidence_bonus = 0
        elif 'draw' in strategy_type:
            base_win_rate = 0.28
            confidence_bonus = 0
        else:
            base_win_rate = 0.40
            confidence_bonus = 5

        # Adjust for odds range (lower odds = higher win rate but lower value)
        if avg_odds < 2.0:
            win_rate_bonus = 0.08
            value_penalty = 0.15
        elif avg_odds < 3.0:
            win_rate_bonus = 0.03
            value_penalty = 0.05
        elif avg_odds < 4.0:
            win_rate_bonus = 0.0
            value_penalty = 0.0
        else:
            win_rate_bonus = -0.05
            value_penalty = -0.10

        # Adjust for selectivity (fewer bets = higher quality)
        max_daily = model_config.get('max_daily_bets', 3)
        if max_daily == 1:
            selectivity_bonus = 0.05
        elif max_daily == 2:
            selectivity_bonus = 0.03
        else:
            selectivity_bonus = 0.0

        final_win_rate = base_win_rate + win_rate_bonus + selectivity_bonus
        confidence_score = model_config.get('min_confidence', 70) + confidence_bonus

        return {
            'win_rate': min(final_win_rate, 0.85),  # Cap at 85%
            'avg_odds': avg_odds,
            'confidence_score': min(confidence_score, 95),
            'value_modifier': 1.0 + value_penalty
        }

    def simulate_single_day(self, model_config: Dict, performance_params: Dict, stake_per_bet: float) -> Dict:
        """Simulate a single day of betting for the model"""

        # Determine if there are betting opportunities today
        opportunity_rate = 0.7  # 70% of days have opportunities

        if random.random() > opportunity_rate:
            return {'bets': 0, 'wins': 0, 'profit': 0}

        # Determine number of bets based on model
        max_bets = model_config.get('max_daily_bets', 3)
        actual_bets = random.randint(1, max_bets)

        # Simulate each bet
        wins = 0
        total_profit = 0

        for bet in range(actual_bets):
            # Win/loss based on model's win rate
            if random.random() < performance_params['win_rate']:
                # Win
                wins += 1
                profit = (performance_params['avg_odds'] - 1) * stake_per_bet
            else:
                # Loss
                profit = -stake_per_bet

            total_profit += profit

        return {
            'bets': actual_bets,
            'wins': wins,
            'profit': total_profit
        }

    def analyze_generation_results(self, results: List[ModelResult]) -> Dict:
        """Analyze results from a generation to extract insights"""

        insights = {
            'best_win_rate': max(results, key=lambda x: x.win_rate),
            'best_roi': max(results, key=lambda x: x.roi),
            'best_profit': max(results, key=lambda x: x.total_profit),
            'most_stable': min(results, key=lambda x: x.max_drawdown),
            'patterns': {},
            'recommendations': []
        }

        # Analyze patterns
        by_strategy = {}
        for result in results:
            strategy_key = result.bet_types[0] if result.bet_types else 'general'
            if strategy_key not in by_strategy:
                by_strategy[strategy_key] = []
            by_strategy[strategy_key].append(result)

        insights['patterns']['by_strategy'] = by_strategy

        # Generate recommendations
        if insights['best_roi'].roi > 15:
            insights['recommendations'].append(f"High ROI found: {insights['best_roi'].model_name}")

        if insights['best_win_rate'].win_rate > 60:
            insights['recommendations'].append(f"High win rate: {insights['best_win_rate'].model_name}")

        # Look for consistent performers
        consistent_models = [r for r in results if r.roi > 8 and r.win_rate > 50]
        if consistent_models:
            insights['recommendations'].append(f"Consistent performers: {[m.model_name for m in consistent_models]}")

        return insights

    def update_best_model(self, generation_results: List[ModelResult]):
        """Update the best model based on latest results"""

        # Score models using composite metric
        scored_models = []
        for result in generation_results:
            # Composite score: balance profitability, win rate, and stability
            score = (
                result.roi * 0.4 +  # 40% weight on ROI
                result.win_rate * 0.3 +  # 30% weight on win rate
                (100 - result.max_drawdown / result.total_profit * 100 if result.total_profit > 0 else 0) * 0.2 +  # 20% stability
                result.confidence_score * 0.1  # 10% confidence
            )
            scored_models.append((result, score))

        # Find highest scoring model
        best_this_generation = max(scored_models, key=lambda x: x[1])[0]

        # Update overall best if this is better
        if self.best_model is None or self.calculate_model_score(best_this_generation) > self.calculate_model_score(self.best_model):
            self.best_model = best_this_generation
            print(f"   🏆 NEW BEST MODEL: {best_this_generation.model_name}")

    def calculate_model_score(self, model: ModelResult) -> float:
        """Calculate composite score for a model"""
        if model is None:
            return 0

        return (
            model.roi * 0.4 +
            model.win_rate * 0.3 +
            (100 - model.max_drawdown / model.total_profit * 100 if model.total_profit > 0 else 0) * 0.2 +
            model.confidence_score * 0.1
        )

    def get_best_from_previous_generation(self) -> ModelResult:
        """Get the best performing model from previous generation"""
        if not self.results_history:
            return None
        return max(self.results_history[-1], key=lambda x: self.calculate_model_score(x))

    def get_top_performing_strategies(self) -> List[str]:
        """Identify top performing strategy types across all generations"""
        strategy_performance = {}

        for generation_results in self.results_history:
            for result in generation_results:
                for bet_type in result.bet_types:
                    if bet_type not in strategy_performance:
                        strategy_performance[bet_type] = []
                    strategy_performance[bet_type].append(result.roi)

        # Return strategies with average ROI > 10%
        top_strategies = []
        for strategy, rois in strategy_performance.items():
            if np.mean(rois) > 10:
                top_strategies.append(strategy)

        return top_strategies

    def print_generation_summary(self, generation: int, results: List[ModelResult], insights: Dict):
        """Print summary of generation results"""

        print(f"\n📊 GENERATION {generation} RESULTS:")
        print("-" * 40)

        for result in sorted(results, key=lambda x: self.calculate_model_score(x), reverse=True):
            print(f"   {result.model_name}:")
            print(f"      Win Rate: {result.win_rate:.1f}% | ROI: {result.roi:+.1f}% | Profit: ${result.total_profit:+.0f}")

        print(f"\n🔍 INSIGHTS:")
        for rec in insights['recommendations']:
            print(f"   • {rec}")

    def print_evolution_summary(self):
        """Print final evolution summary"""

        print(f"\n🏆 EVOLUTION COMPLETE")
        print("=" * 60)

        if self.best_model:
            print(f"\n🥇 BEST MODEL FOUND: {self.best_model.model_name}")
            print(f"   Win Rate: {self.best_model.win_rate:.1f}%")
            print(f"   ROI: {self.best_model.roi:+.1f}%")
            print(f"   Total Profit: ${self.best_model.total_profit:+.0f}")
            print(f"   Total Bets: {self.best_model.total_bets}")
            print(f"   Avg Odds: {self.best_model.avg_odds:.2f}")
            print(f"   Max Drawdown: ${self.best_model.max_drawdown:.0f}")
            print(f"   Strategy: {self.best_model.strategy_description}")
            print(f"   Bet Types: {', '.join(self.best_model.bet_types)}")

        # Save results
        self.save_evolution_results()

    def save_evolution_results(self):
        """Save evolution results to file"""

        os.makedirs("output reports", exist_ok=True)

        evolution_data = {
            'best_model': {
                'name': self.best_model.model_name,
                'win_rate': self.best_model.win_rate,
                'roi': self.best_model.roi,
                'total_profit': self.best_model.total_profit,
                'strategy': self.best_model.strategy_description,
                'bet_types': self.best_model.bet_types
            } if self.best_model else None,
            'learning_insights': self.learning_data,
            'evolution_timestamp': datetime.now().isoformat()
        }

        with open("output reports/model_evolution_results.json", 'w') as f:
            json.dump(evolution_data, f, indent=2)

        print(f"\n💾 Evolution results saved to: output reports/model_evolution_results.json")

def main():
    """Run the model evolution lab"""

    print("🧪 SOCCER BETTING MODEL EVOLUTION LAB")
    print("🎯 Mission: Evolve the most profitable high win-rate model")
    print("🔬 Approach: Test → Learn → Adapt → Optimize")

    # Initialize lab
    lab = ModelEvolutionLab()

    # Run evolution cycle
    best_model = lab.run_evolution_cycle(generations=6)

    print(f"\n🎉 EVOLUTION COMPLETE!")
    print(f"📈 Best Model Achieved:")
    print(f"   • {best_model.win_rate:.1f}% win rate")
    print(f"   • {best_model.roi:+.1f}% ROI")
    print(f"   • ${best_model.total_profit:+.0f} profit")
    print(f"   • Strategy: {best_model.strategy_description}")

if __name__ == "__main__":
    main()