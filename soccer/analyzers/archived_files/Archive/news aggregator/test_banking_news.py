#!/usr/bin/env python3
"""
Test Banking News Generator

Creates realistic banking news articles for demonstration
"""

from news_agent import NewsAgent
from datetime import datetime, timedelta
import json

def create_sample_banking_newsletter():
    """Create a banking newsletter with sample realistic articles"""
    
    print("🏦 Creating Sample Banking Newsletter with Realistic Articles...")
    
    # Sample banking news articles
    banking_articles = {
        "JPMorgan Chase": [
            {
                "title": "JPMorgan CEO Jamie Dimon Discusses Strategic Priorities in Q3 Earnings Call",
                "url": "https://www.bloomberg.com/news/jpmorgan-strategy-2025",
                "published_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                "source": "Bloomberg",
                "description": "JPMorgan Chase CEO Jamie Dimon outlined the bank's strategic priorities during the Q3 earnings call, focusing on digital transformation and expanding wealth management services. The bank plans to invest $15 billion in technology initiatives over the next two years.",
                "sentiment": "positive",
                "relevance_score": 0.95
            },
            {
                "title": "JPMorgan Plans Major Technology Investment in 2025",
                "url": "https://www.reuters.com/business/jpmorgan-tech-investment", 
                "published_date": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                "source": "Reuters",
                "description": "JPMorgan Chase announced plans to invest heavily in AI-powered trading systems and customer service automation, positioning itself as a leader in financial technology innovation.",
                "sentiment": "positive", 
                "relevance_score": 0.88
            }
        ],
        "Bank of America": [
            {
                "title": "Bank of America CEO Brian Moynihan Outlines Digital Banking Strategy",
                "url": "https://www.wsj.com/articles/bofa-digital-strategy",
                "published_date": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                "source": "Wall Street Journal", 
                "description": "Bank of America CEO Brian Moynihan detailed the bank's comprehensive digital transformation strategy, emphasizing mobile banking expansion and AI integration to enhance customer experience.",
                "sentiment": "positive",
                "relevance_score": 0.92
            }
        ],
        "Wells Fargo": [
            {
                "title": "Wells Fargo CEO Charlie Scharf Discusses Regulatory Progress and Strategic Focus",
                "url": "https://www.ft.com/content/wells-fargo-regulatory-update",
                "published_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                "source": "Financial Times",
                "description": "Wells Fargo CEO Charlie Scharf provided updates on regulatory compliance progress and outlined strategic initiatives to rebuild customer trust and expand market share in consumer banking.",
                "sentiment": "neutral",
                "relevance_score": 0.86
            }
        ],
        "Citigroup": [
            {
                "title": "Citigroup CEO Jane Fraser Announces Organizational Restructuring Plan",
                "url": "https://www.cnbc.com/2025/09/08/citi-restructuring-2025.html",
                "published_date": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'),
                "source": "CNBC",
                "description": "Citigroup CEO Jane Fraser unveiled a comprehensive organizational restructuring plan aimed at simplifying operations and improving efficiency across global markets, including significant technology investments.",
                "sentiment": "positive",
                "relevance_score": 0.91
            }
        ],
        "Goldman Sachs": [
            {
                "title": "Goldman Sachs CEO David Solomon Details Marcus Digital Banking Evolution", 
                "url": "https://www.marketwatch.com/story/goldman-marcus-strategy",
                "published_date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                "source": "MarketWatch",
                "description": "Goldman Sachs CEO David Solomon discussed the evolution of Marcus digital banking platform and strategic partnerships to expand consumer banking reach while maintaining the firm's investment banking leadership.",
                "sentiment": "positive",
                "relevance_score": 0.89
            }
        ]
    }
    
    # Generate formatted newsletter content
    newsletter_date = datetime.now().strftime('%B %d, %Y')
    week_start = (datetime.now() - timedelta(days=7)).strftime('%B %d')
    week_end = datetime.now().strftime('%B %d, %Y')
    
    newsletter_content = f"""
📰 WEEKLY BANKING STRATEGIC NEWS DIGEST 📰
==========================================
📅 Week of {week_start} - {week_end}
🤖 Generated on {newsletter_date}

📊 EXECUTIVE SUMMARY:
=========================
🏢 Major Banks with Strategic News: 5
📰 Total Strategic Articles Analyzed: 6
🎯 Focus: Strategic plans, CEO interviews, transformations

🔴 JPMORGAN CHASE (JPM)
===============
📊 Sentiment Overview: ✅2 Positive

   1. ✅ JPMorgan CEO Jamie Dimon Discusses Strategic Priorities in Q3 Earnings Call
      📅 {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')} | 📰 Bloomberg
      📝 JPMorgan Chase CEO Jamie Dimon outlined the bank's strategic priorities during the Q3 earnings call, focusing on digital transformation and expanding wealth management services. The bank plans to invest $15 billion in technology initiatives over the next two years.
      🔗 https://www.bloomberg.com/news/jpmorgan-strategy-2025
      📊 Relevance: 95.0%

   2. ✅ JPMorgan Plans Major Technology Investment in 2025
      📅 {(datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')} | 📰 Reuters
      📝 JPMorgan Chase announced plans to invest heavily in AI-powered trading systems and customer service automation, positioning itself as a leader in financial technology innovation.
      🔗 https://www.reuters.com/business/jpmorgan-tech-investment
      📊 Relevance: 88.0%


🔴 BANK OF AMERICA (BAC)
================
📊 Sentiment Overview: ✅1 Positive

   1. ✅ Bank of America CEO Brian Moynihan Outlines Digital Banking Strategy
      📅 {(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')} | 📰 Wall Street Journal
      📝 Bank of America CEO Brian Moynihan detailed the bank's comprehensive digital transformation strategy, emphasizing mobile banking expansion and AI integration to enhance customer experience.
      🔗 https://www.wsj.com/articles/bofa-digital-strategy
      📊 Relevance: 92.0%


🔴 WELLS FARGO (WFC)
============
📊 Sentiment Overview: ➖1 Neutral

   1. ➖ Wells Fargo CEO Charlie Scharf Discusses Regulatory Progress and Strategic Focus
      📅 {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')} | 📰 Financial Times
      📝 Wells Fargo CEO Charlie Scharf provided updates on regulatory compliance progress and outlined strategic initiatives to rebuild customer trust and expand market share in consumer banking.
      🔗 https://www.ft.com/content/wells-fargo-regulatory-update
      📊 Relevance: 86.0%


🔴 CITIGROUP (C)
=========
📊 Sentiment Overview: ✅1 Positive

   1. ✅ Citigroup CEO Jane Fraser Announces Organizational Restructuring Plan
      📅 {(datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')} | 📰 CNBC
      📝 Citigroup CEO Jane Fraser unveiled a comprehensive organizational restructuring plan aimed at simplifying operations and improving efficiency across global markets, including significant technology investments.
      🔗 https://www.cnbc.com/2025/09/08/citi-restructuring-2025.html
      📊 Relevance: 91.0%


🔴 GOLDMAN SACHS (GS)
=============
📊 Sentiment Overview: ✅1 Positive

   1. ✅ Goldman Sachs CEO David Solomon Details Marcus Digital Banking Evolution
      📅 {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')} | 📰 MarketWatch
      📝 Goldman Sachs CEO David Solomon discussed the evolution of Marcus digital banking platform and strategic partnerships to expand consumer banking reach while maintaining the firm's investment banking leadership.
      🔗 https://www.marketwatch.com/story/goldman-marcus-strategy
      📊 Relevance: 89.0%


🎯 KEY STRATEGIC THEMES:
========================
🤖 Digital Transformation: All 5 banks highlighting AI and technology investments
💼 Leadership Updates: CEO interviews and strategic communications
📊 Organizational Changes: Restructuring and efficiency initiatives  
🏦 Consumer Banking: Focus on digital banking and customer experience
💰 Technology Investment: Major capital allocation to fintech initiatives

🔧 NEWSLETTER SETTINGS:
=======================
📈 High Priority: 5 companies (Top banks by AUM)
🎯 Strategic Focus: CEO interviews, earnings calls, transformations, filings
📊 Article Threshold: 50%+ relevance score for strategic content

---
🤖 Automated by Banking News Agent | Next update: {(datetime.now() + timedelta(days=7)).strftime('%B %d, %Y')}
"""
    
    # Save the newsletter
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"banking_strategic_newsletter_{date_str}.txt"
    filepath = f"/Users/richardgibbons/soccer betting python/news aggregator/newsletters/{filename}"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(newsletter_content)
    
    print(f"✅ Banking Strategic Newsletter Created!")
    print(f"📄 File: {filepath}")
    print(f"🎯 Coverage: 5 major banks with 6 strategic articles")
    print(f"🔍 Focus: CEO interviews, strategic plans, digital transformation")
    
    return filepath

if __name__ == "__main__":
    create_sample_banking_newsletter()