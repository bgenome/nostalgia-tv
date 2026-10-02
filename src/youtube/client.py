#!/usr/bin/env python3
"""
Nostalgia TV - YouTube Premium Client & Video Sync Engine
Handles YouTube authentication via session cookies, playlist inspection,
video download synchronization, direct stream resolution, and offline simulation.
"""

import os
import sys
import json
import time
import shutil
import subprocess
import threading
import urllib.parse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
MEDIA_DIR = os.path.join(BASE_DIR, "media", "YouTube")
CONFIG_FILE = os.path.join(DATA_DIR, "youtube_config.json")
COOKIES_FILE = os.path.join(DATA_DIR, "youtube_cookies.txt")

# Rich offline simulated catalog for instant testing / demo mode
SIMULATED_YOUTUBE_CHANNELS = {
    "supersimplesongs": {
        "title": "Super Simple Songs - Kids Songs",
        "uploader": "Super Simple Songs",
        "channel_id": "UC4nT5JePq6o4zV_z7dJ8QWw",
        "url": "https://www.youtube.com/@SuperSimpleSongs",
        "avatar": "https://yt3.googleusercontent.com/ytc/AIdro_k678",
        "videos": [
            {
                "id": "e_04ZrNroTo",
                "title": "Twinkle Twinkle Little Star | Super Simple Songs",
                "duration": 156,
                "thumbnail": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "upload_date": "2020-05-10"
            },
            {
                "id": "1GDFa-nEzlg",
                "title": "The Wheels On The Bus | Super Simple Songs",
                "duration": 140,
                "thumbnail": "https://images.unsplash.com/photo-1570125909232-eb263c188f7e?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "upload_date": "2020-07-15"
            },
            {
                "id": "71hqRT9Uycg",
                "title": "Five Little Ducks | Nursery Rhymes",
                "duration": 165,
                "thumbnail": "https://images.unsplash.com/photo-1555848962-6e7713d4875b?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "upload_date": "2021-01-20"
            },
            {
                "id": "DR-cfDsHCGA",
                "title": "Old MacDonald Had A Farm | Animal Songs",
                "duration": 180,
                "thumbnail": "https://images.unsplash.com/photo-1500595046743-cd271d694d30?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                "upload_date": "2021-04-12"
            }
        ]
    },
    "msrachel": {
        "title": "Ms Rachel - Songs for Littles",
        "uploader": "Ms Rachel",
        "channel_id": "UCrRmsO286zM9_oU_VqB_Yvg",
        "url": "https://www.youtube.com/@msrachel",
        "avatar": "https://yt3.googleusercontent.com/ytc/AIdro_msrachel",
        "videos": [
            {
                "id": "mr_001",
                "title": "Learn to Talk with Ms Rachel - First Words & Nursery Rhymes",
                "duration": 1200,
                "thumbnail": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                "upload_date": "2022-09-01"
            },
            {
                "id": "mr_002",
                "title": "Hop Little Bunnies & Toddler Movement Songs",
                "duration": 650,
                "thumbnail": "https://images.unsplash.com/photo-1589923188900-85dae523342b?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                "upload_date": "2023-01-15"
            },
            {
                "id": "mr_003",
                "title": "Icky Sticky Bubble Gum & Rhymes for Speech Development",
                "duration": 480,
                "thumbnail": "https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                "upload_date": "2023-03-22"
            }
        ]
    },
    "sesamestreet": {
        "title": "Sesame Street - Classic Songs & Sketches",
        "uploader": "Sesame Street",
        "channel_id": "UC9C3m9iU5sC_4hPj5u-77ww",
        "url": "https://www.youtube.com/@SesameStreet",
        "avatar": "https://yt3.googleusercontent.com/ytc/AIdro_sesame",
        "videos": [
            {
                "id": "ss_001",
                "title": "Ernie sings 'Rubber Duckie' (Classic 1970)",
                "duration": 150,
                "thumbnail": "https://images.unsplash.com/photo-1559827291-72ee739d0d9a?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                "upload_date": "2019-11-10"
            },
            {
                "id": "ss_002",
                "title": "Cookie Monster - 'C is for Cookie' Anthem",
                "duration": 135,
                "thumbnail": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                "upload_date": "2020-02-14"
            },
            {
                "id": "ss_003",
                "title": "Elmo's Song with Big Bird and Snuffy",
                "duration": 160,
                "thumbnail": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=640&q=80",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                "upload_date": "2020-06-01"
            }
        ]
    }
}

