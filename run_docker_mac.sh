#!/bin/bash
set -e

echo "Building Nostalgia TV Docker image..."
docker build -t nostalgia-tv-mac .

echo "--------------------------------------------------------"
echo "IMPORTANT: Running a GUI app in Docker on macOS requires XQuartz."
echo "1. Download and install XQuartz from https://www.xquartz.org/"
echo "2. Open XQuartz, go to Preferences -> Security"
echo "3. Check 'Allow connections from network clients'"
echo "4. Restart XQuartz (Quit and reopen)"
echo "--------------------------------------------------------"
echo "Allowing local connections to X server..."

# Attempt to run xhost (will fail if XQuartz isn't running, but we continue)
xhost + 127.0.0.1 2>/dev/null || echo "Warning: xhost command failed. Make sure XQuartz is running."

echo "Starting container..."
# Run the container, passing the X11 display socket via host.docker.internal
docker run -it --rm \
    -e DISPLAY=host.docker.internal:0 \
    -v "$(pwd)/data:/app/data" \
    nostalgia-tv-mac
