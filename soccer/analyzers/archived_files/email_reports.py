#!/usr/bin/env python3
"""
Email Reports System
Automatically send daily soccer betting reports via email
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import json
from datetime import datetime
import pandas as pd

class EmailReporter:
    """Send daily reports via email"""

    def __init__(self, config_file="email_config.json"):
        self.config = self.load_config(config_file)
        self.date_str = datetime.now().strftime("%Y%m%d")
        self.date_readable = datetime.now().strftime("%B %d, %Y")

    def load_config(self, config_file):
        """Load email configuration"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Email config file not found. Creating template: {config_file}")
            self.create_config_template(config_file)
            return None

    def create_config_template(self, config_file):
        """Create email configuration template"""
        template = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "your-email@gmail.com",
            "sender_password": "your-app-password",
            "recipient_email": "recipient@example.com",
            "email_enabled": False,
            "instructions": {
                "gmail_setup": [
                    "1. Enable 2-factor authentication on your Gmail account",
                    "2. Go to Google Account settings > Security > App passwords",
                    "3. Generate an app password for 'Mail'",
                    "4. Use that app password in 'sender_password' field",
                    "5. Set 'email_enabled' to true when ready"
                ],
                "other_providers": {
                    "outlook": {"smtp_server": "smtp-mail.outlook.com", "smtp_port": 587},
                    "yahoo": {"smtp_server": "smtp.mail.yahoo.com", "smtp_port": 587},
                    "icloud": {"smtp_server": "smtp.mail.me.com", "smtp_port": 587}
                }
            }
        }

        with open(config_file, 'w') as f:
            json.dump(template, f, indent=2)

        print(f"✅ Created email config template: {config_file}")
        print("📧 Please configure your email settings and set 'email_enabled': true")

    def create_daily_summary(self):
        """Create HTML email summary of today's reports"""

        # Load today's key data
        picks_file = f"output reports/daily_picks_{self.date_str}.csv"
        summary_data = self.load_summary_data(picks_file)

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2e7d32; color: white; padding: 15px; border-radius: 5px; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .picks {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .conservative {{ background-color: #fff3e0; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚽ Soccer Betting Daily Report</h1>
                <h2>{self.date_readable}</h2>
            </div>

            <div class="summary">
                <h3>📊 Daily Summary</h3>
                <ul>
                    <li><strong>Picks Generated:</strong> {summary_data['picks_count']}</li>
                    <li><strong>Strategy:</strong> {summary_data['strategy']}</li>
                    <li><strong>Risk Level:</strong> {summary_data['risk_level']}</li>
                    <li><strong>Fixtures Analyzed:</strong> {summary_data['fixtures_analyzed']}</li>
                </ul>
            </div>

            {self.get_picks_section(summary_data)}

            <div class="summary">
                <h3>📈 Performance Tracking</h3>
                <p><strong>Cumulative Picks:</strong> {summary_data['total_picks']} total bets tracked</p>
                <p><strong>Bankroll Status:</strong> ${summary_data['bankroll']}</p>
                <p><strong>System Status:</strong> {summary_data['system_status']}</p>
            </div>

            {self.get_us_sportsbooks_section()}

            <div class="summary">
                <h3>📎 Attached Reports</h3>
                <ul>
                    <li>daily_picks_{self.date_str}.csv - Today's betting recommendations</li>
                    <li>daily_all_games_{self.date_str}.csv - All games analyzed</li>
                    <li>high_confidence_picks_{self.date_str}.csv - High-confidence selections</li>
                    <li>us_sportsbooks_comparison_{self.date_str}.csv - DraftKings vs FanDuel odds</li>
                    <li>us_sportsbooks_report_{self.date_str}.txt - US bookmakers analysis</li>
                    <li>cumulative_picks_tracker.csv - Complete betting history</li>
                </ul>
            </div>

            <div class="summary">
                <h3>🤖 System Information</h3>
                <p>Generated automatically by Soccer Betting AI System</p>
                <p>Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Next report: Tomorrow at the same time</p>
            </div>
        </body>
        </html>
        """

        return html

    def get_picks_section(self, summary_data):
        """Generate picks section based on strategy"""
        if summary_data['picks_count'] == 0:
            return '''
            <div class="conservative">
                <h3>🛡️ Conservative Approach Today</h3>
                <p><strong>No betting opportunities found</strong> - The system identified insufficient value in today's matches.</p>
                <p>✅ <strong>Capital Preservation Mode:</strong> Protecting bankroll by waiting for better opportunities</p>
                <p>💡 <strong>Next Steps:</strong> Continue monitoring tomorrow's fixtures for high-value bets</p>
            </div>
            '''
        else:
            return f'''
            <div class="picks">
                <h3>🎯 Today's Betting Recommendations</h3>
                <p><strong>{summary_data['picks_count']} picks</strong> identified with positive expected value</p>
                <p>See attached CSV files for detailed analysis and odds</p>
            </div>
            '''

    def get_us_sportsbooks_section(self):
        """Generate US sportsbooks comparison section"""
        us_report_file = f"output reports/us_sportsbooks_report_{self.date_str}.txt"
        us_csv_file = f"output reports/us_sportsbooks_comparison_{self.date_str}.csv"

        if not os.path.exists(us_report_file) and not os.path.exists(us_csv_file):
            return '''
            <div class="summary">
                <h3>🇺🇸 US Sportsbooks (DraftKings vs FanDuel)</h3>
                <p><strong>Status:</strong> Analysis not available today</p>
                <p>💡 Check back tomorrow for US odds comparison</p>
            </div>
            '''

        # Try to get summary stats from the report
        matches_compared = 0
        dk_better = 0
        fd_better = 0

        try:
            if os.path.exists(us_report_file):
                with open(us_report_file, 'r') as f:
                    content = f.read()
                    # Extract summary stats from the report
                    for line in content.split('\n'):
                        if 'Total Matches Compared:' in line:
                            matches_compared = line.split(':')[1].strip()
                        elif 'DraftKings Better:' in line:
                            dk_better = line.split(':')[1].strip().split()[0]
                        elif 'FanDuel Better:' in line:
                            fd_better = line.split(':')[1].strip().split()[0]
        except Exception as e:
            print(f"⚠️ Error reading US sportsbooks report: {e}")

        return f'''
        <div class="summary">
            <h3>🇺🇸 US Sportsbooks (DraftKings vs FanDuel)</h3>
            <ul>
                <li><strong>Matches Analyzed:</strong> {matches_compared}</li>
                <li><strong>DraftKings Better:</strong> {dk_better} markets</li>
                <li><strong>FanDuel Better:</strong> {fd_better} markets</li>
                <li><strong>Focus:</strong> MLS, EPL, Champions League</li>
            </ul>
            <p>💰 <strong>Purpose:</strong> Find the best odds between US's top two sportsbooks</p>
        </div>
        '''

    def load_summary_data(self, picks_file):
        """Load summary data for email"""
        data = {
            'picks_count': 0,
            'strategy': 'Conservative',
            'risk_level': 'Low',
            'fixtures_analyzed': 'Unknown',
            'total_picks': 'Unknown',
            'bankroll': 'Unknown',
            'system_status': 'Operational'
        }

        try:
            # Count picks
            if os.path.exists(picks_file):
                df = pd.read_csv(picks_file)
                # Don't count header-only or system message rows
                actual_picks = len(df[~df['home_team'].str.contains('No picks|Conservative', na=False)])
                data['picks_count'] = actual_picks

            # Load fixtures count
            fixtures_file = f"real_fixtures_{self.date_str}.json"
            if os.path.exists(fixtures_file):
                with open(fixtures_file, 'r') as f:
                    fixtures = json.load(f)
                    data['fixtures_analyzed'] = len(fixtures)

            # Load cumulative data
            cumulative_file = "output reports/cumulative_picks_tracker.csv"
            if os.path.exists(cumulative_file):
                cum_df = pd.read_csv(cumulative_file)
                data['total_picks'] = len(cum_df)
                if len(cum_df) > 0:
                    data['bankroll'] = f"{cum_df['running_bankroll'].iloc[-1]:.2f}"

        except Exception as e:
            print(f"⚠️ Error loading summary data: {e}")

        return data

    def send_daily_report(self):
        """Send daily email report with attachments"""

        if not self.config or not self.config.get('email_enabled', False):
            print("📧 Email not configured or disabled")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['sender_email']
            msg['To'] = self.config['recipient_email']
            msg['Subject'] = f"⚽ Soccer Betting Report - {self.date_readable}"

            # Add HTML body
            html_body = self.create_daily_summary()
            msg.attach(MIMEText(html_body, 'html'))

            # Attach reports
            reports_to_attach = [
                f"output reports/daily_picks_{self.date_str}.csv",
                f"output reports/daily_all_games_{self.date_str}.csv",
                f"output reports/high_confidence_picks_{self.date_str}.csv",
                f"output reports/us_sportsbooks_comparison_{self.date_str}.csv",
                f"output reports/us_sportsbooks_report_{self.date_str}.txt",
                "output reports/cumulative_picks_tracker.csv"
            ]

            for report_file in reports_to_attach:
                if os.path.exists(report_file):
                    self.attach_file(msg, report_file)
                else:
                    print(f"⚠️ Report file not found: {report_file}")

            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.sendmail(self.config['sender_email'], self.config['recipient_email'], msg.as_string())

            print(f"✅ Daily report emailed successfully to {self.config['recipient_email']}")
            return True

        except Exception as e:
            print(f"❌ Email send failed: {e}")
            return False

    def attach_file(self, msg, file_path):
        """Attach a file to email message"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            filename = os.path.basename(file_path)
            part.add_header('Content-Disposition', f'attachment; filename= {filename}')
            msg.attach(part)

        except Exception as e:
            print(f"⚠️ Could not attach {file_path}: {e}")

def main():
    """Send daily email report"""
    print("📧 Starting email report system...")

    reporter = EmailReporter()
    if reporter.send_daily_report():
        print("🎉 Daily email report sent successfully!")
    else:
        print("❌ Failed to send daily email report")

if __name__ == "__main__":
    main()