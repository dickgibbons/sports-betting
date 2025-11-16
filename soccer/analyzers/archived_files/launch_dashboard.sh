#!/bin/bash

# Launch Soccer Betting Dashboard
# Opens the Streamlit web interface in your browser

echo "🚀 Launching Soccer Betting Dashboard..."
echo ""

# Change to soccer directory
cd "/Users/richardgibbons/soccer betting python/soccer"

echo "📊 Starting Streamlit dashboard..."
echo "🌐 Dashboard will open in your browser automatically"
echo "🔗 URL: http://localhost:8501"
echo ""
echo "💡 Use Ctrl+C to stop the dashboard"
echo ""

# Launch Streamlit dashboard
streamlit run soccer_dashboard.py