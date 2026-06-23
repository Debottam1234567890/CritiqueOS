#!/bin/bash
cd "$(dirname "$0")"

echo "========================================="
echo "🍅 Welcome to CritiqueOS!"
echo "If the standalone executable crashed, this native runner will work 100%."
echo "========================================="

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt -q

echo "Starting CritiqueOS..."
python3 main.py
