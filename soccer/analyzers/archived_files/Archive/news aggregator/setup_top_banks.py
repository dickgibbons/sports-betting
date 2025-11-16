#!/usr/bin/env python3
"""
Setup Top 25 Banks by AUM

Configures news agent with the top 25 banks by Assets Under Management,
focusing on strategic plans, filings, and executive interviews
"""

from news_agent import NewsAgent

def setup_top_banks_by_aum():
    """Setup news agent with top 25 banks by AUM focused on strategic content"""
    
    print("🏦 Setting up News Agent with Top 25 Banks by AUM...")
    print("🎯 Focus: Strategic plans, filings, interviews, executive content")
    
    # Initialize agent
    agent = NewsAgent()
    
    # Clear existing companies
    agent.companies = []
    
    # Top 25 banks by Assets Under Management (AUM) with strategic focus keywords
    top_banks = [
        # Top Tier (Priority 1) - Largest global banks
        {
            "name": "JPMorgan Chase", "ticker": "JPM", "priority": 1,
            "keywords": [
                "JPMorgan Chase strategic plan", "Jamie Dimon strategy", "JPM earnings call", 
                "JPMorgan acquisition", "JPM merger", "Jamie Dimon interview", "JPMorgan outlook",
                "JPM 10-K filing", "JPMorgan investor day", "Chase bank strategy", "JPM roadmap"
            ]
        },
        {
            "name": "Bank of America", "ticker": "BAC", "priority": 1,
            "keywords": [
                "Bank of America strategy", "Brian Moynihan strategic", "BAC earnings call",
                "BofA strategic plan", "Bank of America acquisition", "BAC merger", "Moynihan interview",
                "BofA outlook", "BAC 10-K filing", "Bank of America investor", "BofA roadmap"
            ]
        },
        {
            "name": "Wells Fargo", "ticker": "WFC", "priority": 1,
            "keywords": [
                "Wells Fargo strategic plan", "Charlie Scharf strategy", "WFC earnings call",
                "Wells Fargo transformation", "WFC acquisition", "Scharf interview", "Wells Fargo outlook",
                "WFC 10-K filing", "Wells Fargo investor day", "Wells Fargo roadmap", "WFC strategic"
            ]
        },
        {
            "name": "Citigroup", "ticker": "C", "priority": 1,
            "keywords": [
                "Citigroup strategic plan", "Jane Fraser strategy", "Citi earnings call",
                "Citibank transformation", "Citi acquisition", "Fraser interview", "Citigroup outlook",
                "Citi 10-K filing", "Citigroup investor day", "Citi roadmap", "Jane Fraser strategic"
            ]
        },
        {
            "name": "Goldman Sachs", "ticker": "GS", "priority": 1,
            "keywords": [
                "Goldman Sachs strategic plan", "David Solomon strategy", "GS earnings call",
                "Goldman transformation", "GS acquisition", "Solomon interview", "Goldman outlook",
                "GS 10-K filing", "Goldman investor day", "Goldman roadmap", "Marcus strategy"
            ]
        },
        
        # Large Banks (Priority 2)
        {
            "name": "Morgan Stanley", "ticker": "MS", "priority": 2,
            "keywords": [
                "Morgan Stanley strategic plan", "James Gorman strategy", "MS earnings call",
                "Morgan Stanley transformation", "MS acquisition", "Gorman interview", "Morgan Stanley outlook",
                "MS 10-K filing", "Morgan Stanley investor", "MS roadmap", "wealth management strategy"
            ]
        },
        {
            "name": "U.S. Bancorp", "ticker": "USB", "priority": 2,
            "keywords": [
                "U.S. Bancorp strategic plan", "Andy Cecere strategy", "USB earnings call",
                "U.S. Bank transformation", "USB acquisition", "Cecere interview", "U.S. Bancorp outlook",
                "USB 10-K filing", "U.S. Bancorp investor", "USB roadmap", "U.S. Bank strategic"
            ]
        },
        {
            "name": "PNC Financial", "ticker": "PNC", "priority": 2,
            "keywords": [
                "PNC Financial strategic plan", "William Demchak strategy", "PNC earnings call",
                "PNC Bank transformation", "PNC acquisition", "Demchak interview", "PNC outlook",
                "PNC 10-K filing", "PNC investor day", "PNC roadmap", "PNC strategic"
            ]
        },
        {
            "name": "Truist Financial", "ticker": "TFC", "priority": 2,
            "keywords": [
                "Truist Financial strategic plan", "William Rogers strategy", "TFC earnings call",
                "Truist transformation", "TFC acquisition", "Rogers interview", "Truist outlook",
                "TFC 10-K filing", "Truist investor", "TFC roadmap", "BB&T SunTrust merger"
            ]
        },
        {
            "name": "Capital One", "ticker": "COF", "priority": 2,
            "keywords": [
                "Capital One strategic plan", "Richard Fairbank strategy", "COF earnings call",
                "Capital One transformation", "COF acquisition", "Fairbank interview", "Capital One outlook",
                "COF 10-K filing", "Capital One investor", "COF roadmap", "digital banking strategy"
            ]
        },
        
        # Regional/International Banks (Priority 2-3)
        {
            "name": "TD Bank", "ticker": "TD", "priority": 2,
            "keywords": [
                "TD Bank strategic plan", "Bharat Masrani strategy", "TD earnings call",
                "Toronto Dominion transformation", "TD acquisition", "Masrani interview", "TD outlook",
                "TD 10-K filing", "TD investor day", "TD roadmap", "TD U.S. strategy"
            ]
        },
        {
            "name": "Bank of Montreal", "ticker": "BMO", "priority": 2,
            "keywords": [
                "Bank of Montreal strategic plan", "Darryl White strategy", "BMO earnings call",
                "BMO transformation", "BMO acquisition", "White interview", "BMO outlook",
                "BMO 10-K filing", "BMO investor", "BMO roadmap", "BMO U.S. expansion"
            ]
        },
        {
            "name": "Royal Bank of Canada", "ticker": "RY", "priority": 2,
            "keywords": [
                "Royal Bank Canada strategic plan", "Dave McKay strategy", "RBC earnings call",
                "RBC transformation", "RBC acquisition", "McKay interview", "RBC outlook",
                "RBC 10-K filing", "RBC investor", "RBC roadmap", "RBC U.S. strategy"
            ]
        },
        {
            "name": "Charles Schwab", "ticker": "SCHW", "priority": 2,
            "keywords": [
                "Charles Schwab strategic plan", "Walt Bettinger strategy", "SCHW earnings call",
                "Schwab transformation", "SCHW acquisition", "Bettinger interview", "Schwab outlook",
                "SCHW 10-K filing", "Schwab investor", "SCHW roadmap", "TD Ameritrade integration"
            ]
        },
        {
            "name": "American Express", "ticker": "AXP", "priority": 2,
            "keywords": [
                "American Express strategic plan", "Stephen Squeri strategy", "AXP earnings call",
                "AmEx transformation", "AXP acquisition", "Squeri interview", "AmEx outlook",
                "AXP 10-K filing", "American Express investor", "AXP roadmap", "AmEx digital strategy"
            ]
        },
        
        # Mid-Tier Banks (Priority 3)
        {
            "name": "Fifth Third Bank", "ticker": "FITB", "priority": 3,
            "keywords": [
                "Fifth Third strategic plan", "Greg Carmichael strategy", "FITB earnings call",
                "Fifth Third transformation", "FITB acquisition", "Carmichael interview", "Fifth Third outlook",
                "FITB 10-K filing", "Fifth Third investor", "FITB roadmap", "Fifth Third strategic"
            ]
        },
        {
            "name": "KeyCorp", "ticker": "KEY", "priority": 3,
            "keywords": [
                "KeyCorp strategic plan", "Chris Gorman strategy", "KEY earnings call",
                "KeyBank transformation", "KEY acquisition", "Gorman interview", "KeyCorp outlook",
                "KEY 10-K filing", "KeyCorp investor", "KEY roadmap", "KeyBank strategic"
            ]
        },
        {
            "name": "Regions Financial", "ticker": "RF", "priority": 3,
            "keywords": [
                "Regions Financial strategic plan", "John Turner strategy", "RF earnings call",
                "Regions Bank transformation", "RF acquisition", "Turner interview", "Regions outlook",
                "RF 10-K filing", "Regions investor", "RF roadmap", "Regions strategic"
            ]
        },
        {
            "name": "Huntington Bancshares", "ticker": "HBAN", "priority": 3,
            "keywords": [
                "Huntington strategic plan", "Steve Steinour strategy", "HBAN earnings call",
                "Huntington transformation", "HBAN acquisition", "Steinour interview", "Huntington outlook",
                "HBAN 10-K filing", "Huntington investor", "HBAN roadmap", "TCF merger"
            ]
        },
        {
            "name": "M&T Bank", "ticker": "MTB", "priority": 3,
            "keywords": [
                "M&T Bank strategic plan", "Rene Jones strategy", "MTB earnings call",
                "M&T transformation", "MTB acquisition", "Jones interview", "M&T outlook",
                "MTB 10-K filing", "M&T investor", "MTB roadmap", "People's United merger"
            ]
        },
        {
            "name": "Comerica", "ticker": "CMA", "priority": 3,
            "keywords": [
                "Comerica strategic plan", "Curt Farmer strategy", "CMA earnings call",
                "Comerica transformation", "CMA acquisition", "Farmer interview", "Comerica outlook",
                "CMA 10-K filing", "Comerica investor", "CMA roadmap", "Comerica strategic"
            ]
        },
        {
            "name": "Zions Bancorporation", "ticker": "ZION", "priority": 3,
            "keywords": [
                "Zions strategic plan", "Harris Simmons strategy", "ZION earnings call",
                "Zions transformation", "ZION acquisition", "Simmons interview", "Zions outlook",
                "ZION 10-K filing", "Zions investor", "ZION roadmap", "Zions Bancorporation strategic"
            ]
        },
        {
            "name": "Citizens Financial", "ticker": "CFG", "priority": 3,
            "keywords": [
                "Citizens Financial strategic plan", "Bruce Van Saun strategy", "CFG earnings call",
                "Citizens transformation", "CFG acquisition", "Van Saun interview", "Citizens outlook",
                "CFG 10-K filing", "Citizens investor", "CFG roadmap", "Citizens Bank strategic"
            ]
        },
        {
            "name": "First Republic Bank", "ticker": "FRC", "priority": 3,
            "keywords": [
                "First Republic strategic plan", "Jim Herbert strategy", "FRC earnings call",
                "First Republic transformation", "FRC acquisition", "Herbert interview", "First Republic outlook",
                "FRC 10-K filing", "First Republic investor", "FRC roadmap", "private banking strategy"
            ]
        },
        {
            "name": "SVB Financial", "ticker": "SIVB", "priority": 3,
            "keywords": [
                "SVB Financial strategic plan", "Greg Becker strategy", "SIVB earnings call",
                "Silicon Valley Bank transformation", "SIVB acquisition", "Becker interview", "SVB outlook",
                "SIVB 10-K filing", "SVB investor", "SIVB roadmap", "tech banking strategy"
            ]
        }
    ]
    
    # Add banks to the agent
    for bank in top_banks:
        agent.add_company(
            name=bank["name"],
            ticker=bank["ticker"],
            keywords=bank["keywords"],
            priority=bank["priority"]
        )
    
    print(f"\n✅ Setup complete! Added {len(top_banks)} top banks by AUM")
    
    # Show priority breakdown
    priority_counts = {}
    for bank in top_banks:
        p = bank["priority"]
        priority_counts[p] = priority_counts.get(p, 0) + 1
    
    print(f"\n📊 Priority Breakdown:")
    print(f"   🔴 Priority 1 (Largest): {priority_counts.get(1, 0)} banks")
    print(f"   🟡 Priority 2 (Large): {priority_counts.get(2, 0)} banks") 
    print(f"   🟢 Priority 3 (Regional): {priority_counts.get(3, 0)} banks")
    
    # List configured banks
    agent.list_companies()
    
    print(f"\n🎯 Strategic Focus Keywords Include:")
    print(f"   📋 Strategic plans, transformations, roadmaps")
    print(f"   💼 Executive interviews (CEOs, key leaders)")
    print(f"   📊 Earnings calls and investor days")
    print(f"   📑 SEC filings (10-K, major disclosures)")
    print(f"   🤝 M&A activity and acquisitions")
    print(f"   🔮 Forward-looking outlook statements")
    
    print(f"\n📰 Ready to generate strategic banking newsletter!")
    print(f"📋 Next steps:")
    print(f"   1. Generate newsletter: python3 news_agent.py --newsletter")
    print(f"   2. Schedule weekly: python3 weekly_news_scheduler.py --day friday --time 17:00")
    print(f"   3. Add more banks: python3 news_agent.py --add 'Bank Name' 'TICKER' 2")
    
    return agent

