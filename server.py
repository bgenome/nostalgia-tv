#!/usr/bin/env python3
"""
Nostalgia TV - Standalone Broadcast Server & Remote Admin Panel API
Includes full Plex Media Server integration, dynamic channel CRUD,
remote control, and hot-reloading broadcast engine.
Zero external pip dependencies required.
"""

import os
import sys
import json
import time
import socket
import shutil
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timedelta

# Import local modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data", "channels.json")
YAML_FILE = os.path.join(BASE_DIR, "data", "channels.yaml")
WEB_DIR = os.path.join(BASE_DIR, "web")
EPOCH = datetime(2020, 1, 1, 0, 0, 0)
START_TIME = time.time()

# Import Local Clients
sys.path.insert(0, BASE_DIR)
from src.plex.client import PlexClient
from src.youtube.client import YouTubeClient

plex_client = PlexClient()
youtube_client = YouTubeClient()

def get_local_ip():
    """Detects primary local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def load_channels_data():
    if not os.path.exists(DATA_FILE):
        return {"global": {}, "channels": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"global": {}, "channels": {}}

def save_channels_data(data):
    """Saves channel configuration to JSON and attempts YAML sync."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Optional YAML sync if pyyaml is present
    try:
        import yaml
        with open(YAML_FILE, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)
    except ImportError:
        pass


