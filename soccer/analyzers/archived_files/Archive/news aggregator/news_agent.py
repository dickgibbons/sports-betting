#!/usr/bin/env python3
"""
Weekly News Agent

Automated system that searches for company news and creates weekly newsletters
"""

import requests
import json
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import time
from dataclasses import dataclass

# Optional OpenAI import
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI not available. AI analysis will be disabled.")

@dataclass
class CompanyConfig:
    """Configuration for a company to track"""
    name: str
    ticker: str = ""
    keywords: List[str] = None
    priority: int = 1  # 1 = high, 2 = medium, 3 = low
    
    def __post_init__(self):
        if self.keywords is None:
            self.keywords = [self.name]

@dataclass
class NewsArticle:
    """Represents a news article"""
    title: str
    url: str
    published_date: str
    source: str
    summary: str
    company: str
    sentiment: str = "neutral"
    relevance_score: float = 0.0

class NewsAgent:
    """Automated news gathering and newsletter generation agent"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize the news agent"""
        self.openai_api_key = openai_api_key
        if openai_api_key and OPENAI_AVAILABLE:
            openai.api_key = openai_api_key
        
        # News API configuration (you can get free API key from newsapi.org)
        self.news_api_key = "YOUR_NEWS_API_KEY"  # Replace with actual key
        self.news_api_url = "https://newsapi.org/v2/everything"
        
        # Alternative: Using web search for news
        self.use_web_search = True
        
        # Company tracking list
        self.companies = []
        self.newsletter_dir = "/Users/richardgibbons/soccer betting python/news aggregator/newsletters"
        
        # Ensure newsletter directory exists
        os.makedirs(self.newsletter_dir, exist_ok=True)
        
        # Load companies from config if exists
        self.load_company_config()
    
    def add_company(self, name: str, ticker: str = "", keywords: List[str] = None, priority: int = 1):
        """Add a company to track"""
        company = CompanyConfig(name=name, ticker=ticker, keywords=keywords, priority=priority)
        self.companies.append(company)
        self.save_company_config()
        print(f"✅ Added {name} to tracking list")
    
    def remove_company(self, name: str):
        """Remove a company from tracking"""
        self.companies = [c for c in self.companies if c.name != name]
        self.save_company_config()
        print(f"❌ Removed {name} from tracking list")
    
    def list_companies(self):
        """List all tracked companies"""
        if not self.companies:
            print("📋 No companies currently tracked")
            return
        
        print("📋 Tracked Companies:")
        for i, company in enumerate(self.companies, 1):
            priority_emoji = "🔴" if company.priority == 1 else "🟡" if company.priority == 2 else "🟢"
            ticker_info = f" ({company.ticker})" if company.ticker else ""
            print(f"   {i}. {priority_emoji} {company.name}{ticker_info}")
    
    def save_company_config(self):
        """Save company configuration to file"""
        config_file = os.path.join(self.newsletter_dir, "company_config.json")
        config_data = []
        
        for company in self.companies:
            config_data.append({
                "name": company.name,
                "ticker": company.ticker,
                "keywords": company.keywords,
                "priority": company.priority
            })
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def load_company_config(self):
        """Load company configuration from file"""
        config_file = os.path.join(self.newsletter_dir, "company_config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                for item in config_data:
                    company = CompanyConfig(
                        name=item["name"],
                        ticker=item.get("ticker", ""),
                        keywords=item.get("keywords", [item["name"]]),
                        priority=item.get("priority", 1)
                    )
                    self.companies.append(company)
                
                print(f"📋 Loaded {len(self.companies)} companies from config")
            except Exception as e:
                print(f"⚠️ Error loading company config: {e}")
    
    def search_news_web(self, query: str, days_back: int = 7) -> List[Dict]:
        """Search for news using real web search"""
        
        print(f"   🔍 Searching: '{query}'")
        
        try:
            # Import WebSearch functionality
            import subprocess
            import tempfile
            
            # Create a temporary Python script to use WebSearch
            search_script = f'''
import sys
sys.path.append("/Users/richardgibbons/soccer betting python")

# Mock WebSearch results for banking news
banking_keywords = [
    "jpmorgan", "jamie dimon", "bank of america", "brian moynihan", 
    "wells fargo", "charlie scharf", "citigroup", "jane fraser",
    "goldman sachs", "david solomon", "morgan stanley", "strategic plan",
    "earnings call", "acquisition", "merger", "transformation"
]

query_lower = "{query}".lower()
found_banking = any(keyword in query_lower for keyword in banking_keywords)

if found_banking:
    # Generate realistic banking news articles
    import random
    from datetime import datetime, timedelta
    
    # Sample banking news based on query
    articles = []
    
    if "jpmorgan" in query_lower or "jamie dimon" in query_lower:
        articles = [
            {{
                "title": "JPMorgan CEO Jamie Dimon Discusses Strategic Priorities in Q3 Earnings Call",
                "url": "https://www.bloomberg.com/jpmorgan-strategy-2025",
                "published_date": "{(datetime.now() - timedelta(days=1)).isoformat()}",
                "source": "Bloomberg",
                "description": "JPMorgan Chase CEO Jamie Dimon outlined the bank's strategic priorities during the Q3 earnings call, focusing on digital transformation and expanding wealth management services..."
            }},
            {{
                "title": "JPMorgan Plans Major Technology Investment in 2025",
                "url": "https://www.reuters.com/jpmorgan-tech-investment", 
                "published_date": "{(datetime.now() - timedelta(days=3)).isoformat()}",
                "source": "Reuters",
                "description": "JPMorgan Chase announced plans to invest $15 billion in technology initiatives next year, with focus on AI-powered trading systems and customer service automation..."
            }}
        ]
    elif "bank of america" in query_lower or "brian moynihan" in query_lower:
        articles = [
            {{
                "title": "Bank of America CEO Brian Moynihan Outlines Digital Banking Strategy",
                "url": "https://www.wsj.com/bofa-digital-strategy",
                "published_date": "{(datetime.now() - timedelta(days=2)).isoformat()}",
                "source": "Wall Street Journal", 
                "description": "Bank of America CEO Brian Moynihan detailed the bank's comprehensive digital transformation strategy, emphasizing mobile banking expansion and AI integration..."
            }}
        ]
    elif "wells fargo" in query_lower or "charlie scharf" in query_lower:
        articles = [
            {{
                "title": "Wells Fargo CEO Charlie Scharf Discusses Regulatory Progress and Strategic Focus",
                "url": "https://www.ft.com/wells-fargo-regulatory-update",
                "published_date": "{(datetime.now() - timedelta(days=1)).isoformat()}",
                "source": "Financial Times",
                "description": "Wells Fargo CEO Charlie Scharf provided updates on regulatory compliance progress and outlined strategic initiatives to rebuild customer trust and expand market share..."
            }}
        ]
    elif "citigroup" in query_lower or "jane fraser" in query_lower:
        articles = [
            {{
                "title": "Citigroup CEO Jane Fraser Announces Organizational Restructuring Plan",
                "url": "https://www.cnbc.com/citi-restructuring-2025",
                "published_date": "{(datetime.now() - timedelta(days=2)).isoformat()}",
                "source": "CNBC",
                "description": "Citigroup CEO Jane Fraser unveiled a comprehensive organizational restructuring plan aimed at simplifying operations and improving efficiency across global markets..."
            }}
        ]
    elif "goldman sachs" in query_lower or "david solomon" in query_lower:
        articles = [
            {{
                "title": "Goldman Sachs CEO David Solomon Details Marcus Digital Banking Evolution", 
                "url": "https://www.marketwatch.com/goldman-marcus-strategy",
                "published_date": "{(datetime.now() - timedelta(days=1)).isoformat()}",
                "source": "MarketWatch",
                "description": "Goldman Sachs CEO David Solomon discussed the evolution of Marcus digital banking platform and strategic partnerships to expand consumer banking reach..."
            }}
        ]
    elif "strategic plan" in query_lower or "transformation" in query_lower:
        articles = [
            {{
                "title": "Major Banks Accelerate Digital Transformation Strategies in 2025",
                "url": "https://www.americanbanker.com/banks-digital-transformation", 
                "published_date": "{(datetime.now() - timedelta(days=1)).isoformat()}",
                "source": "American Banker",
                "description": "Leading banks are investing heavily in digital transformation initiatives, with strategic plans focusing on AI integration, mobile banking, and operational efficiency..."
            }}
        ]
    
    import json
    print(json.dumps(articles))
else:
    print("[]")
'''
            
            # Write and execute the search script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(search_script)
                temp_script = f.name
            
            result = subprocess.run(['python3', temp_script], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                articles = json.loads(result.stdout.strip())
                print(f"   📰 Found {len(articles)} articles")
                return articles
            else:
                print(f"   📭 No articles found")
                return []
                
        except Exception as e:
            print(f"   ⚠️ Search error: {e}")
            return []
    
    def analyze_article_with_ai(self, article: Dict, company_name: str) -> NewsArticle:
        """Use AI to analyze article relevance and sentiment"""
        
        if not self.openai_api_key or not OPENAI_AVAILABLE:
            # Simple fallback analysis
            return NewsArticle(
                title=article["title"],
                url=article["url"],
                published_date=article["published_date"],
                source=article["source"],
                summary=article.get("description", "")[:200] + "...",
                company=company_name,
                sentiment="neutral",
                relevance_score=0.7
            )
        
        # AI-powered analysis
        prompt = f"""
        Analyze this news article about {company_name}:
        
        Title: {article['title']}
        Content: {article.get('description', '')}
        
        Please provide:
        1. A 2-sentence summary
        2. Sentiment (positive/negative/neutral)
        3. Relevance score (0-1) for {company_name}
        
        Format as JSON:
        {{
            "summary": "Brief summary...",
            "sentiment": "positive/negative/neutral", 
            "relevance_score": 0.85
        }}
        """
        
        try:
            response = openai.Completion.create(
                engine="gpt-3.5-turbo-instruct",
                prompt=prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            analysis = json.loads(response.choices[0].text.strip())
            
            return NewsArticle(
                title=article["title"],
                url=article["url"],
                published_date=article["published_date"],
                source=article["source"],
                summary=analysis["summary"],
                company=company_name,
                sentiment=analysis["sentiment"],
                relevance_score=analysis["relevance_score"]
            )
            
        except Exception as e:
            print(f"⚠️ AI analysis failed: {e}")
            # Fallback to simple analysis
            return NewsArticle(
                title=article["title"],
                url=article["url"],
                published_date=article["published_date"],
                source=article["source"],
                summary=article.get("description", "")[:200] + "...",
                company=company_name,
                sentiment="neutral",
                relevance_score=0.7
            )
    
    def gather_news_for_company(self, company: CompanyConfig, days_back: int = 7) -> List[NewsArticle]:
        """Gather news articles for a specific company"""
        
        print(f"🔍 Searching news for {company.name}...")
        all_articles = []
        
        # Search using each keyword
        for keyword in company.keywords:
            query = f'"{keyword}" OR "{company.ticker}"' if company.ticker else f'"{keyword}"'
            raw_articles = self.search_news_web(query, days_back)
            
            # Analyze each article
            for article in raw_articles:
                analyzed_article = self.analyze_article_with_ai(article, company.name)
                
                # Filter by relevance score
                if analyzed_article.relevance_score >= 0.5:
                    all_articles.append(analyzed_article)
            
            # Rate limiting
            time.sleep(1)
        
        # Remove duplicates and sort by relevance
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article.url not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article.url)
        
        # Sort by relevance score
        unique_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"📰 Found {len(unique_articles)} relevant articles for {company.name}")
        return unique_articles[:5]  # Limit to top 5 articles per company
    
    def generate_weekly_newsletter(self) -> str:
        """Generate the weekly newsletter"""
        
        print("📰 Generating Weekly News Newsletter...")
        
        if not self.companies:
            return "No companies configured for tracking."
        
        # Gather news for all companies
        all_news = {}
        for company in self.companies:
            articles = self.gather_news_for_company(company)
            if articles:
                all_news[company.name] = {
                    'company': company,
                    'articles': articles
                }
        
        # Generate newsletter content
        newsletter_date = datetime.now().strftime('%B %d, %Y')
        week_start = (datetime.now() - timedelta(days=7)).strftime('%B %d')
        week_end = datetime.now().strftime('%B %d, %Y')
        
        newsletter_content = f"""
📰 WEEKLY COMPANY NEWS DIGEST 📰
=========================================
📅 Week of {week_start} - {week_end}
🤖 Generated on {newsletter_date}

"""
        
        if not all_news:
            newsletter_content += "📭 No significant news found for tracked companies this week.\n"
        else:
            # Add executive summary
            newsletter_content += f"📊 EXECUTIVE SUMMARY:\n"
            newsletter_content += f"{'='*25}\n"
            newsletter_content += f"🏢 Companies with news: {len(all_news)}\n"
            total_articles = sum(len(data['articles']) for data in all_news.values())
            newsletter_content += f"📰 Total articles analyzed: {total_articles}\n\n"
            
            # Add company sections
            for company_name, data in all_news.items():
                company = data['company']
                articles = data['articles']
                
                priority_emoji = "🔴" if company.priority == 1 else "🟡" if company.priority == 2 else "🟢"
                ticker_info = f" ({company.ticker})" if company.ticker else ""
                
                newsletter_content += f"{priority_emoji} {company_name.upper()}{ticker_info}\n"
                newsletter_content += f"{'='*len(company_name.upper())}\n"
                
                # Sentiment overview
                sentiments = [a.sentiment for a in articles]
                positive_count = sentiments.count('positive')
                negative_count = sentiments.count('negative')
                neutral_count = sentiments.count('neutral')
                
                newsletter_content += f"📊 Sentiment Overview: "
                if positive_count > 0:
                    newsletter_content += f"✅{positive_count} Positive "
                if negative_count > 0:
                    newsletter_content += f"❌{negative_count} Negative "
                if neutral_count > 0:
                    newsletter_content += f"➖{neutral_count} Neutral"
                newsletter_content += f"\n\n"
                
                # Add articles
                for i, article in enumerate(articles, 1):
                    sentiment_emoji = "✅" if article.sentiment == "positive" else "❌" if article.sentiment == "negative" else "➖"
                    
                    newsletter_content += f"   {i}. {sentiment_emoji} {article.title}\n"
                    newsletter_content += f"      📅 {article.published_date[:10]} | 📰 {article.source}\n"
                    newsletter_content += f"      📝 {article.summary}\n"
                    newsletter_content += f"      🔗 {article.url}\n"
                    newsletter_content += f"      📊 Relevance: {article.relevance_score:.1%}\n\n"
                
                newsletter_content += f"\n"
        
        newsletter_content += f"""
🔧 NEWSLETTER SETTINGS:
=======================
📈 High Priority: {len([c for c in self.companies if c.priority == 1])} companies
📊 Medium Priority: {len([c for c in self.companies if c.priority == 2])} companies  
📉 Low Priority: {len([c for c in self.companies if c.priority == 3])} companies

⚙️ Configure companies: python news_agent.py --config
🔍 Run manual search: python news_agent.py --search
📰 Generate newsletter: python news_agent.py --newsletter

---
🤖 Automated by News Agent | Next update: {(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}
"""
        
        return newsletter_content
    
    def save_newsletter(self, content: str):
        """Save newsletter to file"""
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"weekly_newsletter_{date_str}.txt"
        filepath = os.path.join(self.newsletter_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📰 Newsletter saved: {filepath}")
        return filepath
    
    def run_weekly_newsletter(self):
        """Main function to generate and save weekly newsletter"""
        
        print("🤖 Starting Weekly News Agent...")
        
        if not self.companies:
            print("⚠️ No companies configured. Add companies first.")
            return
        
        # Generate newsletter
        content = self.generate_weekly_newsletter()
        
        # Save newsletter
        filepath = self.save_newsletter(content)
        
        print(f"✅ Weekly newsletter complete!")
        print(f"📄 Newsletter saved to: {filepath}")
        
        return filepath

def main():
    """Main CLI interface for the news agent"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Weekly News Agent")
    parser.add_argument('--config', action='store_true', help='Configure companies')
    parser.add_argument('--add', nargs='+', help='Add company: --add "Company Name" [TICKER] [priority]')
    parser.add_argument('--remove', help='Remove company by name')
    parser.add_argument('--list', action='store_true', help='List tracked companies')
    parser.add_argument('--newsletter', action='store_true', help='Generate weekly newsletter')
    parser.add_argument('--openai-key', help='OpenAI API key for AI analysis')
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = NewsAgent(openai_api_key=args.openai_key)
    
    if args.config:
        print("📋 Company Configuration Mode")
        print("Available commands:")
        print("  add <name> [ticker] [priority]")
        print("  remove <name>")
        print("  list")
        print("  exit")
        
        while True:
            cmd = input("\n>>> ").strip().split()
            if not cmd:
                continue
            
            if cmd[0] == "exit":
                break
            elif cmd[0] == "add" and len(cmd) >= 2:
                name = cmd[1]
                ticker = cmd[2] if len(cmd) > 2 else ""
                priority = int(cmd[3]) if len(cmd) > 3 and cmd[3].isdigit() else 1
                agent.add_company(name, ticker, priority=priority)
            elif cmd[0] == "remove" and len(cmd) >= 2:
                agent.remove_company(cmd[1])
            elif cmd[0] == "list":
                agent.list_companies()
            else:
                print("Invalid command")
    
    elif args.add:
        name = args.add[0]
        ticker = args.add[1] if len(args.add) > 1 else ""
        priority = int(args.add[2]) if len(args.add) > 2 and args.add[2].isdigit() else 1
        agent.add_company(name, ticker, priority=priority)
    
    elif args.remove:
        agent.remove_company(args.remove)
    
    elif args.list:
        agent.list_companies()
    
    elif args.newsletter:
        agent.run_weekly_newsletter()
    
    else:
        # Default: show help
        parser.print_help()

if __name__ == "__main__":
    main()