# 📰 News Aggregator

Automated weekly news agent that searches for company news and creates personalized newsletters.

## 🚀 Features

- **Company Tracking**: Monitor news for multiple companies with priority levels
- **AI Analysis**: Uses OpenAI to analyze sentiment and relevance of articles
- **Weekly Newsletters**: Automatically generates comprehensive weekly digest
- **Email Delivery**: Optional email delivery of newsletters
- **Scheduling**: Automated weekly scheduling with customizable timing
- **Web Search Integration**: Searches multiple news sources for comprehensive coverage

## 📁 Files

- `news_agent.py` - Main news aggregation and newsletter generation engine
- `weekly_news_scheduler.py` - Automated scheduler for weekly newsletter delivery  
- `setup_news_agent.py` - Quick setup script with sample companies
- `README.md` - This documentation file

## 🛠️ Setup

### 1. Quick Setup with Sample Companies

```bash
cd "/Users/richardgibbons/soccer betting python/news aggregator"
python setup_news_agent.py --both
```

This will:
- Add sample companies (Apple, Microsoft, Tesla, etc.)
- Generate a demo newsletter
- Show you how the system works

### 2. Manual Company Configuration

```bash
python news_agent.py --config
```

Interactive mode to add/remove companies:
```
>>> add Apple AAPL 1
>>> add Microsoft MSFT 1  
>>> add Tesla TSLA 2
>>> list
>>> exit
```

### 3. Command Line Company Management

```bash
# Add a high-priority company
python news_agent.py --add "Apple" "AAPL" 1

# Add medium priority company
python news_agent.py --add "Tesla" "TSLA" 2

# List all tracked companies
python news_agent.py --list

# Remove a company
python news_agent.py --remove "Apple"
```

## 📰 Generate Newsletter

### One-time Generation
```bash
python news_agent.py --newsletter
```

### With AI Analysis (Optional)
```bash
python news_agent.py --newsletter --openai-key "your-openai-api-key"
```

## 📅 Automated Weekly Scheduling

### Basic Scheduling
```bash
python weekly_news_scheduler.py --day monday --time 09:00
```

### With Email Delivery
```bash
python weekly_news_scheduler.py --day friday --time 17:00 --email your@email.com --openai-key "your-key"
```

### Test Mode (Run Once)
```bash
python weekly_news_scheduler.py --test
```

## ⚙️ Configuration

### Company Priority Levels
- **Priority 1 (🔴)**: High priority - Most important companies
- **Priority 2 (🟡)**: Medium priority - Important but not critical
- **Priority 3 (🟢)**: Low priority - Background monitoring

### Email Setup (Optional)
To enable email delivery, update `weekly_news_scheduler.py`:

```python
email_config = {
    'smtp_server': 'smtp.gmail.com',      # Your email provider
    'smtp_port': 587,
    'smtp_user': 'your_email@gmail.com',  # Your email
    'smtp_password': 'your_app_password', # App password
    'recipient_email': args.email
}
```

### OpenAI Integration (Optional)
For AI-powered analysis:
1. Get OpenAI API key from https://openai.com/api/
2. Use `--openai-key` parameter or set environment variable
3. Enables sentiment analysis and relevance scoring

## 📊 Newsletter Format

The generated newsletter includes:

1. **Executive Summary** - Overview of companies with news
2. **Company Sections** - Organized by priority level
   - Sentiment overview (positive/negative/neutral)
   - Top 5 most relevant articles per company
   - Article summaries with AI analysis
   - Source links and publication dates
3. **Configuration Summary** - Current tracking settings

## 🗂️ File Structure

```
news aggregator/
├── news_agent.py              # Main news engine
├── weekly_news_scheduler.py   # Automated scheduler
├── setup_news_agent.py        # Setup utility
├── README.md                  # Documentation
└── newsletters/               # Generated newsletters
    ├── company_config.json    # Company configuration
    ├── weekly_newsletter_YYYYMMDD.txt
    └── ...
```

## 🎯 Example Usage Workflow

1. **Initial Setup**:
   ```bash
   python setup_news_agent.py --setup
   ```

2. **Generate Test Newsletter**:
   ```bash
   python news_agent.py --newsletter
   ```

3. **Start Weekly Automation**:
   ```bash
   python weekly_news_scheduler.py --day monday --time 09:00
   ```

4. **Add More Companies**:
   ```bash
   python news_agent.py --add "Amazon" "AMZN" 1
   python news_agent.py --add "Netflix" "NFLX" 2
   ```

## 🔧 Customization

### Adding Custom Keywords
When adding companies, you can specify custom search terms:
```python
agent.add_company(
    name="Apple", 
    ticker="AAPL",
    keywords=["Apple Inc", "iPhone", "iPad", "Tim Cook", "iOS"],
    priority=1
)
```

### Scheduling Options
- **Days**: monday, tuesday, wednesday, thursday, friday, saturday, sunday
- **Times**: Any time in HH:MM format (24-hour)
- **Multiple Schedules**: Run the scheduler multiple times for different schedules

## 🚨 Requirements

- Python 3.7+
- `requests` - For web API calls
- `schedule` - For automated scheduling  
- `openai` - For AI analysis (optional)
- `smtplib` - For email delivery (built-in)

Install dependencies:
```bash
pip install requests schedule openai
```

## 📝 Notes

- News search uses web search functionality for comprehensive coverage
- Articles are filtered by relevance score (minimum 50%)
- Duplicate articles are automatically removed
- Rate limiting prevents API overuse
- All newsletters are saved locally regardless of email settings

## 🔮 Future Enhancements

- Multiple news API integrations
- Custom email templates
- Slack/Discord integration
- RSS feed generation
- Advanced filtering options
- Mobile app notifications