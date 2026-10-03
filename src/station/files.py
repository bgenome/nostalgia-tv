"""Turn a USB library into clock aligned channel directories."""

import json
import os

VIDEO_SUFFIXES = (".mp4", ".mkv", ".avi", ".m4v")


def directory_has_video(directory):
    if not directory or not os.path.isdir(directory):
        return False
    for root, dirs, names in os.walk(directory):
        dirs[:] = [name for name in dirs if not name.startswith(".")]
        for name in names:
            if name.lower().endswith(VIDEO_SUFFIXES):
                return True
    return False


def channels_from_root(root):
    if not root or not os.path.isdir(root):
        return []
    folders = []
    loose = False
    for name in sorted(os.listdir(root)):
        if name.startswith("."):
            continue
        path = os.path.join(root, name)
        if os.path.isdir(path) and directory_has_video(path):
            folders.append(path)
        elif os.path.isfile(path) and name.lower().endswith(VIDEO_SUFFIXES):
            loose = True

    channels = []
    number = 2
    for path in folders:
        channels.append({
            "number": number,
            "name": os.path.basename(path) or "Library",
            "type": "tv_shows",
            "directory": path,
        })
        number += 1
    if loose:
        channels.append({
            "number": number,
            "name": "Library",
            "type": "tv_shows",
            "directory": root,
        })
    if channels:
        return channels
    if directory_has_video(root):
        return [{
            "number": 2,
            "name": os.path.basename(root.rstrip(os.sep)) or "Library",
            "type": "tv_shows",
            "directory": root,
        }]
    return []


def candidate_roots():
    roots = []
    preferred = "/media/library"
    if os.path.isdir(preferred):
        roots.append(preferred)
    for base in ("/media", "/run/media", "/mnt"):
        if not os.path.isdir(base):
            continue
        for name in sorted(os.listdir(base)):
            path = os.path.join(base, name)
            if os.path.isdir(path) and path not in roots:
                roots.append(path)
    return roots


def find_library(roots=None):
    if roots is None:
        roots = candidate_roots()
    for root in roots:
        channels = channels_from_root(root)
        if channels:
            return channels
    return []


def write_channels_yaml(path, channels):
    lines = ["channels:"]
    if not channels:
        lines.append("  {}")
    else:
        for channel in channels:
            lines.append(f"  {int(channel['number'])}:")
            lines.append(f"    name: {json.dumps(channel['name'])}")
            lines.append(f"    type: {json.dumps(channel['type'])}")
            lines.append(f"    directory: {json.dumps(channel.get('directory') or '')}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
