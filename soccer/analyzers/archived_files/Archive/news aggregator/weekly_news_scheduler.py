#!/usr/bin/env python3
"""
Weekly News Scheduler

Automated scheduler to run the news agent weekly and send newsletters
"""

import schedule
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from news_agent import NewsAgent
import os

class NewsScheduler:
    """Automated scheduler for weekly newsletters"""
    
    def __init__(self, openai_key: str = None, email_config: dict = None):
        self.agent = NewsAgent(openai_api_key=openai_key)
        self.email_config = email_config or {}
        
    def send_email_newsletter(self, newsletter_content: str, recipient_email: str):
        """Send newsletter via email"""
        
        if not self.email_config:
            print("⚠️ No email configuration provided. Newsletter saved to file only.")
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['smtp_user']
            msg['To'] = recipient_email
            msg['Subject'] = f"Weekly Company News Digest - {datetime.now().strftime('%B %d, %Y')}"
            
            # Add newsletter content
            msg.attach(MIMEText(newsletter_content, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['smtp_user'], self.email_config['smtp_password'])
            server.send_message(msg)
            server.quit()
            
            print(f"📧 Newsletter emailed to {recipient_email}")
            
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            print("📄 Newsletter saved to file instead")
    
    def run_weekly_job(self):
        """Main weekly job to generate and send newsletter"""
        
        print(f"🤖 Running weekly news job at {datetime.now()}")
        
        try:
            # Generate newsletter
            newsletter_path = self.agent.run_weekly_newsletter()
            
            # Read newsletter content
            if os.path.exists(newsletter_path):
                with open(newsletter_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Send email if configured
                if self.email_config and 'recipient_email' in self.email_config:
                    self.send_email_newsletter(content, self.email_config['recipient_email'])
                
                print(f"✅ Weekly news job completed successfully")
            
        except Exception as e:
            print(f"❌ Weekly news job failed: {e}")
    
    def setup_schedule(self, day_of_week: str = "monday", time_str: str = "09:00"):
        """Setup weekly schedule"""
        
        print(f"📅 Scheduling weekly newsletter for {day_of_week}s at {time_str}")
        
        # Schedule the job
        if day_of_week.lower() == "monday":
            schedule.every().monday.at(time_str).do(self.run_weekly_job)
        elif day_of_week.lower() == "tuesday":
            schedule.every().tuesday.at(time_str).do(self.run_weekly_job)
        elif day_of_week.lower() == "wednesday":
            schedule.every().wednesday.at(time_str).do(self.run_weekly_job)
        elif day_of_week.lower() == "thursday":
            schedule.every().thursday.at(time_str).do(self.run_weekly_job)
        elif day_of_week.lower() == "friday":
            schedule.every().friday.at(time_str).do(self.run_weekly_job)
        elif day_of_week.lower() == "saturday":
            schedule.every().saturday.at(time_str).do(self.run_weekly_job)
        elif day_of_week.lower() == "sunday":
            schedule.every().sunday.at(time_str).do(self.run_weekly_job)
    
    def start_scheduler(self):
        """Start the scheduler loop"""
        
        print("🚀 News scheduler started. Press Ctrl+C to stop.")
        print("📅 Next run:", schedule.next_run())
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n⏹️ Scheduler stopped by user")

def main():
    """Main function for the scheduler"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Weekly News Scheduler")
    parser.add_argument('--day', default='monday', help='Day of week to run (default: monday)')
    parser.add_argument('--time', default='09:00', help='Time to run HH:MM (default: 09:00)')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--email', help='Email address to send newsletter to')
    parser.add_argument('--test', action='store_true', help='Run newsletter generation once (test mode)')
    
    args = parser.parse_args()
    
    # Email configuration (optional)
    email_config = None
    if args.email:
        email_config = {
            'smtp_server': 'smtp.gmail.com',  # Change for your email provider
            'smtp_port': 587,
            'smtp_user': 'your_email@gmail.com',  # Your email
            'smtp_password': 'your_app_password',  # Your app password
            'recipient_email': args.email
        }
        print("📧 Email delivery configured")
    
    # Initialize scheduler
    scheduler = NewsScheduler(openai_key=args.openai_key, email_config=email_config)
    
    if args.test:
        # Test mode - run once
        print("🧪 Test mode: Running newsletter generation once...")
        scheduler.run_weekly_job()
    else:
        # Schedule mode
        scheduler.setup_schedule(args.day, args.time)
        scheduler.start_scheduler()

if __name__ == "__main__":
    main()