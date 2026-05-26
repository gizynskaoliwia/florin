#!/bin/bash

cd "$(dirname "$0")"

echo "====================================="
echo "   Starting Florin Budget Tracker    "
echo "====================================="

# Check if Python is installed
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed."
    echo "Please install Python 3.10+ from python.org or via Homebrew."
    read -p "Press Enter to exit..."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Setting up virtual environment for the first time..."
    $PYTHON_CMD -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies quietly
echo "Checking dependencies..."
pip install -r requirements.txt -q

# Launch the app
echo "Launching Florin..."
python main.py
