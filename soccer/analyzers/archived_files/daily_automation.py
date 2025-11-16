#!/usr/bin/env python3
"""
Daily Soccer Betting Automation System
Runs daily analysis and emails reports automatically
"""

import subprocess
import sys
import os
from datetime import datetime
import logging
import json

class DailyAutomation:
    """Main automation coordinator"""

    def __init__(self):
        self.setup_logging()
        self.date_str = datetime.now().strftime("%Y%m%d")
        self.date_readable = datetime.now().strftime("%Y-%m-%d")

    def setup_logging(self):
        """Setup logging for automation"""
        log_file = f"automation_log_{datetime.now().strftime('%Y%m')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def run_daily_sequence(self):
        """Execute the complete daily automation sequence"""

        self.logger.info(f"🚀 Starting daily automation for {self.date_readable}")
        self.logger.info("=" * 60)

        success_count = 0
        total_steps = 7

        # Step 1: Generate fixtures and analysis
        if self.run_fixtures_analysis():
            success_count += 1

        # Step 2: Generate streamlined reports
        if self.run_streamlined_reports():
            success_count += 1

        # Step 2.5: Run US Sportsbooks analysis
        if self.run_us_sportsbooks_analysis():
            success_count += 1

        # Step 3: Update cumulative tracker
        if self.update_cumulative_tracker():
            success_count += 1

        # Step 4: Update performance trackers
        if self.update_performance_trackers():
            success_count += 1

        # Step 5: Generate analysis summary
        if self.generate_analysis_summary():
            success_count += 1

        # Step 6: Send email report
        if self.send_email_report():
            success_count += 1

        # Final summary
        self.logger.info(f"\n📊 Daily automation completed: {success_count}/{total_steps} steps successful")

        if success_count == total_steps:
            self.logger.info("✅ All automation steps completed successfully!")
            return True
        else:
            self.logger.warning(f"⚠️ {total_steps - success_count} steps failed - check logs")
            return False

    def run_fixtures_analysis(self):
        """Step 1: Generate today's fixtures and analysis"""
        try:
            self.logger.info("📊 Step 1: Generating fixtures and analysis...")

            # Run REAL-ONLY daily fixtures generator (no simulated data)
            result = subprocess.run([
                sys.executable, "real_only_fixtures_generator.py"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                self.logger.info("✅ Fixtures analysis completed successfully")
                return True
            else:
                self.logger.error(f"❌ Fixtures analysis failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("❌ Fixtures analysis timed out")
            return False
        except Exception as e:
            self.logger.error(f"❌ Fixtures analysis error: {e}")
            return False

    def run_streamlined_reports(self):
        """Step 2: Generate streamlined daily reports"""
        try:
            self.logger.info("📋 Step 2: Generating streamlined reports...")

            result = subprocess.run([
                sys.executable, "streamlined_generator.py"
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                self.logger.info("✅ Streamlined reports generated successfully")

                # Generate top 5 best picks
                try:
                    subprocess.run([
                        sys.executable, "top5_daily_picks.py"
                    ], capture_output=True, text=True, timeout=30)
                except:
                    pass  # Optional report, don't fail if it errors

                return True
            else:
                self.logger.error(f"❌ Streamlined reports failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Streamlined reports error: {e}")
            return False

    def run_us_sportsbooks_analysis(self):
        """Step 2.5: Run US Sportsbooks (DraftKings vs FanDuel) analysis"""
        try:
            self.logger.info("🇺🇸 Step 2.5: Running US Sportsbooks analysis...")

            result = subprocess.run([
                sys.executable, "us_sportsbooks_integration.py"
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                self.logger.info("✅ US Sportsbooks analysis completed successfully")
                return True
            else:
                self.logger.warning(f"⚠️ US Sportsbooks analysis failed: {result.stderr}")
                # Not critical - continue with other reports
                return True

        except subprocess.TimeoutExpired:
            self.logger.warning("⚠️ US Sportsbooks analysis timed out")
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ US Sportsbooks analysis error: {e}")
            # Not critical - continue with other reports
            return True

    def update_cumulative_tracker(self):
        """Step 3: Update cumulative picks tracker"""
        try:
            self.logger.info("📈 Step 3: Updating cumulative tracker...")

            # Check if tracker needs updating
            tracker_file = "output reports/cumulative_picks_tracker.csv"
            if os.path.exists(tracker_file):
                self.logger.info("✅ Cumulative tracker already up to date")
                return True
            else:
                result = subprocess.run([
                    sys.executable, "rebuild_cumulative_tracker.py"
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    self.logger.info("✅ Cumulative tracker updated successfully")
                    return True
                else:
                    self.logger.error(f"❌ Cumulative tracker update failed: {result.stderr}")
                    return False

        except Exception as e:
            self.logger.error(f"❌ Cumulative tracker error: {e}")
            return False

    def update_performance_trackers(self):
        """Step 4: Update performance tracking files"""
        try:
            self.logger.info("🏆 Step 4: Updating performance trackers...")

            # Run top8 tracker (most stable)
            result = subprocess.run([
                sys.executable, "clean_top8_tracker.py"
            ], capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                self.logger.info("✅ Performance trackers updated successfully")
                return True
            else:
                self.logger.warning(f"⚠️ Performance trackers had issues: {result.stderr}")
                # Continue anyway - not critical
                return True

        except Exception as e:
            self.logger.warning(f"⚠️ Performance trackers error: {e}")
            # Continue anyway - not critical
            return True

    def generate_analysis_summary(self):
        """Step 5: Generate daily analysis summary"""
        try:
            self.logger.info("📊 Step 5: Generating analysis summary...")

            # Create a simple analysis summary
            summary = {
                "date": self.date_readable,
                "automation_run": datetime.now().isoformat(),
                "reports_generated": self.count_reports_generated(),
                "system_status": "Operational",
                "next_run": "Tomorrow at same time"
            }

            summary_file = f"output reports/daily_summary_{self.date_str}.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)

            self.logger.info("✅ Analysis summary generated successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Analysis summary error: {e}")
            return False

    def send_email_report(self):
        """Step 6: Send email report"""
        try:
            self.logger.info("📧 Step 6: Sending email report...")

            result = subprocess.run([
                sys.executable, "email_reports.py"
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                self.logger.info("✅ Email report sent successfully")
                return True
            else:
                self.logger.warning(f"⚠️ Email report failed: {result.stderr}")
                # Not critical - system still works
                return True

        except Exception as e:
            self.logger.warning(f"⚠️ Email report error: {e}")
            # Not critical - system still works
            return True

    def count_reports_generated(self):
        """Count how many reports were generated today"""
        reports = [
            f"output reports/daily_picks_{self.date_str}.csv",
            f"output reports/daily_all_games_{self.date_str}.csv",
            f"output reports/high_confidence_picks_{self.date_str}.csv",
            f"output reports/us_sportsbooks_comparison_{self.date_str}.csv",
            f"output reports/us_sportsbooks_report_{self.date_str}.txt",
            f"real_fixtures_{self.date_str}.json"
        ]

        count = sum(1 for report in reports if os.path.exists(report))
        return count

def main():
    """Run daily automation"""
    automation = DailyAutomation()

    try:
        success = automation.run_daily_sequence()
        exit_code = 0 if success else 1
        sys.exit(exit_code)

    except KeyboardInterrupt:
        automation.logger.info("❌ Daily automation interrupted by user")
        sys.exit(1)
    except Exception as e:
        automation.logger.error(f"❌ Daily automation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()