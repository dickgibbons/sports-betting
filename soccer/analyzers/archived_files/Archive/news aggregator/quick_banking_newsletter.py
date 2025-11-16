#!/usr/bin/env python3
"""
Quick Banking Newsletter Generator

Generates newsletter for top 5 priority banks only for faster testing
"""

from news_agent import NewsAgent
import json

def generate_quick_banking_newsletter():
    """Generate newsletter for top 5 banks only"""
    
    print("🏦 Generating Quick Banking Newsletter (Top 5 Priority Banks)...")
    
    # Initialize agent
    agent = NewsAgent()
    
    # Load full config
    config_file = "/Users/richardgibbons/soccer betting python/news aggregator/newsletters/company_config.json"
    with open(config_file, 'r') as f:
        all_companies = json.load(f)
    
    # Filter to only priority 1 banks (top 5)
    priority_1_banks = [c for c in all_companies if c['priority'] == 1]
    
    print(f"🎯 Focusing on {len(priority_1_banks)} Priority 1 banks:")
    for bank in priority_1_banks:
        print(f"   🔴 {bank['name']} ({bank['ticker']})")
    
    # Temporarily set agent companies to only priority 1
    agent.companies = []
    for bank in priority_1_banks:
        from news_agent import CompanyConfig
        company = CompanyConfig(
            name=bank["name"],
            ticker=bank["ticker"],
            keywords=bank["keywords"],
            priority=bank["priority"]
        )
        agent.companies.append(company)
    
    # Generate newsletter
    newsletter_path = agent.run_weekly_newsletter()
    
    print(f"\n✅ Quick banking newsletter generated!")
    print(f"📄 File: {newsletter_path}")
    print(f"🎯 Covers: JPMorgan Chase, Bank of America, Wells Fargo, Citigroup, Goldman Sachs")
    
    return newsletter_path

if __name__ == "__main__":
    generate_quick_banking_newsletter()