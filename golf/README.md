# PGA Tour Prediction Model

Predict PGA Tour tournament winners and top-10 finishers using machine learning and DataGolf API data.

## Project Structure

```
PGA_Bets/
├── configs/
│   └── config.py           # API keys and configuration
├── data/
│   ├── raw/                # Raw data from DataGolf API
│   └── processed/          # Cleaned and feature-engineered data
├── models/                 # Trained model artifacts
├── notebooks/              # Jupyter notebooks for EDA and experiments
├── scripts/
│   ├── datagolf_client.py  # DataGolf API wrapper
│   ├── collect_data.py     # Data collection utilities
│   └── test_api.py         # API connection test
├── requirements.txt
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Edit `configs/config.py` and add your DataGolf API key:

```python
DATAGOLF_API_KEY = "your_actual_api_key"
```

Or use environment variable:
```bash
export DATAGOLF_API_KEY="your_actual_api_key"
```

### 3. Test API Connection

```bash
cd PGA_Bets
python scripts/test_api.py YOUR_API_KEY
```

## Data Collection

### Collect Current Data (Rankings, Field, Predictions)

```bash
python scripts/collect_data.py --api-key YOUR_API_KEY --mode current
```

### Collect Historical Data (Rounds, Scores)

```bash
python scripts/collect_data.py --api-key YOUR_API_KEY --mode historical
```

### Collect Everything

```bash
python scripts/collect_data.py --api-key YOUR_API_KEY --mode all
```

## Data Available from DataGolf

### Current/Live Data
- **DG Rankings**: DataGolf's proprietary player rankings
- **Skill Ratings**: Overall skill ratings per player
- **Skill Decompositions**: SG breakdown (OTT, APP, ARG, PUTT)
- **Approach Skill**: Detailed approach by yardage bucket
- **Pre-Tournament Predictions**: Win/Top 5/10/20 probabilities
- **Betting Odds**: Lines from 8+ sportsbooks

### Historical Data
- **Round Scoring**: Score and SG by round for every player
- **Tournament Results**: Finishes, earnings, FedEx points
- **Prediction Archive**: Historical pre-tournament predictions

## Modeling Approach

### Target Variables
1. **Winner** (binary): Did player win? (~0.7% base rate)
2. **Top 10** (binary): Did player finish top 10? (~7% base rate)
3. **Finish Position** (ordinal/regression): Actual finishing position

### Key Features
- Strokes Gained categories (SG:OTT, SG:APP, SG:ARG, SG:PUTT)
- Rolling form (last 12/24/36 rounds)
- Course history at venue
- Course fit (length, accuracy requirements)
- Recent results (cuts made, top 10s)
- World Golf Ranking / DG Ranking

### Recommended Models
- **XGBoost/LightGBM**: Gradient boosting for tabular data
- **Ensemble**: Combine multiple models
- **Ranking model**: LambdaMART for finish position

## Next Steps

1. [ ] Run data collection scripts
2. [ ] Exploratory Data Analysis (see `notebooks/`)
3. [ ] Feature engineering pipeline
4. [ ] Train baseline model
5. [ ] Backtest on 2023-2024 tournaments
6. [ ] Compare to DataGolf baseline

## References

- [DataGolf API Documentation](https://datagolf.com/api-access)
- [DataGolf Python Wrapper](https://github.com/coreyjs/data-golf-api)
- [Strokes Gained Explained](https://www.pgatour.com/stats/stat.02675.html)
