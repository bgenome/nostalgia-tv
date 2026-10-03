"""Station choices saved on the device. Tokens are never baked into the image."""

import json
import os
import subprocess
import uuid

from src.station.files import directory_has_video, write_channels_yaml
from src.station.messages import CLOCKS

TIMEZONE_SCRIPT = "/usr/local/sbin/nostalgia-set-timezone"
MOUNT_SCRIPT = "/usr/local/sbin/nostalgia-mount-library"


def data_dir(app_dir):
    return os.path.join(app_dir, "data")


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return default
    if not isinstance(data, dict):
        return default
    return data


def read_station(app_dir):
    return _read_json(os.path.join(data_dir(app_dir), "station.json"), {})


def read_plex(app_dir):
    return _read_json(os.path.join(data_dir(app_dir), "plex_config.json"), {})


def client_id(app_dir):
    path = os.path.join(data_dir(app_dir), "client_id")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as handle:
            existing = handle.read().strip()
        if existing:
            return existing
    value = str(uuid.uuid4())
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(value + "\n")
    return value


def save_files_station(app_dir, channels, timezone):
    write_channels_yaml(os.path.join(data_dir(app_dir), "channels.yaml"), channels)
    payload = {
        "source": "files",
        "timezone": timezone,
        "directories": [channel["directory"] for channel in channels],
    }
    _write_json(os.path.join(data_dir(app_dir), "station.json"), payload)
    return payload


def save_plex_station(app_dir, server_url, token, timezone):
    plex_payload = {
        "server_url": server_url,
        "token": token,
        "use_demo_mode": False,
        "direct_stream": True,
        "last_connected": None,
    }
    _write_json(os.path.join(data_dir(app_dir), "plex_config.json"), plex_payload)
    station_payload = {
        "source": "plex",
        "timezone": timezone,
    }
    _write_json(os.path.join(data_dir(app_dir), "station.json"), station_payload)
    return station_payload


def clean_plex_config():
    return {
        "server_url": "",
        "token": "",
        "use_demo_mode": False,
        "direct_stream": True,
        "last_connected": None,
    }


def station_ready(app_dir):
    station = read_station(app_dir)
    source = station.get("source")
    if source == "plex":
        plex = read_plex(app_dir)
        return bool(plex.get("server_url") and plex.get("token")) and plex.get("use_demo_mode") is False
    if source == "files":
        directories = station.get("directories") or []
        return any(directory_has_video(path) for path in directories)
    return False


def apply_timezone(zone_id):
    allowed = {zone for _label, zone in CLOCKS}
    if zone_id not in allowed:
        return False
    if os.path.exists(TIMEZONE_SCRIPT):
        if os.geteuid() == 0:
            command = [TIMEZONE_SCRIPT, zone_id]
        else:
            command = ["sudo", "-n", TIMEZONE_SCRIPT, zone_id]
        subprocess.run(command, check=False)
        return True
    return False


def mount_library():
    if not os.path.exists(MOUNT_SCRIPT):
        return False
    if os.geteuid() == 0:
        command = [MOUNT_SCRIPT]
    else:
        command = ["sudo", "-n", MOUNT_SCRIPT]
    subprocess.run(command, check=False)
    return True


def _write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
