#!/bin/bash
# EC2 Setup Script - Run this on a fresh EC2 instance
# Amazon Linux 2023 or Ubuntu 22.04 recommended

set -e

echo "=============================================="
echo "NHL Model Training - EC2 Setup"
echo "=============================================="

# Update system
echo "Updating system packages..."
if command -v apt &> /dev/null; then
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip python3-venv
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv ~/nhl_training_env
source ~/nhl_training_env/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install scikit-learn==1.6.1 pandas==2.2.0 numpy==1.26.4 requests==2.31.0 xgboost==2.0.0 joblib==1.3.2

# Verify installation
echo ""
echo "Verifying installation..."
python3 -c "import sklearn; print(f'sklearn version: {sklearn.__version__}')"
python3 -c "import pandas; print(f'pandas version: {pandas.__version__}')"
python3 -c "import numpy; print(f'numpy version: {numpy.__version__}')"

echo ""
echo "=============================================="
echo "Setup complete!"
echo "To train models, run:"
echo "  source ~/nhl_training_env/bin/activate"
echo "  python3 train_all_models.py"
echo "=============================================="
