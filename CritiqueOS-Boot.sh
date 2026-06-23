#!/bin/bash

echo "🍅 Welcome to CritiqueOS Setup!"
echo "Creating a safe virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
pip install -r requirements.txt -q

echo "Starting CritiqueOS..."
python3 main.py
