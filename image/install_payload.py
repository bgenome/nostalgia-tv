#!/usr/bin/env python3
"""Copy the kiosk onto an image root. YouTube and the dev harness stay out."""

import argparse
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.station.files import write_channels_yaml
from src.station.store import clean_plex_config

APP_FILES = (
    "main.py",
    "src/config/parser.py",
    "src/engine/scheduler.py",
    "src/ui/main_window.py",
    "src/ui/setup_window.py",
    "src/remote/listener.py",
    "src/remote/keys.py",
    "src/plex/__init__.py",
    "src/plex/client.py",
    "src/station/__init__.py",
    "src/station/messages.py",
    "src/station/clock.py",
    "src/station/files.py",
    "src/station/store.py",
    "src/station/plex_link.py",
    "src/station/plex_lineup.py",
    "shaders/crt-easymode.glsl",
)

FORBIDDEN_PATH_PARTS = (
    "youtube",
    "yt-dlp",
    "yt_dlp",
    "server.py",
    "web",
    "platforms",
    "node_modules",
)

FORBIDDEN_TEXT = (
    "YouTubeClient",
    "yt-dlp",
    "yt_dlp",
    "src/youtube",
    "src.youtube",
)


def install_app(repo_root, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(dest)
    for relative in APP_FILES:
        source = os.path.join(repo_root, relative)
        target = os.path.join(dest, relative)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)
    data_dir = os.path.join(dest, "data")
    os.makedirs(data_dir, exist_ok=True)
    write_channels_yaml(os.path.join(data_dir, "channels.yaml"), [])
    with open(os.path.join(data_dir, "plex_config.json"), "w", encoding="utf-8") as handle:
        json.dump(clean_plex_config(), handle, indent=2)
        handle.write("\n")
    assert_install_clean(dest)


def assert_install_clean(dest):
    for root, dirs, files in os.walk(dest):
        for name in dirs + files:
            lowered = name.lower()
            for part in FORBIDDEN_PATH_PARTS:
                if part in lowered:
                    raise SystemExit(f"Image install path contains {name}")
        for name in files:
            path = os.path.join(root, name)
            if not name.endswith((".py", ".json", ".yaml", ".yml", ".glsl", ".service", ".txt", ".sh")):
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
            for needle in FORBIDDEN_TEXT:
                if needle in text:
                    raise SystemExit(f"{path} contains {needle}")

    plex_path = os.path.join(dest, "data", "plex_config.json")
    with open(plex_path, "r", encoding="utf-8") as handle:
        plex = json.load(handle)
    if plex.get("token"):
        raise SystemExit("Plex token must stay empty in the image")
    if plex.get("use_demo_mode") is not False:
        raise SystemExit("Demo mode must be off in the image")
    if not os.path.exists(os.path.join(dest, "main.py")):
        raise SystemExit("main.py missing from the image")
    if not os.path.exists(os.path.join(dest, "src", "plex", "client.py")):
        raise SystemExit("Plex client missing from the image")
    if os.path.exists(os.path.join(dest, "src", "youtube")):
        raise SystemExit("YouTube package is on the image install path")
    if os.path.exists(os.path.join(dest, "server.py")):
        raise SystemExit("Dev harness is on the image install path")


def main():
    parser = argparse.ArgumentParser(description="Install the Nostalgia TV kiosk payload")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()
    install_app(os.path.abspath(args.repo), os.path.abspath(args.dest))


if __name__ == "__main__":
    main()
