# PGA Tour Prediction Model - Data Sources Research

## Summary

For building a winner/top-10 prediction model, you'll need historical tournament results, player statistics (especially Strokes Gained metrics), and course-specific data. Below are the available options ranked by quality and accessibility.

---

## Tier 1: Premium APIs (Best Data Quality)

### DataGolf (Recommended)
- **Website**: https://datagolf.com
- **Pricing**: 
  - Scratch Basic: $190/year - Model predictions, odds screens, historical stats
  - Scratch PLUS: $270/year - Everything in Basic + **API Access**, raw scores/stats archive, tournament simulators
- **Key Features**:
  - Pre-tournament probabilistic forecasts (win, top 5/10/20, make cut)
  - Strokes Gained breakdowns by category (OTT, APP, ARG, PUTT)
  - Course history and fit adjustments
  - Historical raw data from 22+ global tours going back to 2004
  - Live tournament stats and predictions
  - Betting odds comparison across 8+ sportsbooks
- **Python Library**: Unofficial wrapper available at https://github.com/coreyjs/data-golf-api
- **Verdict**: Best bang for buck for serious modeling. Their model predictions can serve as a benchmark.

### SportsDataIO / FantasyData
- **Website**: https://sportsdata.io/pga-golf-api
- **Pricing**: Contact for quote (enterprise-level)
- **Key Features**:
  - Real-time scoring and leaderboards
  - Historical database going back decades
  - Player profiles and season statistics
  - Betting odds integration
- **Verdict**: Overkill unless you need real-time data feeds for production apps.

### Sportradar
- **Website**: https://developer.sportradar.com/golf/reference/golf-overview
- **Pricing**: Trial available, paid plans (enterprise-level)
- **Key Features**:
  - Hole-by-hole coverage for PGA, DP World, LIV, LPGA, Champions Tour
  - Push feeds for real-time updates
  - Official World Golf Rankings
  - Comprehensive player statistics
- **Verdict**: Industry standard for media/betting companies. Expensive for individual use.

---

## Tier 2: Free Datasets (Good Starting Point)

### Kaggle Datasets

1. **PGA Tour Golf Data (2015-2022)** - Most comprehensive free option
   - URL: https://www.kaggle.com/datasets/robikscube/pga-tour-golf-data-20152022
   - Contains: Tournament results, player stats
   - Starter notebook available

2. **PGA Tour Historical Results (2009-2022)**
   - URL: https://www.kaggle.com/datasets/jasonyli0/pga-tour-past-results
   - Contains: Tournament finishes, scores

3. **PGA Tour Data (2010-2018)**
   - URL: https://www.kaggle.com/datasets/jmpark746/pga-tour-data-2010-2018
   - Contains: Player statistics by season

### GitHub Projects with Data

1. **daronprater/PGA-Tour-Data-Science-Project**
   - URL: https://github.com/daronprater/PGA-Tour-Data-Science-Project
   - Contains: Web scraper for pgatour.com, cleaned CSV data (2007-2017)
   - Includes: ML classification model for predicting tournament winners
   - Great reference for feature engineering

2. **codyheiser/pga-data**
   - URL: https://github.com/codyheiser/pga-data
   - Contains: Scraper for historical scores and finishes
   - Uses PGA Tour's JSON endpoints

3. **krissysantucci/Golf_Masters**
   - URL: https://github.com/krissysantucci/Golf_Masters
   - Contains: Analysis specifically for predicting Masters top 10
   - Good reference for feature selection

---

## Tier 3: Web Scraping (Most Up-to-Date)

### PGA Tour Website (pgatour.com/stats)
- **Approach**: Build custom scraper using BeautifulSoup/Selenium
- **Data Available**:
  - 100+ statistics per player per season
  - Strokes Gained categories
  - Tournament results
  - Course-specific performance
- **Challenges**:
  - Site structure changes periodically
  - May need to handle JavaScript rendering
  - Requires ongoing maintenance
- **Existing Scrapers**: See GitHub projects above for reference code

### ESPN Leaderboards
- **URL**: espn.com/golf/leaderboard
- **Use Case**: Live tournament tracking
- **GitHub Reference**: https://github.com/jmstjordan/PGALiveLeaderboard

---

## Recommended Approach for Your Model

### Phase 1: Proof of Concept (Free)
1. Download Kaggle dataset (2015-2022)
2. Supplement with web scraping for 2023-2025 data
3. Build initial model to validate approach

### Phase 2: Production Model (Paid)
1. Subscribe to DataGolf PLUS ($270/year)
2. Access their API for:
   - Comprehensive historical data
   - Strokes Gained breakdowns
   - Course fit adjustments
   - Pre-tournament predictions (use as features or benchmark)

---

## Key Statistics to Collect

### Strokes Gained (Most Predictive)
- SG: Off-the-Tee (SG_OTT)
- SG: Approach (SG_APP)
- SG: Around-the-Green (SG_ARG)
- SG: Putting (SG_PUTT)
- SG: Total (SG_TOTAL)
- SG: Tee-to-Green (SG_T2G)

### Traditional Stats
- Driving Distance
- Driving Accuracy %
- Greens in Regulation %
- Scrambling %
- Putts per Round
- Scoring Average

### Form Indicators
- Recent results (last 5-10 events)
- Rolling SG averages (12/24/36 rounds)
- Course history at venue
- World Golf Ranking

### Course-Specific
- Course length
- Rough difficulty
- Green speed/complexity
- Historical winning scores
- Weather conditions (wind, altitude)

---

## Next Steps

1. **Decision**: Free (Kaggle + scraping) or Paid (DataGolf)?
2. **Data Collection**: Set up pipeline for chosen approach
3. **Feature Engineering**: Build player form metrics, course fit scores
4. **Model Training**: Start with gradient boosting (XGBoost/LightGBM)
5. **Validation**: Backtest on 2023-2024 tournaments

Let me know which direction you'd like to take!
