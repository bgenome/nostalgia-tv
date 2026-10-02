FROM ubuntu:22.04

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies including mpv and PyQt6 prerequisites
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libmpv-dev \
    mpv \
    python3-pyqt6 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libegl1 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Use the mac requirements since we don't need the CEC library for testing
COPY requirements-mac.txt .
RUN pip3 install --no-cache-dir -r requirements-mac.txt

# Copy the rest of the application
COPY . .

# Set environment variables for Qt to use X11
ENV QT_QPA_PLATFORM=xcb

CMD ["python3", "main.py"]
