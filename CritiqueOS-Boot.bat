@echo off
title CritiqueOS Bootloader
echo =========================================
echo 🍅 Welcome to CritiqueOS!
echo =========================================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

echo Starting CritiqueOS...
python main.py
pause
