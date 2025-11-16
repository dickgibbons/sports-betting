#!/usr/bin/env python3
"""
Create downloadable CSV report for today's soccer betting analysis
"""

import json
import pandas as pd
from datetime import datetime
import os

def create_todays_betting_csv():
    """Create comprehensive CSV reports from today's betting analysis"""

    print("📊 CREATING DOWNLOADABLE CSV REPORTS")
    print("="*50)

    # Load today's analysis
    try:
        with open('output reports/optimal_model_analysis.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: No analysis data found. Please run the optimal profit model first.")
        return

    selected_bets = data['selected_bets']
    analysis_summary = data['analysis_summary']
    timestamp = data.get('timestamp', datetime.now().isoformat())

    print(f"📋 Found {len(selected_bets)} selected bets to process")

    # Create detailed bets DataFrame
    if selected_bets:
        bets_df = pd.DataFrame(selected_bets)

        # Add calculated fields
        bets_df['potential_profit'] = (bets_df['odds'] - 1) * bets_df['stake']
        bets_df['potential_return'] = bets_df['odds'] * bets_df['stake']
        bets_df['risk_amount'] = bets_df['stake']
        bets_df['date'] = datetime.now().strftime('%Y-%m-%d')
        bets_df['time_analyzed'] = datetime.now().strftime('%H:%M:%S')

        # Add betting strategy information
        bets_df['strategy_type'] = bets_df['type'].str.replace('_', ' ').str.title()
        bets_df['confidence_level'] = bets_df['confidence'].apply(lambda x:
            'Very High' if x >= 90 else 'High' if x >= 80 else 'Medium' if x >= 70 else 'Low')

        # Reorder columns for better readability
        columns_order = [
            'date', 'time_analyzed', 'match', 'league', 'market', 'selection',
            'odds', 'stake', 'risk_amount', 'potential_profit', 'potential_return',
            'expected_roi', 'confidence', 'confidence_level', 'strategy_type',
            'type', 'reasoning'
        ]

        # Only include columns that exist in the DataFrame
        available_columns = [col for col in columns_order if col in bets_df.columns]
        bets_df = bets_df[available_columns]

    else:
        # Create empty DataFrame with proper structure
        bets_df = pd.DataFrame(columns=[
            'date', 'time_analyzed', 'match', 'league', 'market', 'selection',
            'odds', 'stake', 'risk_amount', 'potential_profit', 'potential_return',
            'expected_roi', 'confidence', 'confidence_level', 'strategy_type',
            'type', 'reasoning'
        ])

    # Create summary DataFrame
    total_stake = bets_df['stake'].sum() if not bets_df.empty else 0
    total_potential_profit = bets_df['potential_profit'].sum() if not bets_df.empty else 0
    total_potential_return = bets_df['potential_return'].sum() if not bets_df.empty else 0
    portfolio_roi = (total_potential_profit / total_stake * 100) if total_stake > 0 else 0

    summary_data = {
        'date': [datetime.now().strftime('%Y-%m-%d')],
        'analysis_time': [datetime.now().strftime('%H:%M:%S')],
        'total_opportunities_found': [analysis_summary.get('total_opportunities', 0)],
        'bets_selected': [analysis_summary.get('selected_count', 0)],
        'total_stake': [total_stake],
        'total_potential_profit': [total_potential_profit],
        'total_potential_return': [total_potential_return],
        'expected_total_roi': [analysis_summary.get('expected_total_roi', 0)],
        'portfolio_roi_percent': [portfolio_roi],
        'risk_assessment': [analysis_summary.get('risk_assessment', 'Unknown')],
        'model_version': ['Multi-Strategy Profit Maximizer v1.0'],
        'data_source': ['API-Sports with real fixture data'],
        'max_daily_bets': [3],
        'min_roi_threshold': ['15%']
    }

    # Add strategy breakdown
    strategy_breakdown = analysis_summary.get('strategy_breakdown', {})
    for strategy, count in strategy_breakdown.items():
        summary_data[f'{strategy}_bets'] = [count]

    summary_df = pd.DataFrame(summary_data)

    # Create file names with today's date
    today_str = datetime.now().strftime('%Y%m%d')
    timestamp_str = datetime.now().strftime('%H%M%S')

    bets_filename = f'output reports/todays_bets_{today_str}_{timestamp_str}.csv'
    summary_filename = f'output reports/portfolio_summary_{today_str}_{timestamp_str}.csv'

    # Save CSV files
    try:
        bets_df.to_csv(bets_filename, index=False)
        summary_df.to_csv(summary_filename, index=False)

        print(f"✅ Detailed bets saved: {bets_filename}")
        print(f"✅ Portfolio summary saved: {summary_filename}")

        # Display the data
        print("\n📊 TODAY'S BETTING OPPORTUNITIES CSV:")
        print("=" * 80)
        if not bets_df.empty:
            # Show key columns only for display
            display_columns = ['match', 'market', 'odds', 'stake', 'potential_profit', 'expected_roi', 'confidence']
            display_df = bets_df[display_columns] if all(col in bets_df.columns for col in display_columns) else bets_df
            print(display_df.to_string(index=False))
        else:
            print("No betting opportunities selected today")

        print(f"\n📈 PORTFOLIO SUMMARY CSV:")
        print("=" * 50)
        # Show key summary metrics
        key_summary_columns = ['date', 'bets_selected', 'total_stake', 'total_potential_profit',
                              'portfolio_roi_percent', 'risk_assessment']
        display_summary = summary_df[key_summary_columns] if all(col in summary_df.columns for col in key_summary_columns) else summary_df
        print(display_summary.to_string(index=False))

        # Create a combined report with both datasets
        combined_filename = f'output reports/complete_betting_report_{today_str}_{timestamp_str}.csv'

        # Add headers to distinguish sections
        with open(combined_filename, 'w') as f:
            f.write("SOCCER BETTING ANALYSIS REPORT\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Model: Multi-Strategy Profit Maximizer v1.0\n")
            f.write("Data Source: API-Sports (Real Fixture Data)\n")
            f.write("\n")

            f.write("PORTFOLIO SUMMARY\n")
            f.write("================\n")
            summary_df.to_csv(f, index=False)
            f.write("\n")

            f.write("INDIVIDUAL BETS\n")
            f.write("===============\n")
            bets_df.to_csv(f, index=False)

        print(f"✅ Combined report saved: {combined_filename}")

        return {
            'bets_file': bets_filename,
            'summary_file': summary_filename,
            'combined_file': combined_filename,
            'bets_count': len(bets_df),
            'total_stake': total_stake,
            'potential_profit': total_potential_profit
        }

    except Exception as e:
        print(f"❌ Error saving CSV files: {e}")
        return None

def generate_betting_metrics_csv():
    """Generate additional metrics CSV for deeper analysis"""

    print(f"\n📈 GENERATING ADDITIONAL METRICS CSV...")

    try:
        with open('output reports/optimal_model_analysis.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No analysis data found")
        return None

    # Create metrics breakdown
    metrics_data = []

    selected_bets = data.get('selected_bets', [])
    analysis_summary = data.get('analysis_summary', {})

    # Overall metrics
    metrics_data.append({
        'metric_type': 'Portfolio',
        'metric_name': 'Total Opportunities',
        'value': analysis_summary.get('total_opportunities', 0),
        'unit': 'matches',
        'category': 'Coverage'
    })

    metrics_data.append({
        'metric_type': 'Portfolio',
        'metric_name': 'Selection Rate',
        'value': round((analysis_summary.get('selected_count', 0) / max(analysis_summary.get('total_opportunities', 1), 1)) * 100, 1),
        'unit': 'percent',
        'category': 'Selectivity'
    })

    # Individual bet metrics
    for i, bet in enumerate(selected_bets, 1):
        metrics_data.extend([
            {
                'metric_type': f'Bet_{i}',
                'metric_name': 'Match',
                'value': bet.get('match', 'Unknown'),
                'unit': 'text',
                'category': 'Match Info'
            },
            {
                'metric_type': f'Bet_{i}',
                'metric_name': 'Expected ROI',
                'value': round(bet.get('expected_roi', 0), 1),
                'unit': 'percent',
                'category': 'Returns'
            },
            {
                'metric_type': f'Bet_{i}',
                'metric_name': 'Confidence',
                'value': round(bet.get('confidence', 0), 1),
                'unit': 'percent',
                'category': 'Confidence'
            },
            {
                'metric_type': f'Bet_{i}',
                'metric_name': 'Risk Level',
                'value': 'Low' if bet.get('confidence', 0) >= 80 else 'Medium' if bet.get('confidence', 0) >= 70 else 'High',
                'unit': 'category',
                'category': 'Risk'
            }
        ])

    metrics_df = pd.DataFrame(metrics_data)

    today_str = datetime.now().strftime('%Y%m%d')
    timestamp_str = datetime.now().strftime('%H%M%S')
    metrics_filename = f'output reports/betting_metrics_{today_str}_{timestamp_str}.csv'

    metrics_df.to_csv(metrics_filename, index=False)
    print(f"✅ Betting metrics saved: {metrics_filename}")

    return metrics_filename

def main():
    """Create all CSV reports for today's analysis"""

    print("🚀 CSV REPORT GENERATOR")
    print("📅 Creating downloadable reports for today's betting analysis")

    # Create main betting reports
    result = create_todays_betting_csv()

    if result:
        print(f"\n✅ SUCCESS! CSV reports created:")
        print(f"   📊 Individual bets: {result['bets_file']}")
        print(f"   📈 Portfolio summary: {result['summary_file']}")
        print(f"   📋 Combined report: {result['combined_file']}")

        # Create additional metrics
        metrics_file = generate_betting_metrics_csv()
        if metrics_file:
            print(f"   📏 Betting metrics: {metrics_file}")

        print(f"\n💡 All files are ready for download and analysis!")
        print(f"💰 Portfolio: {result['bets_count']} bets, ${result['total_stake']} stake, ${result['potential_profit']:.2f} potential profit")

    else:
        print(f"\n❌ Failed to create CSV reports")

if __name__ == "__main__":
    main()