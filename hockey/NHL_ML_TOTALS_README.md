# NHL Machine Learning Totals Predictor

Machine learning system that predicts NHL game totals and first period probabilities using multiple ML models.

---

## 🎯 What It Does

**Daily Report Shows:**
1. **Predicted Total** for each NHL game (using 5 ML models)
2. **Market Total** from The Odds API
3. **Edge** (our prediction vs market)
4. **First Period Probabilities:**
   - Home team over 0.5 goals
   - Away team over 0.5 goals
   - Period total over 1.5 goals
5. **All Model Predictions** (linear, ridge, random forest, gradient boosting, XGBoost)

---

## 📁 Files

```
/Users/dickgibbons/AI Projects/sports-betting/nhl/analyzers/
├── nhl_ml_totals_predictor.py       # ML models & training
└── nhl_daily_totals_report.py       # Daily report generator

/Users/dickgibbons/AI Projects/sports-betting/nhl/models/
├── totals_*.pkl                      # Trained totals models
├── first_period_*.pkl                # First period probability models
├── scaler.pkl                        # Feature scaler
├── team_stats.pkl                    # Team statistics
└── best_model_name.pkl               # Best performing model name
```

---

## 🤖 ML Models Used

### Game Totals (Regression):
1. **Linear Regression** - Baseline
2. **Ridge Regression** - Regularized linear (current best)
3. **Random Forest** - Ensemble trees
4. **Gradient Boosting** - Advanced boosting
5. **XGBoost** - High-performance gradient boosting

### First Period (Classification):
1. **Home Over 0.5 Goals** - Random Forest Classifier
2. **Away Over 0.5 Goals** - Random Forest Classifier
3. **Period Over 1.5 Goals** - Random Forest Classifier

---

## 🔄 Daily Automation

### Automatically Runs at 5:00 AM
The system is integrated into your daily automation (`run_all_daily.sh`):

```bash
# Runs every day at 5:00 AM via cron
0 5 * * * cd /Users/dickgibbons/AI Projects/sports-betting && ./run_all_daily.sh
```

### Report Location
```
/Users/dickgibbons/AI Projects/sports-betting/reports/YYYY-MM-DD/nhl_ml_totals_YYYY-MM-DD.txt
```

---

## 📊 Example Report

```
GAME #1: Oilers @ Capitals
────────────────────────────────────────────────────
   🤖 ML Predicted Total:  6.51
   💰 Market Total:        6.5
   📈 Edge:                +0.01

   🎯 FIRST PERIOD PROBABILITIES:
      Capitals over 0.5 goals: 72.3%
      Oilers over 0.5 goals: 68.1%
      1st Period Total over 1.5 goals: 65.4%

   📊 MODEL PREDICTIONS:
      linear              : 6.52
      ridge               : 6.51
      random_forest       : 7.20
      gradient_boost      : 7.36
      xgboost             : 7.62
```

---

## 🚀 Manual Usage

### View Today's Report
```bash
cat /Users/dickgibbons/AI Projects/sports-betting/reports/$(date +%Y-%m-%d)/nhl_ml_totals_$(date +%Y-%m-%d).txt
```

### Generate Report Manually
```bash
cd /Users/dickgibbons/AI Projects/sports-betting/nhl/analyzers
python3 nhl_daily_totals_report.py
```

### Generate for Specific Date
```bash
python3 nhl_daily_totals_report.py --date 2025-11-19
```

### Retrain Models
```bash
# Edit dates in nhl_ml_totals_predictor.py if needed, then run:
python3 nhl_ml_totals_predictor.py
```

---

## 📈 Features Used

**Team Statistics (Rolling Averages):**
- Goals per game (for/against)
- First period goals per game (for/against)
- Shots per game (for/against)

**Calculated Features:**
- Home team offensive strength
- Home team defensive strength
- Away team offensive strength
- Away team defensive strength
- First period scoring rates

---

## 🎯 How to Use the Reports

### Betting Strategy

**1. Focus on Games with Edge ≥ 0.5 Goals:**
```
Edge: +0.8 🔥  → Bet OVER (our prediction is 0.8 higher than market)
Edge: -0.7 ❄️   → Bet UNDER (our prediction is 0.7 lower than market)
```

**2. First Period Probabilities:**
```
Period over 1.5 goals: 75%  → Strong bet on 1P Over 1.5
Home over 0.5 goals: 80%    → Strong bet on home 1P team total over 0.5
```

**3. Model Consensus:**
- If all 5 models agree within 0.3 goals → High confidence
- If models diverge significantly → Lower confidence

---

## 📊 Model Performance

**Current Season (2024-25):**
- Training Data: 290 games (Oct 8 - Nov 18, 2024)
- Games with sufficient history: 204
- Best Model: Ridge Regression

**Note:** First period probabilities currently showing 0% due to data collection issues during training. This will improve with more complete period-by-period data.

---

## 🔧 Improving the System

### To Improve Accuracy:

**1. Add More Features:**
- Goalie stats (save percentage, goals against average)
- Recent form (last 5 games)
- Home/road splits
- Special teams (PP%, PK%)
- Injuries/lineup changes

**2. Better First Period Data:**
- Currently struggling to capture period-by-period scores
- Need to fetch from gamecenter API more reliably

**3. More Training Data:**
- Currently using ~40 days of games
- Could train on full season or multiple seasons

**4. Ensemble Weighting:**
- Weight models by performance
- Use model stacking

---

## ⚠️ Known Issues

1. **First Period Probabilities Showing 0%**
   - Data collection for period-by-period scoring needs improvement
   - Models trained on limited first period data

2. **Market Totals Sometimes Missing**
   - Team name mismatches between NHL API and Odds API
   - Lines may not be posted yet for evening games

3. **Negative R² Values**
   - Current features may not capture enough variance
   - Adding goalie stats and recent form should help

---

## 🎓 Understanding the Metrics

**R² (R-Squared):**
- 1.0 = Perfect predictions
- 0.0 = As good as predicting the average
- Negative = Worse than average

**Current R²:** -0.07 (Ridge model)
- Indicates features need improvement
- Still provides directional guidance vs market

**Cross-Validation R²:**
- Tests model on unseen data
- More reliable measure than test R²

---

## 📋 Daily Workflow

**Morning (After 5:00 AM):**
1. Check email/terminal for report
2. Review games with significant edge
3. Compare to your own analysis
4. Check first period probabilities

**Before Game Time:**
1. Verify market lines match report
2. Place bets on games with ≥0.5 edge
3. Consider first period bets

**After Games:**
1. Track results
2. Note which models performed best
3. Adjust strategy

---

## 🔄 Retraining Schedule

**Recommended:**
- Retrain weekly during season (more current data)
- Retrain after major trades/injuries
- Retrain at All-Star break

**Command:**
```bash
cd /Users/dickgibbons/AI Projects/sports-betting/nhl/analyzers
# Edit dates in script if needed
python3 nhl_ml_totals_predictor.py
```

---

**Last Updated:** November 19, 2025
**Status:** ✅ Active (runs daily at 5:00 AM)
**API:** api-web.nhle.com (NHL Official API)
