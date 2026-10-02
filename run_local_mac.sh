#!/bin/bash
set -e

echo "Setting up Nostalgia TV for local macOS testing..."

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Please install it from https://brew.sh/"
    exit 1
fi

echo "Checking if mpv is installed..."
if ! command -v mpv &> /dev/null; then
    echo "Installing mpv via Homebrew..."
    brew install mpv
else
    echo "mpv is already installed."
fi

echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements-mac.txt

echo "Setup complete!"
echo "--------------------------------------------------------"
echo "Starting Nostalgia TV..."
echo "Use the UP and DOWN arrow keys on your keyboard to change channels."
echo "Press ESC to quit."
echo "--------------------------------------------------------"

python main.py
