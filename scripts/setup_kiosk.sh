#!/bin/bash
set -e

echo "Installing Nostalgia TV dependencies for Raspberry Pi OS Lite..."
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    cage \
    wayland-protocols \
    libmpv-dev \
    mpv \
    cec-utils \
    python3-pyqt6 \
    python3-pip \
    python3-venv

echo "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Installing systemd service..."
sudo cp scripts/nostalgia-tv.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nostalgia-tv.service

echo "Setup complete! Please ensure your NAS is mounted in /etc/fstab."
echo "You can start the service now with: sudo systemctl start nostalgia-tv"
