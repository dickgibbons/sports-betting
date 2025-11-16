#!/usr/bin/env python3
"""
AWS Lambda Handler for Daily Soccer Reports
Runs soccer betting analysis and emails reports daily at 6 AM
"""

import json
import boto3
import os
import tempfile
import zipfile
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Import your soccer modules
from daily_betting_report_generator import DailyBettingReportGenerator
from generate_all_daily_reports import main as generate_all_reports

def lambda_handler(event, context):
    """Main Lambda handler function"""

    print("🚀 Starting Daily Soccer Reports Lambda")

    try:
        # Environment variables
        api_key = os.environ.get('API_SPORTS_KEY', '960c628e1c91c4b1f125e1eec52ad862')
        email_recipient = os.environ.get('EMAIL_RECIPIENT', 'your-email@domain.com')
        sender_email = os.environ.get('SENDER_EMAIL', 'soccer-reports@your-domain.com')

        # Calculate tomorrow's date
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        day_name = tomorrow.strftime('%A')
        date_str = tomorrow.strftime('%Y%m%d')

        print(f"📅 Generating reports for {day_name}, {tomorrow_str}")

        # Create temporary directory for reports
        with tempfile.TemporaryDirectory() as temp_dir:

            # Set up paths in temp directory
            os.environ['TEMP_DIR'] = temp_dir
            reports_dir = os.path.join(temp_dir, 'output_reports')
            os.makedirs(reports_dir, exist_ok=True)

            # Run soccer analysis
            print("⚽ Running soccer analysis...")
            generator = DailyBettingReportGenerator(api_key)
            generator.today = tomorrow_str
            generator.day_name = day_name

            # Generate main report
            daily_report = generator.generate_daily_report()

            if not daily_report:
                print("❌ No fixtures found for tomorrow")
                return {
                    'statusCode': 200,
                    'body': json.dumps('No fixtures available for tomorrow')
                }

            # Generate all additional reports
            print("📊 Generating specialized reports...")
            generate_all_reports()

            # Collect report files
            report_files = []
            expected_files = [
                f'daily_picks_{date_str}.csv',
                f'daily_report_{date_str}.txt',
                f'high_confidence_picks_{date_str}.csv',
                f'high_confidence_report_{date_str}.txt',
                'top8_daily_tracker.csv',
                'strategy_comparison.txt'
            ]

            for filename in expected_files:
                file_path = os.path.join(reports_dir, filename)
                if os.path.exists(file_path):
                    report_files.append(file_path)
                    print(f"✅ Found: {filename}")
                else:
                    print(f"⚠️ Missing: {filename}")

            # Send email with reports
            if report_files:
                print(f"📧 Sending email with {len(report_files)} attachments...")
                send_email_with_reports(
                    sender_email,
                    email_recipient,
                    report_files,
                    tomorrow_str,
                    daily_report
                )

                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': f'Reports generated and sent for {tomorrow_str}',
                        'total_matches': daily_report.get('total_matches', 0),
                        'recommended_bets': daily_report.get('recommended_bets', 0),
                        'files_sent': len(report_files)
                    })
                }
            else:
                print("❌ No report files generated")
                return {
                    'statusCode': 500,
                    'body': json.dumps('No report files were generated')
                }

    except Exception as e:
        print(f"❌ Lambda execution failed: {str(e)}")
        import traceback
        traceback.print_exc()

        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

def send_email_with_reports(sender, recipient, report_files, date_str, daily_report):
    """Send email with report attachments using AWS SES"""

    try:
        # Initialize SES client
        ses_client = boto3.client('ses', region_name='us-east-1')

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = recipient
        msg['Subject'] = f'⚽ Daily Soccer Reports - {date_str}'

        # Email body
        total_matches = daily_report.get('total_matches', 0)
        recommended_bets = daily_report.get('recommended_bets', 0)

        body = f"""
🚀 Daily Soccer Betting Reports - {date_str}

📊 Analysis Summary:
• Total Matches Analyzed: {total_matches}
• Recommended Betting Opportunities: {recommended_bets}
• Report Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

📎 Attached Reports:
"""

        for file_path in report_files:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB
            body += f"• {filename} ({file_size:.1f} KB)\n"

        body += """
📈 Report Descriptions:
• daily_picks_*.csv - All betting opportunities with odds and analysis
• daily_report_*.txt - Human-readable summary report
• high_confidence_*.csv - Conservative picks with 85%+ confidence
• top8_daily_tracker.csv - Best daily picks with historical tracking
• strategy_comparison.txt - Performance comparison across strategies

⚠️ Important: These are model predictions for entertainment purposes only.
Always bet responsibly and within your means.

🤖 Generated automatically by AWS Lambda
        """

        msg.attach(MIMEText(body, 'plain'))

        # Attach report files
        for file_path in report_files:
            filename = os.path.basename(file_path)

            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)

        # Send email
        response = ses_client.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={'Data': msg.as_string()}
        )

        print(f"✅ Email sent successfully. Message ID: {response['MessageId']}")
        return True

    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False

# For local testing
if __name__ == "__main__":
    # Test locally
    test_event = {}
    test_context = {}
    result = lambda_handler(test_event, test_context)
    print(f"Local test result: {result}")