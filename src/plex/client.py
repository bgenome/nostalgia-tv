"""
Plex Media Server Client for Nostalgia TV
Connects to Plex Media Server via REST API, browses TV and movie libraries,
retrieves episode schedules and direct stream URLs.
Includes a rich simulated demo mode for offline testing.
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_FILE = os.path.join(BASE_DIR, "data", "plex_config.json")

# Built-in Realistic Simulated Plex Data for testing / offline demo
DEMO_PLEX_DATA = {
    "server_info": {
        "name": "Home NAS Plex (Simulated)",
        "version": "1.32.5.7348",
        "platform": "Linux (Synology DSM)",
        "machineIdentifier": "demo-plex-nostalgia-01",
        "myPlex": True,
        "is_demo": True
    },
    "libraries": [
        {
            "id": "1",
            "key": "1",
            "title": "90s Cartoons & Animation",
            "type": "show",
            "count": 5,
            "thumb": "/library/sections/1/thumb"
        },
        {
            "id": "2",
            "key": "2",
            "title": "Retro Family Movies",
            "type": "movie",
            "count": 4,
            "thumb": "/library/sections/2/thumb"
        },
        {
            "id": "3",
            "key": "3",
            "title": "Vintage Commercials & Bumpers",
            "type": "movie",
            "count": 3,
            "thumb": "/library/sections/3/thumb"
        }
    ],
    "shows": {
        "101": {
            "ratingKey": "101",
            "title": "Arthur",
            "year": 1996,
            "summary": "Based on the books by Marc Brown, Arthur follows the adventures of an 8-year-old aardvark, his family, and his friends in Elwood City.",
            "genres": ["Animation", "Children", "Family"],
            "leafCount": 4,
            "thumb": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=300&q=80",
            "episodes": [
                {
                    "ratingKey": "10101",
                    "title": "Arthur's Eyes",
                    "season": 1,
                    "episode": 1,
                    "duration": 660,
                    "summary": "Arthur is embarrassed to discover that he needs glasses.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "part_file": "/volume1/media/Cartoons/Arthur/Season 01/Arthur.S01E01.mp4"
                },
                {
                    "ratingKey": "10102",
                    "title": "Francine's Bad Hair Day",
                    "season": 1,
                    "episode": 2,
                    "duration": 660,
                    "summary": "Francine gets a makeover for school picture day.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "part_file": "/volume1/media/Cartoons/Arthur/Season 01/Arthur.S01E02.mp4"
                },
                {
                    "ratingKey": "10103",
                    "title": "Arthur and the Real Mr. Ratburn",
                    "season": 1,
                    "episode": 3,
                    "duration": 660,
                    "summary": "Arthur and Buster are terrified of getting the strict Mr. Ratburn as their third-grade teacher.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                    "part_file": "/volume1/media/Cartoons/Arthur/Season 01/Arthur.S01E03.mp4"
                },
                {
                    "ratingKey": "10104",
                    "title": "Arthur's Spelling Trubble",
                    "season": 1,
                    "episode": 4,
                    "duration": 660,
                    "summary": "Arthur studies hard for the school spelling bee.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                    "part_file": "/volume1/media/Cartoons/Arthur/Season 01/Arthur.S01E04.mp4"
                }
            ]
        },
        "102": {
            "ratingKey": "102",
            "title": "The Magic School Bus",
            "year": 1994,
            "summary": "Eccentric teacher Ms. Frizzle takes her class on educational, fantastical field trips inside a transforming yellow school bus.",
            "genres": ["Animation", "Adventure", "Family"],
            "leafCount": 3,
            "thumb": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=300&q=80",
            "episodes": [
                {
                    "ratingKey": "10201",
                    "title": "Gets Lost in Space",
                    "season": 1,
                    "episode": 1,
                    "duration": 720,
                    "summary": "Arnold's cousin Janet joins the class on a planetary field trip.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
                    "part_file": "/volume1/media/Cartoons/MagicSchoolBus/Season 01/MagicSchoolBus.S01E01.mp4"
                },
                {
                    "ratingKey": "10202",
                    "title": "For Lunch",
                    "season": 1,
                    "episode": 2,
                    "duration": 720,
                    "summary": "The class travels inside Arnold's digestive system to see how digestion works.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
                    "part_file": "/volume1/media/Cartoons/MagicSchoolBus/Season 01/MagicSchoolBus.S01E02.mp4"
                },
                {
                    "ratingKey": "10203",
                    "title": "Inside Ralphie",
                    "season": 1,
                    "episode": 3,
                    "duration": 720,
                    "summary": "The kids journey inside Ralphie to see white blood cells fight off a virus.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "part_file": "/volume1/media/Cartoons/MagicSchoolBus/Season 01/MagicSchoolBus.S01E03.mp4"
                }
            ]
        },
        "103": {
            "ratingKey": "103",
            "title": "Rugrats",
            "year": 1991,
            "summary": "A group of toddlers explore the world from an imaginative, pint-sized perspective.",
            "genres": ["Animation", "Comedy"],
            "leafCount": 2,
            "thumb": "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=300&q=80",
            "episodes": [
                {
                    "ratingKey": "10301",
                    "title": "Tommy's First Birthday",
                    "season": 1,
                    "episode": 1,
                    "duration": 680,
                    "summary": "Tommy decides he wants to eat dog food so he can be just like Spike.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                    "part_file": "/volume1/media/Cartoons/Rugrats/Season 01/Rugrats.S01E01.mp4"
                },
                {
                    "ratingKey": "10302",
                    "title": "Barbeque Story",
                    "season": 1,
                    "episode": 2,
                    "duration": 680,
                    "summary": "Tommy's new ball goes over the fence into neighbor Angelica's yard.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
                    "part_file": "/volume1/media/Cartoons/Rugrats/Season 01/Rugrats.S01E02.mp4"
                }
            ]
        },
        "104": {
            "ratingKey": "104",
            "title": "Dexter's Laboratory",
            "year": 1996,
            "summary": "A boy genius invents brilliant machines in his secret basement laboratory while trying to keep his sister Dee Dee out.",
            "genres": ["Animation", "Sci-Fi", "Comedy"],
            "leafCount": 2,
            "thumb": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=300&q=80",
            "episodes": [
                {
                    "ratingKey": "10401",
                    "title": "DeeDee's Room",
                    "season": 1,
                    "episode": 1,
                    "duration": 600,
                    "summary": "Dexter ventures into Dee Dee's mysterious bedroom to recover a stolen gadget.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
                    "part_file": "/volume1/media/Cartoons/Dexter/Season 01/Dexter.S01E01.mp4"
                },
                {
                    "ratingKey": "10402",
                    "title": "Maternal Combat",
                    "season": 1,
                    "episode": 2,
                    "duration": 600,
                    "summary": "Dexter creates a Mom-Droid when his mother falls ill.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
                    "part_file": "/volume1/media/Cartoons/Dexter/Season 01/Dexter.S01E02.mp4"
                }
            ]
        },
        "105": {
            "ratingKey": "105",
            "title": "Batman: The Animated Series",
            "year": 1992,
            "summary": "The dark knight defends Gotham City in the definitive Art Deco animated series.",
            "genres": ["Animation", "Action", "Superheroes"],
            "leafCount": 2,
            "thumb": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=300&q=80",
            "episodes": [
                {
                    "ratingKey": "10501",
                    "title": "On Leather Wings",
                    "season": 1,
                    "episode": 1,
                    "duration": 1320,
                    "summary": "A giant bat creature terrorizes Gotham City.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
                    "part_file": "/volume1/media/Cartoons/Batman/Season 01/Batman.S01E01.mp4"
                },
                {
                    "ratingKey": "10502",
                    "title": "Christmas with the Joker",
                    "season": 1,
                    "episode": 2,
                    "duration": 1320,
                    "summary": "The Joker hijacks Gotham's airwaves on Christmas Eve.",
                    "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
                    "part_file": "/volume1/media/Cartoons/Batman/Season 01/Batman.S01E02.mp4"
                }
            ]
        }
    },
    "movies": {
        "201": {
            "ratingKey": "201",
            "title": "The Iron Giant (1999)",
            "year": 1999,
            "duration": 5160,
            "summary": "A young boy befriends a giant metallic robot who fell from space.",
            "genres": ["Animation", "Family", "Sci-Fi"],
            "thumb": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=300&q=80",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
            "part_file": "/volume1/media/Movies/The.Iron.Giant.1999.1080p.mp4"
        },
        "202": {
            "ratingKey": "202",
            "title": "Space Jam (1996)",
            "year": 1996,
            "duration": 5280,
            "summary": "In a desperate bid to win a basketball match and earn their freedom, the Looney Tunes seek the aid of retired basketball champion Michael Jordan.",
            "genres": ["Animation", "Comedy", "Family"],
            "thumb": "https://images.unsplash.com/photo-1546519638-68e109498ffc?w=300&q=80",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
            "part_file": "/volume1/media/Movies/Space.Jam.1996.mp4"
        },
        "203": {
            "ratingKey": "203",
            "title": "A Goofy Movie (1995)",
            "year": 1995,
            "duration": 4680,
            "summary": "When Goofy takes his teenage son Max on a fishing trip, he's oblivious to the fact that Max had planned to impress Roxanne at a concert.",
            "genres": ["Animation", "Adventure", "Comedy"],
            "thumb": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=300&q=80",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
            "part_file": "/volume1/media/Movies/A.Goofy.Movie.1995.mp4"
        },
        "204": {
            "ratingKey": "204",
            "title": "Toy Story (1995)",
            "year": 1995,
            "duration": 4860,
            "summary": "A cowboy doll is profoundly threatened and jealous when a new spaceman action figure supplants him as top toy in a boy's bedroom.",
            "genres": ["Animation", "Adventure", "Family"],
            "thumb": "https://images.unsplash.com/photo-1513542789411-b6a5d4f31634?w=300&q=80",
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "part_file": "/volume1/media/Movies/Toy.Story.1995.mp4"
        }
    },
    "commercials": [
        {
            "ratingKey": "301",
            "title": "Super Nintendo 'Play It Loud' (1994)",
            "duration": 60,
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
            "part_file": "/volume1/media/Bumpers/SNES_1994.mp4"
        },
        {
            "ratingKey": "302",
            "title": "Nickelodeon Slime Time Live Station ID (1998)",
            "duration": 30,
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "part_file": "/volume1/media/Bumpers/Nick_Slime_1998.mp4"
        },
        {
            "ratingKey": "303",
            "title": "Saturday Morning Cartoon Preview Block",
            "duration": 45,
            "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
            "part_file": "/volume1/media/Bumpers/Saturday_Morning_Promo.mp4"
        }
    ]
}


class PlexClient:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self):
        default = {
            "server_url": "http://192.168.1.100:32400",
            "token": "",
            "use_demo_mode": True,
            "direct_stream": True,
            "last_connected": None
        }
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    default.update(data)
            except Exception:
                pass
        return default

    def save_config(self, new_cfg):
        self.config.update(new_cfg)
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)
        return self.config

    def is_configured(self):
        return bool(self.config.get("server_url") and self.config.get("token"))

    def _wants_demo(self):
        return bool(self.config.get("use_demo_mode", True))

    def _make_request(self, path, params=None):
        """Sends authenticated JSON request to live Plex Media Server."""
        server_url = self.config.get("server_url", "").rstrip("/")
        token = self.config.get("token", "")
        
        if not server_url or not token:
            raise ValueError("Plex server URL or token not configured.")

        url_parts = urllib.parse.urlparse(server_url + path)
        query = urllib.parse.parse_qs(url_parts.query)
        if params:
            query.update(params)
        
        # Plex requires token in header or param
        query["X-Plex-Token"] = [token]
        new_query = urllib.parse.urlencode(query, doseq=True)
        full_url = urllib.parse.urlunparse((
            url_parts.scheme, url_parts.netloc, url_parts.path,
            url_parts.params, new_query, url_parts.fragment
        ))

        req = urllib.request.Request(full_url)
        req.add_header("Accept", "application/json")
        req.add_header("X-Plex-Client-Identifier", "nostalgia-tv-kiosk")
        req.add_header("X-Plex-Product", "Nostalgia TV")
        req.add_header("X-Plex-Version", "1.0.0")

        # 4-second timeout to keep UI snappy
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data

    def test_connection(self, url=None, token=None):
        """Tests connection to specified or configured Plex Media Server."""
        test_url = (url or self.config.get("server_url", "")).rstrip("/")
        test_token = token or self.config.get("token", "")

        # If empty or explicitly demo mode, return simulated server success
        if not test_token or self.config.get("use_demo_mode", False):
            return {
                "success": True,
                "is_demo": True,
                "message": "Connected to Plex Media Server (Simulated Demo Mode)",
                "server_info": DEMO_PLEX_DATA["server_info"]
            }

        try:
            full_url = f"{test_url}/identity?X-Plex-Token={test_token}"
            req = urllib.request.Request(full_url)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                mc = data.get("MediaContainer", {})
                return {
                    "success": True,
                    "is_demo": False,
                    "message": "Successfully connected to live Plex Media Server!",
                    "server_info": {
                        "name": mc.get("friendlyName", "Plex Server"),
                        "version": mc.get("version", "Unknown"),
                        "machineIdentifier": mc.get("machineIdentifier", ""),
                        "platform": mc.get("platform", "Plex")
                    }
                }
        except Exception as e:
            # Fall back to demo mode with friendly warning
            return {
                "success": False,
                "is_demo": False,
                "message": f"Connection to Plex server failed: {str(e)}",
                "fallback_available": True
            }

    def get_libraries(self):
        """Retrieves all TV Show and Movie libraries from Plex."""
        if self._wants_demo():
            return DEMO_PLEX_DATA["libraries"]
        if not self.is_configured():
            return []

        try:
            data = self._make_request("/library/sections")
            sections = data.get("MediaContainer", {}).get("Directory", [])
            results = []
            for s in sections:
                if s.get("type") in ["show", "movie"]:
                    results.append({
                        "id": s.get("key"),
                        "key": s.get("key"),
                        "title": s.get("title"),
                        "type": s.get("type"),
                        "count": s.get("count", 0),
                        "thumb": s.get("thumb")
                    })
            return results
        except Exception:
            return []

    def get_library_items(self, section_id):
        """Retrieves all shows or movies in a given library section."""
        if self._wants_demo():
            if str(section_id) == "1":
                return list(DEMO_PLEX_DATA["shows"].values())
            elif str(section_id) == "2":
                return list(DEMO_PLEX_DATA["movies"].values())
            elif str(section_id) == "3":
                return DEMO_PLEX_DATA["commercials"]
            return []
        if not self.is_configured():
            return []

        try:
            data = self._make_request(f"/library/sections/{section_id}/all")
            mc = data.get("MediaContainer", {})
            metadata = mc.get("Metadata", [])
            items = []
            server_url = self.config.get("server_url", "").rstrip("/")
            token = self.config.get("token", "")

            for m in metadata:
                item_type = m.get("type")
                thumb = m.get("thumb")
                if thumb and not thumb.startswith("http"):
                    thumb = f"{server_url}{thumb}?X-Plex-Token={token}"

                item = {
                    "ratingKey": m.get("ratingKey"),
                    "title": m.get("title"),
                    "year": m.get("year"),
                    "type": item_type,
                    "summary": m.get("summary", ""),
                    "thumb": thumb or "",
                    "leafCount": m.get("leafCount", 0)
                }

                if item_type == "movie":
                    dur_ms = m.get("duration", 3600000)
                    item["duration"] = int(dur_ms / 1000)
                    # Extract streaming URL from media parts
                    media = m.get("Media", [])
                    if media and media[0].get("Part"):
                        part = media[0]["Part"][0]
                        item["part_file"] = part.get("file", "")
                        item["video_url"] = f"{server_url}{part.get('key')}?X-Plex-Token={token}"

                items.append(item)
            return items
        except Exception:
            return []

    def get_show_episodes(self, rating_key):
        """Retrieves all episodes of a TV show with durations and streaming URLs."""
        if self._wants_demo():
            show = DEMO_PLEX_DATA["shows"].get(str(rating_key))
            if show:
                return {
                    "show_title": show["title"],
                    "episodes": show["episodes"]
                }
            return {"show_title": "Unknown Show", "episodes": []}
        if not self.is_configured():
            return {"show_title": "", "episodes": []}

        try:
            data = self._make_request(f"/library/metadata/{rating_key}/allLeaves")
            mc = data.get("MediaContainer", {})
            metadata = mc.get("Metadata", [])
            server_url = self.config.get("server_url", "").rstrip("/")
            token = self.config.get("token", "")
            show_title = mc.get("title2") or mc.get("parentTitle") or "TV Show"

            episodes = []
            for ep in metadata:
                dur_ms = ep.get("duration", 1320000)
                media = ep.get("Media", [])
                video_url = ""
                part_file = ""
                if media and media[0].get("Part"):
                    part = media[0]["Part"][0]
                    part_file = part.get("file", "")
                    video_url = f"{server_url}{part.get('key')}?X-Plex-Token={token}"

                episodes.append({
                    "ratingKey": ep.get("ratingKey"),
                    "title": f"S{ep.get('parentIndex', 1):02d}E{ep.get('index', 1):02d} - {ep.get('title', 'Episode')}",
                    "season": ep.get("parentIndex", 1),
                    "episode": ep.get("index", 1),
                    "duration": int(dur_ms / 1000),
                    "summary": ep.get("summary", ""),
                    "video_url": video_url,
                    "part_file": part_file
                })

            return {
                "show_title": show_title,
                "episodes": episodes
            }
        except Exception:
            return {"show_title": "", "episodes": []}

    def search(self, query):
        """Searches Plex library for cartoons, shows, or movies matching a query."""
        if not query:
            return []
        q = query.lower()
        results = []

        # Check demo shows & movies
        for s in DEMO_PLEX_DATA["shows"].values():
            if q in s["title"].lower() or any(q in g.lower() for g in s.get("genres", [])):
                results.append({"type": "show", "data": s})

        for m in DEMO_PLEX_DATA["movies"].values():
            if q in m["title"].lower():
                results.append({"type": "movie", "data": m})

        return results