class SimulatedBroadcastEngine:
    def __init__(self):
        self.data = load_channels_data()
        self.channels = self.data.get("channels", {})
        self.global_cfg = self.data.get("global", {})
        self.active_channel = 2
        self.tv_powered = True

    def reload(self):
        self.data = load_channels_data()
        self.channels = self.data.get("channels", {})
        self.global_cfg = self.data.get("global", {})

    def get_channel_status(self, ch_num, now=None):
        if now is None:
            now = datetime.now()
        
        ch_key = str(ch_num)
        if ch_key not in self.channels:
            return {
                "channel": ch_num,
                "name": f"Channel {ch_num}",
                "type": "static",
                "is_off_air": True,
                "title": "OFF-AIR / STATIC",
                "seek_seconds": 0,
                "duration": 0,
                "video_url": None
            }
        
        ch = self.channels[ch_key]
        ch_type = ch.get("type", "tv_shows")

        if ch_type == "guide":
            return {
                "channel": ch_num,
                "name": ch.get("name", "TV Guide"),
                "type": "guide",
                "is_off_air": False,
                "title": "PREVUE CHANNEL PROGRAM GUIDE",
                "pip_title": "90s Nostalgia Channel Highlights",
                "pip_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "seek_seconds": int((now - EPOCH).total_seconds()) % 60,
                "duration": 60,
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"
            }

        if ch_type == "tv_shows":
            shows = ch.get("shows", [])
            if not shows:
                return self._empty_status(ch_num, ch)
            total_duration = sum(s.get("duration", 600) for s in shows)
            elapsed = int((now - EPOCH).total_seconds())
            cycle_pos = elapsed % total_duration

            accum = 0
            for show in shows:
                dur = show.get("duration", 600)
                if accum <= cycle_pos < accum + dur:
                    seek = cycle_pos - accum
                    return {
                        "channel": ch_num,
                        "name": ch.get("name"),
                        "type": ch_type,
                        "genre": ch.get("genre", "Animation"),
                        "title": show.get("title"),
                        "seek_seconds": seek,
                        "duration": dur,
                        "video_url": show.get("video_url"),
                        "is_off_air": False,
                        "is_bumper": False
                    }
                accum += dur

        elif ch_type == "movies":
            movies = ch.get("movies", [])
            if not movies:
                return self._empty_status(ch_num, ch)
            total_duration = sum(m.get("duration", 3600) for m in movies)
            elapsed = int((now - EPOCH).total_seconds())
            cycle_pos = elapsed % total_duration

            accum = 0
            for movie in movies:
                dur = movie.get("duration", 3600)
                if accum <= cycle_pos < accum + dur:
                    seek = cycle_pos - accum
                    return {
                        "channel": ch_num,
                        "name": ch.get("name"),
                        "type": ch_type,
                        "genre": ch.get("genre", "Feature Film"),
                        "title": movie.get("title"),
                        "seek_seconds": seek,
                        "duration": dur,
                        "video_url": movie.get("video_url"),
                        "is_off_air": False,
                        "is_bumper": False
                    }
                accum += dur

        elif ch_type == "scheduled":
            schedule = ch.get("schedule", [])
            bumpers = ch.get("bumpers", [])
            current_time = now.time()

            active_slot = None
            for slot in schedule:
                st = datetime.strptime(slot["start"], "%H:%M").time()
                et = datetime.strptime(slot["end"], "%H:%M").time()
                if st <= current_time < et:
                    active_slot = slot
                    break

            if active_slot:
                start_dt = datetime.combine(now.date(), datetime.strptime(active_slot["start"], "%H:%M").time())
                slot_elapsed = int((now - start_dt).total_seconds())
                show_dur = active_slot.get("duration", 1320)

                if slot_elapsed < show_dur:
                    return {
                        "channel": ch_num,
                        "name": ch.get("name"),
                        "type": ch_type,
                        "genre": ch.get("genre", "Scheduled Cartoon"),
                        "title": active_slot.get("title"),
                        "seek_seconds": slot_elapsed,
                        "duration": show_dur,
                        "video_url": active_slot.get("video_url"),
                        "is_off_air": False,
                        "is_bumper": False,
                        "time_slot": f"{active_slot['start']} - {active_slot['end']}"
                    }
                else:
                    bumper_elapsed = slot_elapsed - show_dur
                    bumper = bumpers[0] if bumpers else {
                        "title": "Retro Station ID Bumper",
                        "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                        "duration": 30
                    }
                    b_dur = bumper.get("duration", 30)
                    return {
                        "channel": ch_num,
                        "name": ch.get("name"),
                        "type": ch_type,
                        "genre": "Station Bumper / Commercial Break",
                        "title": f"[Commercial Break] {bumper.get('title')}",
                        "seek_seconds": bumper_elapsed % b_dur,
                        "duration": b_dur,
                        "video_url": bumper.get("video_url"),
                        "is_off_air": False,
                        "is_bumper": True,
                        "time_slot": f"{active_slot['start']} - {active_slot['end']}"
                    }
            else:
                bumper = bumpers[0] if bumpers else {
                    "title": "Nostalgia TV Off-Air Bumper",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                    "duration": 60
                }
                return {
                    "channel": ch_num,
                    "name": ch.get("name"),
                    "type": ch_type,
                    "genre": "Off-Air Bumpers",
                    "title": f"[Station ID] {bumper.get('title')}",
                    "seek_seconds": int((now - EPOCH).total_seconds()) % bumper.get("duration", 60),
                    "duration": bumper.get("duration", 60),
                    "video_url": bumper.get("video_url"),
                    "is_off_air": False,
                    "is_bumper": True
                }

        elif ch_type == "bumpers":
            items = ch.get("items", [])
            if not items:
                return self._empty_status(ch_num, ch)
            total_dur = sum(i.get("duration", 60) for i in items)
            elapsed = int((now - EPOCH).total_seconds()) % total_dur
            accum = 0
            for item in items:
                dur = item.get("duration", 60)
                if accum <= elapsed < accum + dur:
                    return {
                        "channel": ch_num,
                        "name": ch.get("name"),
                        "type": ch_type,
                        "genre": ch.get("genre", "Retro Vault"),
                        "title": item.get("title"),
                        "seek_seconds": elapsed - accum,
                        "duration": dur,
                        "video_url": item.get("video_url"),
                        "is_off_air": False,
                        "is_bumper": True
                    }
                accum += dur

        return self._empty_status(ch_num, ch)

    def _empty_status(self, ch_num, ch):
        return {
            "channel": ch_num,
            "name": ch.get("name", f"Channel {ch_num}"),
            "type": ch.get("type", "unknown"),
            "title": "TECHNICAL DIFFICULTIES",
            "seek_seconds": 0,
            "duration": 0,
            "video_url": None,
            "is_off_air": True
        }

    def get_guide_matrix(self):
        now = datetime.now()
        guide = []
        for ch_key, ch in sorted(self.channels.items(), key=lambda x: int(x[0])):
            ch_num = int(ch_key)
            status_now = self.get_channel_status(ch_num, now)
            status_plus30 = self.get_channel_status(ch_num, now + timedelta(minutes=30))
            status_plus60 = self.get_channel_status(ch_num, now + timedelta(minutes=60))

            guide.append({
                "channel": ch_num,
                "name": ch.get("name"),
                "genre": ch.get("genre", "General"),
                "now_title": status_now.get("title", "Off-Air"),
                "next_title": status_plus30.get("title", "Up Next"),
                "later_title": status_plus60.get("title", "Later")
            })
        return {
            "server_time": now.strftime("%I:%M:%S %p"),
            "grid": guide
        }

