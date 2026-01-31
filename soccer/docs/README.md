# Soccer Betting Predictor

A comprehensive Python system that uses the FootyStats API to predict soccer match outcomes for betting purposes using machine learning.

## 🎯 Features

- **Real-time API Integration**: Connects to FootyStats API for live match data
- **Machine Learning Models**: Uses Random Forest and Gradient Boosting for predictions
- **Betting Value Analysis**: Identifies value betting opportunities using Kelly Criterion
- **Comprehensive Feature Engineering**: 36+ features including odds, team stats, and match data
- **Risk Management**: Built-in bankroll management recommendations

## 📊 Model Performance

- **Random Forest**: 69.2% accuracy with cross-validation
- **Gradient Boosting**: 69.2% accuracy with cross-validation
- **Test Accuracy**: Up to 71% on unseen data

## 🗂️ Files

1. **`enhanced_soccer_predictor.py`** - Main production system
   - Full machine learning pipeline
   - Real-time predictions
   - Value betting analysis
   - Kelly Criterion for bet sizing

2. **`soccer_predictor_simple.py`** - Simplified testing version
   - API connection testing
   - Basic prediction logic
   - Data structure exploration

3. **`soccer_betting_predictor.py`** - Original comprehensive version
   - Advanced feature engineering
   - Multiple model support
   - Requires pandas (may have compatibility issues with Python 3.13)

4. **`debug_data.py`** - API data structure analyzer
   - Examines actual API response format
   - Useful for understanding available features

## 🚀 Quick Start

### Prerequisites

```bash
pip install requests scikit-learn joblib numpy
```

### Basic Usage

```python
from enhanced_soccer_predictor import BettingPredictor

# Initialize with your API key
predictor = BettingPredictor("your_api_key_here")

# Make a prediction
predictions = predictor.predict_match_outcome(
    home_odds=1.8,
    draw_odds=3.5, 
    away_odds=4.2
)

# Analyze betting value
value_analysis = predictor.analyze_betting_value(
    predictions, 1.8, 3.5, 4.2
)
```

### Run the Demo

```bash
python3 enhanced_soccer_predictor.py
```

## 📈 What the System Analyzes

### Input Features (36 total)
- **Match Odds**: Home, Draw, Away win probabilities
- **Over/Under Markets**: Goals and corners betting lines
- **Team Performance**: Points per game, recent form
- **Advanced Metrics**: Expected Goals (xG), possession, shots
- **Market Indicators**: BTTS odds, clean sheet probabilities

### Output Predictions
- **Match Outcome**: Home/Draw/Away with confidence scores
- **Value Bets**: Opportunities where model probability > implied odds probability
- **Kelly Criterion**: Optimal bet sizing as percentage of bankroll
- **Risk Assessment**: Confidence levels and uncertainty measures

## 💰 Value Betting Example

```
🏆 Liverpool vs Chelsea
📊 Odds - Home: 2.1, Draw: 3.2, Away: 3.4

GRADIENT_BOOSTING
Prediction: Away Win (Confidence: 0.432)
💰 Value Opportunities:
   Away Win: 38.1% value, Kelly: 17.3% of bankroll
```

## 🔧 API Configuration

The system uses FootyStats API with your provided key:
- **League**: Premier League (ID: 1625) - confirmed working
- **Rate Limiting**: 1 second between requests
- **Data Points**: 380 historical matches for training
- **Request Limit**: 1800 per hour

## ⚠️ Important Disclaimers

- **Educational Purpose**: This system is for learning and research only
- **Risk Warning**: Gambling involves risk - only bet what you can afford to lose
- **No Guarantees**: Past performance doesn't guarantee future results
- **External Factors**: Consider team news, injuries, and other factors not captured in historical data
- **Responsible Gaming**: Always practice responsible gambling habits

## 🔍 Technical Details

### Machine Learning Pipeline
1. **Data Collection**: Fetches historical match data via API
2. **Feature Engineering**: Extracts 36 numerical features from raw data  
3. **Model Training**: Trains ensemble models on historical outcomes
4. **Prediction**: Generates probability distributions for new matches
5. **Value Analysis**: Compares model probabilities to betting odds

### Model Architecture
- **Random Forest**: 100 trees, balanced class weights
- **Gradient Boosting**: 100 estimators, default parameters
- **Feature Scaling**: StandardScaler for numerical stability
- **Validation**: 5-fold cross-validation with stratified sampling

### Betting Strategy
- **Value Threshold**: Minimum 5% edge over implied probability
- **Kelly Criterion**: Optimal bet sizing with 25% maximum
- **Diversification**: Multiple models for consensus predictions
- **Risk Management**: Confidence-based position sizing

## 📞 Support

For issues with the FootyStats API or betting questions, consult:
- FootyStats API Documentation
- Responsible gambling resources
- Professional betting advice

---

**Remember**: This is a tool to assist analysis, not a guarantee of profitable betting. Always gamble responsibly!