# Sports Betting Performance Tracking System

## Overview
This system automatically tracks all your daily predictions and calculates real-world performance by sport and bet type.

## How It Works

### 1. Daily Workflow
When you run `./run_all_daily.sh`, the system automatically:

1. **Updates results from previous day** - Fetches game results and marks predictions as won/lost
2. **Generates predictions** - Runs NHL, NBA, NCAA, and Soccer models
3. **Logs today's predictions** - Saves all high-confidence picks to database
4. **Shows performance summary** - Displays cumulative stats

### 2. Database
All data is stored in: `/Users/dickgibbons/sports-betting/betting_tracker.db`

Tracks:
- Every prediction made (date, sport, bet type, selection, odds, confidence)
- Actual results when games complete
- Win/loss/pending status
- Profit/loss for each bet

### 3. Manual Commands

#### Initialize database (first time only):
```bash
python3 track_performance.py init
```

#### Log predictions manually:
```bash
python3 log_daily_predictions.py 2025-11-26
```

#### Update results from previous day:
```bash
python3 track_performance.py update
```

#### View performance summary anytime:
```bash
python3 track_performance.py show
```

## Performance Metrics

The system calculates:

### Overall Stats
- Total bets placed
- Win/Loss/Pending count
- Win rate %
- Total profit/loss
- ROI %

### By Sport
- NHL
- NBA
- NCAA
- Soccer

### By Bet Type
- Money Line (ML)
- Spread
- Over/Under (Totals)
- Away Win

## What Gets Logged

Only **high-confidence predictions** are tracked:

### NHL
- Money Line picks with 90%+ confidence

### NBA
- Any picks with positive Expected Value (EV)

### NCAA
- All HIGH confidence situational bets
- Back-to-back advantages
- Rest advantages

### Soccer
- Picks with 90%+ confidence
- Primarily away wins

## Result Updates

### Currently Supported
- **NHL**: Automatic via NHL API (works great)
- **NBA**: Automatic via NBA API (works great)

### Needs Development
- **NCAA**: Manual updates needed (no API yet)
- **Soccer**: Manual updates needed (no API yet)

For sports without APIs, you can manually update results in the database until APIs are added.

## Example Output

```
================================================================================
SPORTS BETTING PERFORMANCE TRACKER
================================================================================

OVERALL PERFORMANCE:
  Total Bets: 50 (28W-22L-0P)
  Win Rate: 56.0%
  Total Staked: $5,000.00
  Total Profit: $+247.20
  ROI: +4.94%

================================================================================
PERFORMANCE BY SPORT
================================================================================

NHL:
  Bets: 25 (15W-10L-0P)
  Win Rate: 60.0%
  Profit: $+227.25
  ROI: +9.09%

NBA:
  Bets: 15 (8W-7L-0P)
  Win Rate: 53.3%
  Profit: $+45.45
  ROI: +3.03%

NCAA:
  Bets: 10 (5W-5L-0P)
  Win Rate: 50.0%
  Profit: $-25.50
  ROI: -2.55%
```

## Benefits

1. **Data-driven decisions**: See which sports/bet types are actually profitable
2. **Model validation**: Verify backtest results match real-world performance
3. **ROI tracking**: Know your exact return on investment
4. **Accountability**: Every prediction is logged and tracked
5. **Historical record**: Build a complete betting history

## Next Steps

After a few weeks of data:
- Analyze which models perform best
- Adjust bet sizing based on real ROI
- Drop unprofitable bet types
- Focus on highest-performing sports
- Compare backtest accuracy to live results
