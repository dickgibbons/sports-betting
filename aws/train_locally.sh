#!/bin/bash
# Alternative: Train models locally (if you have sklearn 1.6.1 installed)
# Use this if you don't want to use EC2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ANALYZERS_DIR="${SCRIPT_DIR}/../nhl/analyzers"

echo "=============================================="
echo "Local Model Training"
echo "=============================================="

# Check sklearn version
SKLEARN_VERSION=$(python3 -c "import sklearn; print(sklearn.__version__)" 2>/dev/null || echo "not installed")
echo "Current sklearn version: $SKLEARN_VERSION"

if [ "$SKLEARN_VERSION" != "1.6.1" ]; then
    echo ""
    echo "WARNING: sklearn version is not 1.6.1"
    echo "Models may not be compatible with your existing system."
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run training
cd "$SCRIPT_DIR"
echo ""
echo "Starting training..."
python3 train_all_models.py

# Copy to analyzers directory
echo ""
echo "Copying models to analyzers directory..."
cp -v trained_models/*.pkl "$ANALYZERS_DIR/"

echo ""
echo "=============================================="
echo "Training complete!"
echo "=============================================="
echo "Models copied to: $ANALYZERS_DIR"
