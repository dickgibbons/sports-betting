#!/bin/bash
#
# AWS Enhanced Soccer Model Training Script
# Trains soccer models with additional markets on AWS EC2
#
# Usage: ./aws_train_enhanced_soccer.sh
#

set -e  # Exit on error

echo "=================================="
echo "⚽ AWS ENHANCED SOCCER MODEL TRAINER"
echo "=================================="
echo ""

# Configuration
PROJECT_DIR="$HOME/soccer-betting-python/soccer/daily soccer"
MODELS_DIR="$PROJECT_DIR/models"
BACKUP_DIR="$PROJECT_DIR/model_backups"
LOG_FILE="$PROJECT_DIR/training_enhanced_$(date +%Y%m%d_%H%M%S).log"
S3_BUCKET="s3://your-bucket-name/soccer-models"  # Update with your S3 bucket

# Create directories
mkdir -p "$MODELS_DIR"
mkdir -p "$BACKUP_DIR"

echo "📁 Project directory: $PROJECT_DIR"
echo "💾 Models directory: $MODELS_DIR"
echo "📦 Backup directory: $BACKUP_DIR"
echo "📋 Log file: $LOG_FILE"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "🚀 Starting enhanced soccer model training..."

# Backup existing models
if [ -f "$MODELS_DIR/soccer_ml_models_enhanced.pkl" ]; then
    BACKUP_FILE="$BACKUP_DIR/soccer_ml_models_enhanced_backup_$(date +%Y%m%d_%H%M%S).pkl"
    log "📦 Backing up existing enhanced models to $BACKUP_FILE"
    cp "$MODELS_DIR/soccer_ml_models_enhanced.pkl" "$BACKUP_FILE"
fi

# Navigate to project directory
cd "$PROJECT_DIR" || exit 1

# Check Python environment
log "🐍 Checking Python environment..."
python3 --version | tee -a "$LOG_FILE"

# Check required packages
log "📦 Checking required packages..."
python3 -c "import sklearn, numpy, pandas, joblib, requests" 2>&1 | tee -a "$LOG_FILE"

if [ $? -ne 0 ]; then
    log "❌ Missing required packages. Installing..."
    pip3 install scikit-learn numpy pandas joblib requests --user | tee -a "$LOG_FILE"
fi

# Train enhanced models
log "🤖 Training enhanced soccer models..."
log "   This will train models for:"
log "   - Match outcomes (Home/Draw/Away)"
log "   - Game totals (O/U 2.5)"
log "   - Both teams to score (BTTS)"
log "   - Team totals (Home O/U 1.5, Away O/U 0.5)"
log "   - Half markets (1H O/U 0.5, 1.5 | 2H O/U 0.5, 1.5)"
log "   - Double chance (Home/Draw, Away/Draw, Home/Away)"
log ""

# Run training script
python3 soccer_trainer_enhanced.py 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "✅ Training completed successfully!"
else
    log "❌ Training failed! Check log file: $LOG_FILE"
    exit 1
fi

# Verify models were created
if [ -f "$MODELS_DIR/soccer_ml_models_enhanced.pkl" ]; then
    MODEL_SIZE=$(du -h "$MODELS_DIR/soccer_ml_models_enhanced.pkl" | cut -f1)
    log "✅ Enhanced models file created: $MODEL_SIZE"
else
    log "❌ Models file not found!"
    exit 1
fi

# Sync to S3 (optional - uncomment and update bucket name)
# log "☁️  Syncing models to S3..."
# aws s3 cp "$MODELS_DIR/soccer_ml_models_enhanced.pkl" "$S3_BUCKET/soccer_ml_models_enhanced_$(date +%Y%m%d).pkl"
# if [ $? -eq 0 ]; then
#     log "✅ Models synced to S3"
# else
#     log "⚠️  S3 sync failed (continuing anyway)"
# fi

# Summary
log ""
log "=================================="
log "📊 TRAINING SUMMARY"
log "=================================="
log "✅ Enhanced models trained and saved"
log "📁 Model file: $MODELS_DIR/soccer_ml_models_enhanced.pkl"
log "📋 Log file: $LOG_FILE"
log "📦 Backups: $BACKUP_DIR"
log ""

# Test model loading
log "🧪 Testing model loading..."
python3 -c "
import joblib
import sys

try:
    model_data = joblib.load('$MODELS_DIR/soccer_ml_models_enhanced.pkl')
    print('✅ Models loaded successfully')
    print(f'📊 Total models: {len(model_data[\"models\"])}')
    print(f'📋 Markets: {model_data.get(\"markets\", [])}')
    print(f'📅 Trained: {model_data.get(\"trained_date\", \"Unknown\")}')
    sys.exit(0)
except Exception as e:
    print(f'❌ Error loading models: {e}')
    sys.exit(1)
" 2>&1 | tee -a "$LOG_FILE"

if [ $? -eq 0 ]; then
    log "✅ Model verification passed!"
else
    log "❌ Model verification failed!"
    exit 1
fi

log ""
log "✅ Enhanced soccer model training complete!"
log "🎯 You can now use these models for betting predictions"
echo ""
echo "=================================="
echo "✅ TRAINING COMPLETE!"
echo "=================================="