ENGINE = SimulatedBroadcastEngine()


class NostalgiaTVHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length).decode('utf-8')
            return json.loads(body)
        return {}

    def _serve_range_file(self, filepath, content_type="video/mp4"):
        """Serves local media files with HTTP 206 Partial Content (Range) support for video seeking."""
        if not os.path.exists(filepath) or not os.path.isfile(filepath):
            self.send_response(404)
            self.end_headers()
            return

        file_size = os.path.getsize(filepath)
        range_header = self.headers.get("Range")

        if not range_header:
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            try:
                with open(filepath, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            except Exception:
                pass
            return

        try:
            byte_range = range_header.strip().split("=")[1]
            parts = byte_range.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if parts[1] else file_size - 1
            if end >= file_size:
                end = file_size - 1
            length = end - start + 1

            self.send_response(206)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(remaining, 64 * 1024))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except Exception:
            pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Route /admin to /admin.html
        if path in ["/admin", "/admin/"]:
            self.path = "/admin.html"
            return super().do_GET()

        # ================= PUBLIC & TV APIS =================
        if path == "/api/channels":
            ENGINE.reload()
            return self._send_json(ENGINE.channels)

        if path == "/api/status":
            ch_num = int(query.get("channel", [ENGINE.active_channel])[0])
            status = ENGINE.get_channel_status(ch_num)
            status["active_channel"] = ENGINE.active_channel
            status["tv_powered"] = ENGINE.tv_powered
            status["server_time"] = datetime.now().strftime("%I:%M:%S %p")
            return self._send_json(status)

        if path == "/api/guide":
            return self._send_json(ENGINE.get_guide_matrix())

        if path == "/api/switch":
            if "channel" in query:
                try:
                    ENGINE.active_channel = int(query["channel"][0])
                except ValueError:
                    pass
            status = ENGINE.get_channel_status(ENGINE.active_channel)
            status["active_channel"] = ENGINE.active_channel
            return self._send_json(status)

        # ================= ADMIN APIS =================
        if path == "/api/admin/system":
            local_ip = get_local_ip()
            uptime_sec = int(time.time() - START_TIME)
            return self._send_json({
                "local_ip": local_ip,
                "port": 8080,
                "remote_admin_url": f"http://{local_ip}:8080/admin",
                "remote_tv_url": f"http://{local_ip}:8080/",
                "uptime_seconds": uptime_sec,
                "total_channels": len(ENGINE.channels),
                "active_channel": ENGINE.active_channel,
                "server_time": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "global_settings": ENGINE.global_cfg
            })

        if path == "/api/admin/channels":
            ENGINE.reload()
            return self._send_json({
                "global": ENGINE.global_cfg,
                "channels": ENGINE.channels
            })

        # ================= PLEX APIS =================
        if path == "/api/plex/config":
            cfg = plex_client.config.copy()
            # Mask token for security
            if cfg.get("token"):
                cfg["token_masked"] = cfg["token"][:3] + "..." + cfg["token"][-3:]
            else:
                cfg["token_masked"] = ""
            return self._send_json(cfg)

        if path == "/api/plex/libraries":
            libs = plex_client.get_libraries()
            return self._send_json(libs)

        if path == "/api/plex/library":
            section_id = query.get("section", ["1"])[0]
            items = plex_client.get_library_items(section_id)
            return self._send_json(items)

        if path == "/api/plex/show":
            rating_key = query.get("ratingKey", ["101"])[0]
            show_data = plex_client.get_show_episodes(rating_key)
            return self._send_json(show_data)

        if path == "/api/plex/search":
            q = query.get("q", [""])[0]
            results = plex_client.search(q)
            return self._send_json(results)

        # ================= YOUTUBE & LOCAL MEDIA APIS =================
        if path == "/api/media/stream":
            rel_file = query.get("file", [""])[0]
            safe_rel = urllib.parse.unquote(rel_file).lstrip("/\\")
            filepath = os.path.abspath(os.path.join(BASE_DIR, "media", safe_rel))
            media_root = os.path.abspath(os.path.join(BASE_DIR, "media"))
            if not filepath.startswith(media_root):
                return self._send_json({"error": "Forbidden path"}, 403)
            return self._serve_range_file(filepath)

        if path == "/api/youtube/status":
            return self._send_json(youtube_client.get_status())

        if path == "/api/youtube/sync/status":
            task_id = query.get("task_id", [None])[0]
            return self._send_json(youtube_client.get_sync_status(task_id))

        # Default static file serving from web/
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # ================= ADMIN CHANNEL CRUD =================
        if path == "/api/admin/channel/save":
            body = self._read_json_body()
            ch_num = str(body.get("channel_num"))
            ch_data = body.get("data")
            if not ch_num or not ch_data:
                return self._send_json({"error": "Missing channel_num or data"}, 400)

            all_data = load_channels_data()
            if "channels" not in all_data:
                all_data["channels"] = {}
            all_data["channels"][ch_num] = ch_data
            save_channels_data(all_data)
            ENGINE.reload()
            return self._send_json({"success": True, "channel": ch_num, "data": ch_data})

        if path == "/api/admin/channel/delete":
            body = self._read_json_body()
            ch_num = str(body.get("channel_num"))
            all_data = load_channels_data()
            if "channels" in all_data and ch_num in all_data["channels"]:
                del all_data["channels"][ch_num]
                save_channels_data(all_data)
                ENGINE.reload()
                return self._send_json({"success": True, "deleted": ch_num})
            return self._send_json({"error": "Channel not found"}, 404)

        if path == "/api/admin/global":
            body = self._read_json_body()
            all_data = load_channels_data()
            all_data["global"] = body
            save_channels_data(all_data)
            ENGINE.reload()
            return self._send_json({"success": True, "global": all_data["global"]})

        # ================= REMOTE TV CONTROL =================
        if path == "/api/admin/remote/tune":
            body = self._read_json_body()
            ch_num = int(body.get("channel", ENGINE.active_channel))
            ENGINE.active_channel = ch_num
            status = ENGINE.get_channel_status(ch_num)
            status["active_channel"] = ch_num
            return self._send_json({"success": True, "status": status})

        if path == "/api/admin/remote/power":
            body = self._read_json_body()
            if "state" in body:
                ENGINE.tv_powered = bool(body["state"])
            else:
                ENGINE.tv_powered = not ENGINE.tv_powered
            return self._send_json({"success": True, "tv_powered": ENGINE.tv_powered})

        # ================= PLEX CONFIG & IMPORT =================
        if path == "/api/plex/config":
            body = self._read_json_body()
            saved = plex_client.save_config(body)
            return self._send_json({"success": True, "config": saved})

        if path == "/api/plex/test":
            body = self._read_json_body()
            url = body.get("server_url")
            token = body.get("token")
            result = plex_client.test_connection(url=url, token=token)
            return self._send_json(result)

        if path == "/api/plex/import":
            """Imports a Plex show or movie directly into a channel or creates a new channel."""
            body = self._read_json_body()
            target_ch = str(body.get("channel_num", "2"))
            import_type = body.get("import_type", "show")  # show, movie, slot
            item = body.get("item", {})

            all_data = load_channels_data()
            if "channels" not in all_data:
                all_data["channels"] = {}

            if target_ch not in all_data["channels"]:
                all_data["channels"][target_ch] = {
                    "name": item.get("title", f"Channel {target_ch}"),
                    "type": "tv_shows" if import_type == "show" else "movies",
                    "genre": "Plex Library",
                    "description": item.get("summary", ""),
                    "shows": [],
                    "movies": [],
                    "schedule": []
                }

            channel = all_data["channels"][target_ch]

            if import_type == "show":
                # Fetch full episode list from Plex
                rating_key = item.get("ratingKey")
                episodes_data = plex_client.get_show_episodes(rating_key)
                episodes = episodes_data.get("episodes", [])

                if "shows" not in channel:
                    channel["shows"] = []

                for ep in episodes:
                    channel["shows"].append({
                        "title": f"{item.get('title')} - {ep.get('title')}",
                        "duration": ep.get("duration", 1320),
                        "video_url": ep.get("video_url", ""),
                        "part_file": ep.get("part_file", ""),
                        "tag": f"Season {ep.get('season', 1)}"
                    })
                channel["type"] = "tv_shows"

            elif import_type == "movie":
                if "movies" not in channel:
                    channel["movies"] = []
                channel["movies"].append({
                    "title": item.get("title"),
                    "duration": item.get("duration", 5400),
                    "video_url": item.get("video_url", ""),
                    "part_file": item.get("part_file", "")
                })
                channel["type"] = "movies"

            elif import_type == "slot":
                if "schedule" not in channel:
                    channel["schedule"] = []
                channel["schedule"].append({
                    "start": body.get("start", "16:00"),
                    "end": body.get("end", "16:30"),
                    "title": item.get("title"),
                    "video_url": item.get("video_url", ""),
                    "duration": item.get("duration", 1320)
                })
                channel["type"] = "scheduled"

            save_channels_data(all_data)
            ENGINE.reload()
            return self._send_json({
                "success": True,
                "message": f"Successfully imported '{item.get('title')}' into Channel {target_ch}!",
                "channel": channel
            })

        # ================= YOUTUBE CONFIG & IMPORT =================
        if path == "/api/youtube/config":
            body = self._read_json_body()
            saved = youtube_client.save_config(body)
            return self._send_json({"success": True, "config": saved})

        if path == "/api/youtube/cookies":
            body = self._read_json_body()
            content = body.get("cookies_content", "")
            res = youtube_client.save_cookies_file(content)
            return self._send_json(res)

        if path == "/api/youtube/inspect":
            body = self._read_json_body()
            url = body.get("url", "")
            res = youtube_client.inspect_url(url)
            return self._send_json(res)

        if path == "/api/youtube/import":
            body = self._read_json_body()
            ch_num = int(body.get("channel_num", 6))
            ch_name = body.get("name", "YouTube Channel")
            url = body.get("url", "")
            max_vids = int(body.get("max_videos", 20))
            order = body.get("order", "sequential")
            res = youtube_client.start_background_sync(ch_num, ch_name, url, max_videos=max_vids, order=order)
            return self._send_json(res)

        if path == "/api/youtube/sync/trigger":
            body = self._read_json_body()
            ch_num = int(body.get("channel_num", 6))
            ch_data = ENGINE.channels.get(str(ch_num), {})
            url = ch_data.get("youtube_url", "")
            ch_name = ch_data.get("name", f"Channel {ch_num}")
            res = youtube_client.start_background_sync(ch_num, ch_name, url, max_videos=20)
            return self._send_json(res)

        self.send_response(404)
        self.end_headers()


def run_server(port=8080, open_browser=False):
    os.makedirs(WEB_DIR, exist_ok=True)
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, NostalgiaTVHandler)
    local_ip = get_local_ip()
    
    print("\n" + "=" * 64)
    print("  📺 NOSTALGIA TV BROADCAST SERVER & REMOTE ADMIN PANEL")
    print(f"  >> TV View (Local):         http://localhost:{port}/")
    print(f"  >> Admin Panel (Local):     http://localhost:{port}/admin")
    print(f"  >> Remote Network Admin:    http://{local_ip}:{port}/admin")
    print("  >> Plex Media Server Integration: Active")
    print("  >> YouTube Premium Integration:   Active")
    print("=" * 64 + "\n")
    sys.stdout.flush()

    if open_browser:
        try:
            import subprocess
            if sys.platform == "darwin":
                subprocess.Popen(["open", f"http://localhost:{port}/admin"])
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", f"http://localhost:{port}/admin"])
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Nostalgia TV Server...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port=port, open_browser=False)
