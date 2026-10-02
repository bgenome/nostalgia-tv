#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
cd "$DIR"

mkdir -p plex_config media/Cartoons media/Movies media/Bumpers

echo "Removing any existing nostalgia-plex container..."
docker rm -f nostalgia-plex 2>/dev/null || true

echo "Starting Plex Media Server container..."
docker run -d \
  --name nostalgia-plex \
  -p 32400:32400/tcp \
  -p 1900:1900/udp \
  -p 5353:5353/udp \
  -p 8324:8324/tcp \
  -p 32410:32410/udp \
  -p 32412:32412/udp \
  -p 32413:32413/udp \
  -p 32414:32414/udp \
  -p 32469:32469/tcp \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Etc/UTC \
  -e VERSION=docker \
  -v "$DIR/plex_config:/config" \
  -v "$DIR/media:/media" \
  --restart unless-stopped \
  linuxserver/plex:latest

echo "Plex container launched successfully!"
echo "Checking initial container logs..."
sleep 4
docker ps -f name=nostalgia-plex
