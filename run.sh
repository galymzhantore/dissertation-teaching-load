#!/bin/bash

# Teaching Load Distribution System - Quick Launcher
# This script activates the virtual environment and launches the Streamlit app

echo "=========================================="
echo "Teaching Load Distribution System"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo "❌ Dependencies not installed!"
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo "🚀 Launching Streamlit application..."
echo "📍 Opening http://localhost:8501 in your browser..."
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

streamlit run frontend/streamlit_app.py
