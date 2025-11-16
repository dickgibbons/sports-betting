#!/usr/bin/env python3
"""
Setup News Agent

Quick setup script to configure the news agent with sample companies
"""

from news_agent import NewsAgent

def setup_sample_companies():
    """Setup news agent with sample companies"""
    
    print("🤖 Setting up News Agent with sample companies...")
    
    # Initialize agent
    agent = NewsAgent()
    
    # Sample companies to track
    sample_companies = [
        # Tech companies (high priority)
        {"name": "Apple", "ticker": "AAPL", "keywords": ["Apple Inc", "AAPL", "iPhone", "iPad", "Mac"], "priority": 1},
        {"name": "Microsoft", "ticker": "MSFT", "keywords": ["Microsoft", "MSFT", "Azure", "Windows"], "priority": 1},
        {"name": "Google", "ticker": "GOOGL", "keywords": ["Google", "Alphabet", "GOOGL", "Android"], "priority": 1},
        {"name": "Tesla", "ticker": "TSLA", "keywords": ["Tesla", "TSLA", "Elon Musk", "electric vehicle"], "priority": 1},
        
        # Financial companies (medium priority)
        {"name": "JPMorgan", "ticker": "JPM", "keywords": ["JPMorgan", "JPM", "Chase Bank"], "priority": 2},
        {"name": "Goldman Sachs", "ticker": "GS", "keywords": ["Goldman Sachs", "GS"], "priority": 2},
        
        # Other sectors (low priority)
        {"name": "Johnson & Johnson", "ticker": "JNJ", "keywords": ["Johnson & Johnson", "JNJ"], "priority": 3},
        {"name": "Coca-Cola", "ticker": "KO", "keywords": ["Coca-Cola", "Coke", "KO"], "priority": 3},
    ]
    
    # Add companies
    for company in sample_companies:
        agent.add_company(
            name=company["name"],
            ticker=company["ticker"],
            keywords=company["keywords"],
            priority=company["priority"]
        )
    
    print(f"\n✅ Setup complete! Added {len(sample_companies)} companies")
    
    # List configured companies
    agent.list_companies()
    
    print(f"\n📰 Ready to generate newsletters!")
    print(f"📋 Next steps:")
    print(f"   1. Generate a test newsletter: python news_agent.py --newsletter")
    print(f"   2. Configure more companies: python news_agent.py --config")
    print(f"   3. Schedule weekly newsletters: python weekly_news_scheduler.py")
    
    return agent

def demo_newsletter_generation():
    """Generate a demo newsletter"""
    
    print("\n🧪 Generating demo newsletter...")
    
    # Setup if not already done
    agent = NewsAgent()
    if not agent.companies:
        print("No companies configured. Running setup first...")
        agent = setup_sample_companies()
    
    # Generate newsletter
    newsletter_path = agent.run_weekly_newsletter()
    
    print(f"\n✅ Demo newsletter generated!")
    print(f"📄 Check the file: {newsletter_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup News Agent")
    parser.add_argument('--setup', action='store_true', help='Setup sample companies')
    parser.add_argument('--demo', action='store_true', help='Generate demo newsletter')
    parser.add_argument('--both', action='store_true', help='Setup and generate demo')
    
    args = parser.parse_args()
    
    if args.setup or args.both:
        setup_sample_companies()
    
    if args.demo or args.both:
        demo_newsletter_generation()
    
    if not any([args.setup, args.demo, args.both]):
        # Default behavior
        print("🤖 News Agent Setup")
        print("Choose an option:")
        print("  1. Setup sample companies")
        print("  2. Generate demo newsletter") 
        print("  3. Both")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            setup_sample_companies()
        elif choice == "2":
            demo_newsletter_generation()
        elif choice == "3":
            setup_sample_companies()
            demo_newsletter_generation()
        else:
            print("Invalid choice")