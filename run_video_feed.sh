#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  📺 STARTING NOSTALGIA TV VIDEO FEED SERVER"
echo "  >> Zero-install Python 3 server"
echo "  >> Real CRT shaders, Prevue TV Guide & LG Magic Remote"
echo "=========================================================="

# Launch server and open browser
python3 server.py 8080