def demo_banking_newsletter():
    """Generate a demo banking newsletter focused on strategic content"""
    
    print("\n🧪 Generating demo banking strategic newsletter...")
    
    # Setup if not already done
    agent = NewsAgent()
    if not agent.companies or len(agent.companies) < 20:
        print("Setting up top banks first...")
        agent = setup_top_banks_by_aum()
    
    # Generate newsletter
    newsletter_path = agent.run_weekly_newsletter()
    
    print(f"\n✅ Banking strategic newsletter generated!")
    print(f"📄 Check the file: {newsletter_path}")
    print(f"🎯 Focus: Strategic plans, executive interviews, filings, M&A")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup Top 25 Banks by AUM")
    parser.add_argument('--setup', action='store_true', help='Setup top 25 banks')
    parser.add_argument('--demo', action='store_true', help='Generate demo banking newsletter')
    parser.add_argument('--both', action='store_true', help='Setup and generate demo')
    
    args = parser.parse_args()
    
    if args.setup or args.both:
        setup_top_banks_by_aum()
    
    if args.demo or args.both:
        demo_banking_newsletter()
    
    if not any([args.setup, args.demo, args.both]):
        # Default behavior
        print("🏦 Top 25 Banks by AUM Setup")
        print("Choose an option:")
        print("  1. Setup top 25 banks")
        print("  2. Generate demo banking newsletter") 
        print("  3. Both")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            setup_top_banks_by_aum()
        elif choice == "2":
            demo_banking_newsletter()
        elif choice == "3":
            setup_top_banks_by_aum()
            demo_banking_newsletter()
        else:
            print("Invalid choice")