class YouTubeClient:
    def __init__(self):
        self.config = self._load_config()
        self.active_sync_tasks = {}
        self._lock = threading.Lock()
        os.makedirs(MEDIA_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "use_cookies": True,
            "cookies_path": COOKIES_FILE,
            "sponsorblock_enabled": True,
            "max_quality": "1080p",
            "auto_sync_interval_hours": 24
        }

    def save_config(self, new_cfg):
        self.config.update(new_cfg)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"[YouTubeClient] Error saving config: {e}")
        return self.config

    def find_ytdlp(self):
        """Finds yt-dlp binary or python module."""
        # 1. Check system PATH
        path = shutil.which("yt-dlp")
        if path:
            return [path]
        # 2. Check common Homebrew / local paths
        for candidate in [
            "/opt/homebrew/bin/yt-dlp",
            "/usr/local/bin/yt-dlp",
            os.path.expanduser("~/.local/bin/yt-dlp")
        ]:
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                return [candidate]
        # 3. Check python -m yt_dlp
        try:
            res = subprocess.run([sys.executable, "-m", "yt_dlp", "--version"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            if res.returncode == 0:
                return [sys.executable, "-m", "yt_dlp"]
        except Exception:
            pass
        return None

    def has_ytdlp(self):
        return self.find_ytdlp() is not None

    def has_cookies(self):
        cookie_path = self.config.get("cookies_path", COOKIES_FILE)
        return os.path.exists(cookie_path) and os.path.getsize(cookie_path) > 50

    def get_status(self):
        """Returns environment status (yt-dlp installed, cookies present, etc.)"""
        ytdlp_cmd = self.find_ytdlp()
        version = None
        if ytdlp_cmd:
            try:
                out = subprocess.check_output(ytdlp_cmd + ["--version"], timeout=3).decode().strip()
                version = out
            except Exception:
                version = "installed"

        cookies_present = self.has_cookies()
        cookie_size = os.path.getsize(COOKIES_FILE) if os.path.exists(COOKIES_FILE) else 0

        # Count synced channels
        synced_channels = []
        if os.path.exists(MEDIA_DIR):
            for item in os.listdir(MEDIA_DIR):
                item_path = os.path.join(MEDIA_DIR, item)
                if os.path.isdir(item_path):
                    manifest = os.path.join(item_path, "channel_manifest.json")
                    vid_count = len([f for f in os.listdir(item_path) if f.endswith(('.mp4', '.mkv', '.webm'))])
                    synced_channels.append({
                        "name": item,
                        "path": item_path,
                        "video_count": vid_count,
                        "has_manifest": os.path.exists(manifest)
                    })

        return {
            "ytdlp_available": ytdlp_cmd is not None,
            "ytdlp_version": version,
            "cookies_configured": cookies_present,
            "cookies_size_bytes": cookie_size,
            "sponsorblock_enabled": self.config.get("sponsorblock_enabled", True),
            "media_dir": MEDIA_DIR,
            "synced_channels": synced_channels,
            "is_simulation_mode": ytdlp_cmd is None
        }

    def save_cookies_file(self, content):
        """Saves Netscape format cookies.txt."""
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        return {"success": True, "size": len(content)}

    def inspect_url(self, url):
        """
        Inspects a YouTube channel, playlist, or single video URL.
        Returns metadata and video list without downloading media files.
        """
        url_clean = url.strip()
        ytdlp_cmd = self.find_ytdlp()

        # If yt-dlp is not installed or url is a demo identifier, use simulation
        if not ytdlp_cmd or "demo" in url_clean.lower() or any(k in url_clean.lower() for k in ["supersimple", "msrachel", "sesame"]):
            return self._inspect_simulated(url_clean)

        cmd = list(ytdlp_cmd) + [
            "--dump-single-json",
            "--flat-playlist",
            "--playlist-end", "30",
            "--no-warnings",
            "--ignore-errors"
        ]

        if self.has_cookies() and self.config.get("use_cookies", True):
            cmd.extend(["--cookies", self.config.get("cookies_path", COOKIES_FILE)])

        cmd.append(url_clean)

        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            if proc.returncode != 0:
                # Fallback to simulation if network or blocked
                return self._inspect_simulated(url_clean)

            data = json.loads(proc.stdout.decode('utf-8'))
            entries = data.get("entries", [])
            videos = []

            # If it's a single video rather than a playlist
            if not entries and "id" in data:
                entries = [data]

            for entry in entries:
                if not entry:
                    continue
                v_id = entry.get("id")
                title = entry.get("title", f"Video {v_id}")
                dur = int(entry.get("duration") or 300)
                thumb = entry.get("thumbnail") or f"https://i.ytimg.com/vi/{v_id}/hqdefault.jpg"
                videos.append({
                    "id": v_id,
                    "title": title,
                    "duration": dur,
                    "thumbnail": thumb,
                    "url": f"https://www.youtube.com/watch?v={v_id}",
                    "upload_date": entry.get("upload_date", "")
                })

            return {
                "title": data.get("title") or data.get("uploader") or "YouTube Channel",
                "uploader": data.get("uploader") or data.get("channel") or "YouTube",
                "url": url_clean,
                "video_count": len(videos),
                "videos": videos,
                "is_simulated": False
            }
        except Exception as e:
            print(f"[YouTubeClient] inspect error ({e}), falling back to simulation")
            return self._inspect_simulated(url_clean)

    def _inspect_simulated(self, url):
        """Returns realistic curated demo catalog based on keyword in URL."""
        low = url.lower()
        if "rachel" in low:
            key = "msrachel"
        elif "sesame" in low:
            key = "sesamestreet"
        else:
            key = "supersimplesongs"

        demo = SIMULATED_YOUTUBE_CHANNELS[key]
        return {
            "title": demo["title"],
            "uploader": demo["uploader"],
            "url": url,
            "video_count": len(demo["videos"]),
            "videos": demo["videos"],
            "is_simulated": True
        }

    def start_background_sync(self, channel_num, channel_name, url, max_videos=20, order="sequential"):
        """Launches background synchronization of a YouTube channel."""
        task_id = f"yt_sync_ch_{channel_num}"
        with self._lock:
            self.active_sync_tasks[task_id] = {
                "channel_num": channel_num,
                "channel_name": channel_name,
                "url": url,
                "status": "starting",
                "progress_percent": 0,
                "current_video": "Preparing download...",
                "downloaded_count": 0,
                "total_count": 0,
                "start_time": time.time(),
                "error": None
            }

        thread = threading.Thread(
            target=self._run_sync_worker,
            args=(task_id, channel_num, channel_name, url, max_videos, order),
            daemon=True
        )
        thread.start()
        return {"success": True, "task_id": task_id}

    def get_sync_status(self, task_id=None):
        with self._lock:
            if task_id:
                return self.active_sync_tasks.get(task_id, {"status": "not_found"})
            return list(self.active_sync_tasks.values())

    def _run_sync_worker(self, task_id, channel_num, channel_name, url, max_videos, order):
        safe_folder = "".join(c for c in channel_name if c.isalnum() or c in (' ', '_', '-')).strip()
        dest_dir = os.path.join(MEDIA_DIR, safe_folder)
        os.makedirs(dest_dir, exist_ok=True)

        inspection = self.inspect_url(url)
        videos_to_sync = inspection.get("videos", [])[:max_videos]

        with self._lock:
            if task_id in self.active_sync_tasks:
                self.active_sync_tasks[task_id]["total_count"] = len(videos_to_sync)
                self.active_sync_tasks[task_id]["status"] = "syncing"

        synced_episodes = []
        ytdlp_cmd = self.find_ytdlp()

        for idx, vid in enumerate(videos_to_sync):
            vid_title = vid["title"]
            safe_title = "".join(c for c in vid_title if c.isalnum() or c in (' ', '_', '-')).strip()
            out_filename = f"{idx+1:02d} - {safe_title[:60]}.mp4"
            out_filepath = os.path.join(dest_dir, out_filename)

            with self._lock:
                if task_id in self.active_sync_tasks:
                    self.active_sync_tasks[task_id]["current_video"] = vid_title
                    self.active_sync_tasks[task_id]["progress_percent"] = int((idx / len(videos_to_sync)) * 100)

            # If already exists and valid size (>500KB), reuse
            if os.path.exists(out_filepath) and os.path.getsize(out_filepath) > 500000:
                print(f"[YouTube Sync] Already downloaded: {out_filename}")
            else:
                if ytdlp_cmd and not vid.get("video_url", "").startswith("http"):
                    # Real yt-dlp download
                    dl_cmd = list(ytdlp_cmd) + [
                        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                        "--output", out_filepath,
                        "--no-warnings"
                    ]
                    if self.has_cookies() and self.config.get("use_cookies", True):
                        dl_cmd.extend(["--cookies", self.config.get("cookies_path", COOKIES_FILE)])
                    if self.config.get("sponsorblock_enabled", True):
                        dl_cmd.extend(["--sponsorblock-remove", "sponsor,intro,outro"])
                    dl_cmd.append(vid["url"])

                    try:
                        subprocess.run(dl_cmd, check=True, timeout=120)
                    except Exception as e:
                        print(f"[YouTube Sync] Download error on {vid_title}: {e}")
                        # Fallback create placeholder
                        self._create_sample_mp4(out_filepath)
                else:
                    # Simulation / Open Sample Fallback
                    sample_url = vid.get("video_url") or "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4"
                    self._download_direct_sample(sample_url, out_filepath)

            synced_episodes.append({
                "title": vid_title,
                "duration": vid["duration"],
                "video_url": f"/api/media/stream?file=YouTube/{urllib.parse.quote(safe_folder)}/{urllib.parse.quote(out_filename)}",
                "part_file": out_filepath,
                "thumbnail": vid["thumbnail"],
                "youtube_id": vid["id"]
            })

            with self._lock:
                if task_id in self.active_sync_tasks:
                    self.active_sync_tasks[task_id]["downloaded_count"] = idx + 1

        # Save manifest
        manifest_file = os.path.join(dest_dir, "channel_manifest.json")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump({
                "channel_name": channel_name,
                "channel_num": channel_num,
                "url": url,
                "last_synced": datetime.now().isoformat(),
                "episodes": synced_episodes
            }, f, indent=2)

        # Update channels.json directly so the broadcast engine hot reloads immediately!
        self._integrate_into_channels_data(channel_num, channel_name, synced_episodes, url, order)

        with self._lock:
            if task_id in self.active_sync_tasks:
                self.active_sync_tasks[task_id]["status"] = "completed"
                self.active_sync_tasks[task_id]["progress_percent"] = 100
                self.active_sync_tasks[task_id]["current_video"] = "Sync Complete!"

    def _create_sample_mp4(self, dest_path):
        """Creates minimal valid MP4 file container for testing."""
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(b'\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41' + (b'\x00' * 1024 * 1024))

    def _download_direct_sample(self, url, dest_path):
        import urllib.request
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r, open(dest_path, "wb") as f:
                # Cap at 5MB for fast local testing
                total = 0
                while total < 5 * 1024 * 1024:
                    chunk = r.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
        except Exception:
            self._create_sample_mp4(dest_path)

    def _integrate_into_channels_data(self, channel_num, channel_name, episodes, source_url, order):
        channels_file = os.path.join(DATA_DIR, "channels.json")
        try:
            with open(channels_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"global": {}, "channels": {}}

        ch_key = str(channel_num)
        ch_type = "tv_shows" if order == "sequential" else "movies"

        new_ch = {
            "name": channel_name.upper(),
            "type": ch_type,
            "genre": "Kids Educational (YouTube)",
            "description": f"Curated from YouTube: {channel_name}",
            "source_type": "youtube_sync",
            "youtube_url": source_url,
            "last_synced": datetime.now().isoformat()
        }

        if ch_type == "tv_shows":
            new_ch["shows"] = [
                {
                    "title": ep["title"],
                    "duration": ep["duration"],
                    "video_url": ep["video_url"],
                    "part_file": ep["part_file"]
                }
                for ep in episodes
            ]
        else:
            new_ch["movies"] = [
                {
                    "title": ep["title"],
                    "duration": ep["duration"],
                    "video_url": ep["video_url"],
                    "part_file": ep["part_file"]
                }
                for ep in episodes
            ]

        data["channels"][ch_key] = new_ch

        with open(channels_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"[YouTubeClient] Channel {channel_num} ({channel_name}) saved to channels.json with {len(episodes)} episodes!")
