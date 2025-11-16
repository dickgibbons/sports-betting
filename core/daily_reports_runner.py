#!/usr/bin/env python3
"""
Daily Reports Runner - Master script for all daily betting reports
Generates:
1. Overall top 10 bets across all sports
2. Sport-specific top 10 bets (NHL, NBA, NCAA, Soccer)
3. NHL first period trend report
"""

import sys
import os
from datetime import datetime

# Add analyzers directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'analyzers'))

from daily_betting_report import DailyBettingReport
from nhl_first_period_daily_report import NHLFirstPeriodDailyReport


class DailyReportsRunner:
    """Master runner for all daily betting reports"""

    def __init__(self):
        self.date = datetime.now().strftime('%Y-%m-%d')
        base_dir = "/Users/dickgibbons/sports-betting/reports"
        self.reports_dir = os.path.join(base_dir, self.date)
        os.makedirs(self.reports_dir, exist_ok=True)

        print("="*80)
        print(f"🎯 DAILY REPORTS RUNNER - {self.date}")
        print("="*80)

    def run_all_reports(self):
        """Execute all daily reports"""

        # 1. Overall betting report (top 10 across all sports)
        print("\n" + "="*80)
        print("📊 REPORT 1: OVERALL TOP 10 BETS (ALL SPORTS)")
        print("="*80)
        overall_report = DailyBettingReport()
        all_bets = overall_report.generate_daily_report()
        overall_report.save_report(all_bets)

        # Store bets by sport for sport-specific reports
        all_bets_data = overall_report.all_bets

        # 2. NHL-specific report
        print("\n" + "="*80)
        print("🏒 REPORT 2: NHL TOP 10 BETS")
        print("="*80)
        self._generate_sport_report('NHL', all_bets_data)

        # 3. NHL First Period Trends Report
        print("\n" + "="*80)
        print("🏒 REPORT 3: NHL FIRST PERIOD TRENDS")
        print("="*80)
        self._generate_nhl_first_period_report()

        # 4. NBA-specific report
        print("\n" + "="*80)
        print("🏀 REPORT 4: NBA TOP 10 BETS")
        print("="*80)
        self._generate_sport_report('NBA', all_bets_data)

        # 5. NCAA-specific report
        print("\n" + "="*80)
        print("🏀 REPORT 5: NCAA BASKETBALL TOP 10 BETS")
        print("="*80)
        self._generate_sport_report('NCAA', all_bets_data)

        # 6. Soccer-specific report
        print("\n" + "="*80)
        print("⚽ REPORT 6: SOCCER TOP 10 BETS")
        print("="*80)
        self._generate_sport_report('SOCCER', all_bets_data)

        # Final summary
        print("\n" + "="*80)
        print("✅ ALL DAILY REPORTS COMPLETED")
        print("="*80)
        print(f"\n📁 All reports saved to: {self.reports_dir}/")
        print(f"\n   Files generated:")
        print(f"   - report_{self.date}.txt (Overall)")
        print(f"   - nhl_report_{self.date}.txt")
        print(f"   - nhl_first_period_trends_{self.date}.txt")
        print(f"   - nhl_first_period_trends_{self.date}.csv")
        print(f"   - nba_report_{self.date}.txt")
        print(f"   - ncaa_report_{self.date}.txt")
        print(f"   - soccer_report_{self.date}.txt")
        print("\n" + "="*80)

    def _generate_sport_report(self, sport: str, all_bets: list):
        """Generate top 10 report for a specific sport"""

        # Filter bets for this sport
        sport_bets = [bet for bet in all_bets if bet.get('sport') == sport]

        if not sport_bets:
            print(f"\n⚠️  No {sport} bets found for today\n")
            return

        # Rank by expected edge
        ranked = sorted(sport_bets, key=lambda x: x['expected_edge'], reverse=True)[:10]

        # Categorize by confidence
        elite = [b for b in ranked if b['confidence'] == 'ELITE']
        high = [b for b in ranked if b['confidence'] == 'HIGH']
        medium = [b for b in ranked if b['confidence'] == 'MEDIUM']
        low = [b for b in ranked if b['confidence'] == 'LOW']

        # Display report
        sport_icon = {'NHL': '🏒', 'NBA': '🏀', 'NCAA': '🏀', 'SOCCER': '⚽'}.get(sport, '🎯')

        print(f"\n{sport_icon} {sport} TOP 10 BETS - {self.date}")
        print(f"{'='*80}\n")

        print(f"📊 BREAKDOWN:")
        print(f"   🔥 ELITE: {len(elite)} bets")
        print(f"   ✅ HIGH: {len(high)} bets")
        print(f"   💡 MEDIUM: {len(medium)} bets")
        print(f"   ⚪ LOW: {len(low)} bets")
        print(f"\n{'─'*80}\n")

        # Display bets
        for i, bet in enumerate(ranked, 1):
            conf_marker = {'ELITE': '🔥🔥🔥', 'HIGH': '✅', 'MEDIUM': '💡', 'LOW': '⚪'}.get(bet['confidence'], '')

            print(f"{conf_marker} #{i} {sport_icon} {bet['game']}")
            print(f"   BET: {bet['bet']}")

            odds = bet.get('odds')
            if odds:
                true_ev = bet.get('true_ev', bet['expected_edge'])
                print(f"   ODDS: {odds:+d} | True EV: +{true_ev:.1f}% | Angles: {bet['angle_count']}")
            else:
                print(f"   Expected Edge: +{bet['expected_edge']:.1f}% | Angles: {bet['angle_count']} | Confidence: {bet['confidence']}")

            # Show top 2 reasons
            for j, angle in enumerate(bet['angles'][:2], 1):
                reason = angle.get('reason', '')
                print(f"   {j}. {reason}")

            # Bet sizing
            if bet['confidence'] == 'ELITE':
                print(f"   💰 RECOMMENDED: Bet 2-3% of bankroll")
            elif bet['confidence'] == 'HIGH':
                print(f"   💰 RECOMMENDED: Bet 1-2% of bankroll")
            elif bet['confidence'] == 'MEDIUM':
                print(f"   💰 RECOMMENDED: Bet 0.5-1% of bankroll")

            print()

        # Save to file
        filename = f"{self.reports_dir}/{sport.lower()}_report_{self.date}.txt"
        self._save_sport_report_to_file(sport, ranked, filename)
        print(f"📄 Saved: {filename}\n")

    def _save_sport_report_to_file(self, sport: str, ranked_bets: list, filename: str):
        """Save sport-specific report to file"""

        with open(filename, 'w') as f:
            f.write(f"{sport} BETTING REPORT - {self.date}\n")
            f.write(f"{'='*80}\n\n")

            for i, bet in enumerate(ranked_bets, 1):
                f.write(f"#{i} {bet['game']}\n")
                f.write(f"BET: {bet['bet']}\n")

                odds = bet.get('odds')
                if odds:
                    f.write(f"ODDS: {odds:+d} | True EV: +{bet.get('true_ev', bet['expected_edge']):.1f}%\n")
                else:
                    f.write(f"Edge: +{bet['expected_edge']:.1f}%\n")

                f.write(f"Confidence: {bet['confidence']}\n")
                f.write(f"Angles: {bet['angle_count']}\n")

                for j, angle in enumerate(bet['angles'][:2], 1):
                    f.write(f"  {j}. {angle.get('reason', '')}\n")

                f.write(f"\n")

    def _generate_nhl_first_period_report(self):
        """Generate NHL first period trends report"""

        # Initialize analyzer
        analyzer = NHLFirstPeriodDailyReport()

        # Analyze full season to date
        start_date = '2024-10-01'
        end_date = self.date

        analyzer.analyze_season(start_date, end_date)

        # Generate report to file
        output_file = f"{self.reports_dir}/nhl_first_period_trends_{self.date}.txt"
        csv_file = f"{self.reports_dir}/nhl_first_period_trends_{self.date}.csv"

        # Capture report output to file
        import io
        from contextlib import redirect_stdout

        with open(output_file, 'w') as f:
            with redirect_stdout(f):
                analyzer.generate_report(csv_file=csv_file)

        print(f"\n📄 NHL First Period Trends Report saved: {output_file}")
        print(f"📄 NHL First Period CSV saved: {csv_file}")

        # Also display to console
        analyzer.generate_report()


def main():
    runner = DailyReportsRunner()
    runner.run_all_reports()


if __name__ == "__main__":
    main()
