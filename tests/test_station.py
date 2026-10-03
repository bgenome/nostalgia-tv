import json
import os
import shutil
import tempfile
import unittest
import urllib.error
from datetime import timedelta
from pathlib import Path

from src.remote.keys import action_for_cec_line
from src.station.clock import EPOCH, ClockedLineup
from src.station.files import channels_from_root, directory_has_video, find_library, write_channels_yaml
from src.station.messages import BUYER_TEXT, CLOCKS
from src.station.plex_lineup import PlexScheduler, build_plex_channels
from src.station.plex_link import PlexLink, PlexLinkError, choose_servers
from src.station.store import save_files_station, save_plex_station, station_ready


class TestClockedLineup(unittest.TestCase):
    def test_position_wraps_on_the_epoch_clock(self):
        lineup = ClockedLineup([
            {"url": "a.mp4", "duration": 100},
            {"url": "b.mp4", "duration": 100},
        ])
        url, seek = lineup.current(EPOCH + timedelta(seconds=150))
        self.assertEqual(url, "b.mp4")
        self.assertEqual(seek, 50)
        url, seek = lineup.current(EPOCH + timedelta(seconds=250))
        self.assertEqual(url, "a.mp4")
        self.assertEqual(seek, 50)

    def test_empty_lineup_is_off_air(self):
        self.assertEqual(ClockedLineup([]).current(EPOCH), ("OFF_AIR", 0))


class TestLocalLibrary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_subfolders_become_channels(self):
        cartoons = os.path.join(self.tmp, "Cartoons")
        movies = os.path.join(self.tmp, "Movies")
        os.makedirs(cartoons)
        os.makedirs(movies)
        open(os.path.join(cartoons, "one.mp4"), "wb").close()
        open(os.path.join(movies, "two.mkv"), "wb").close()
        channels = channels_from_root(self.tmp)
        self.assertEqual([channel["number"] for channel in channels], [2, 3])
        self.assertEqual(channels[0]["directory"], cartoons)
        self.assertTrue(directory_has_video(cartoons))

    def test_find_library_skips_empty_roots(self):
        empty = os.path.join(self.tmp, "empty")
        full = os.path.join(self.tmp, "full")
        os.makedirs(empty)
        os.makedirs(full)
        open(os.path.join(full, "show.mp4"), "wb").close()
        found = find_library([empty, full])
        self.assertEqual(found[0]["directory"], full)

    def test_station_ready_follows_the_saved_directories(self):
        folder = os.path.join(self.tmp, "Shows")
        os.makedirs(folder)
        open(os.path.join(folder, "ep.mp4"), "wb").close()
        app = os.path.join(self.tmp, "app")
        os.makedirs(app)
        channels = channels_from_root(self.tmp)
        save_files_station(app, channels, "UTC")
        self.assertTrue(station_ready(app))
        os.remove(os.path.join(folder, "ep.mp4"))
        self.assertFalse(station_ready(app))

    def test_yaml_lists_the_directory(self):
        path = os.path.join(self.tmp, "data", "channels.yaml")
        write_channels_yaml(path, [{
            "number": 2,
            "name": "Cartoons",
            "type": "tv_shows",
            "directory": "/media/library/Cartoons",
        }])
        text = Path(path).read_text(encoding="utf-8")
        self.assertIn("/media/library/Cartoons", text)
        self.assertIn("Cartoons", text)


class TestPlexStation(unittest.TestCase):
    def test_demo_mode_is_not_a_lineup(self):
        class DemoClient:
            config = {"use_demo_mode": True, "token": "x", "server_url": "http://plex"}

            def is_configured(self):
                return True

            def get_libraries(self):
                raise AssertionError("demo catalog must not be read")

        self.assertEqual(build_plex_channels(DemoClient()), [])

    def test_live_libraries_become_channels(self):
        class LiveClient:
            config = {"use_demo_mode": False, "token": "t", "server_url": "http://plex"}

            def is_configured(self):
                return True

            def get_libraries(self):
                return [
                    {"key": "1", "title": "Cartoons", "type": "show"},
                    {"key": "2", "title": "Films", "type": "movie"},
                ]

            def get_library_items(self, section_id):
                if str(section_id) == "1":
                    return [{"ratingKey": "9", "title": "Show", "type": "show"}]
                return [{"title": "Film", "type": "movie", "duration": 30, "video_url": "http://plex/m"}]

            def get_show_episodes(self, rating_key):
                return {"episodes": [{"title": "One", "duration": 10, "video_url": "http://plex/e"}]}

        channels = build_plex_channels(LiveClient())
        self.assertEqual([channel["number"] for channel in channels], [2, 3])
        scheduler = PlexScheduler(channels)
        url, _seek = scheduler.get_currently_playing(2, EPOCH)
        self.assertEqual(url, "http://plex/e")

    def test_saved_plex_token_stays_on_the_device_config(self):
        app = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, app)
        save_plex_station(app, "http://192.168.1.20:32400", "device-token", "UTC")
        with open(os.path.join(app, "data", "plex_config.json"), encoding="utf-8") as handle:
            plex = json.load(handle)
        self.assertEqual(plex["token"], "device-token")
        self.assertIs(plex["use_demo_mode"], False)
        self.assertTrue(station_ready(app))


class TestPlexLink(unittest.TestCase):
    def test_pin_and_local_server(self):
        def opener(request, timeout=0):
            self.assertGreater(timeout, 0)

            class Response:
                def __init__(self, payload):
                    self.payload = payload

                def read(self):
                    return json.dumps(self.payload).encode()

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return False

            if request.get_method() == "POST":
                return Response({"id": 7, "code": "WXYZ"})
            if "/pins/" in request.full_url:
                return Response({"id": 7, "code": "WXYZ", "authToken": "account-token"})
            return Response([{
                "name": "Home",
                "provides": "server",
                "accessToken": "server-token",
                "connections": [
                    {"uri": "https://relay.example", "local": False, "relay": True, "protocol": "https"},
                    {"uri": "http://192.168.1.20:32400", "local": True, "relay": False, "protocol": "http"},
                ],
            }])

        link = PlexLink("client", opener=opener, timeout=3)
        pin_id, code = link.create_pin()
        self.assertEqual((pin_id, code), (7, "WXYZ"))
        self.assertEqual(link.poll_pin(pin_id), "account-token")
        servers = link.list_servers("account-token")
        self.assertEqual(servers[0]["server_url"], "http://192.168.1.20:32400")
        self.assertEqual(servers[0]["token"], "server-token")

    def test_network_error(self):
        def opener(request, timeout=0):
            raise urllib.error.URLError("down")

        link = PlexLink("client", opener=opener)
        with self.assertRaises(PlexLinkError) as caught:
            link.create_pin()
        self.assertEqual(caught.exception.code, "network")

    def test_expired_pin(self):
        def opener(request, timeout=0):
            raise urllib.error.HTTPError(request.full_url, 404, "missing", {}, None)

        link = PlexLink("client", opener=opener)
        with self.assertRaises(PlexLinkError) as caught:
            link.poll_pin(7)
        self.assertEqual(caught.exception.code, "expired")

    def test_choose_servers_skips_players(self):
        servers = choose_servers([
            {"name": "Phone", "provides": "player", "connections": []},
        ], "account-token")
        self.assertEqual(servers, [])


class TestBuyerLanguage(unittest.TestCase):
    def test_on_screen_sentences_have_no_hyphen_or_dash(self):
        for sentence in BUYER_TEXT:
            self.assertNotIn("-", sentence)
            self.assertNotIn("\u2013", sentence)
            self.assertNotIn("\u2014", sentence)

    def test_clock_labels_match_the_timezone_script(self):
        script = Path("image/rootfs/usr/local/sbin/nostalgia-set-timezone").read_text(encoding="utf-8")
        for _label, zone in CLOCKS:
            self.assertIn(zone, script)


class TestCecKeys(unittest.TestCase):
    def test_channel_buttons(self):
        self.assertEqual(action_for_cec_line("key pressed: channel up (30)"), "ch_up")
        self.assertEqual(action_for_cec_line("DEBUG: key pressed: channel down (31)"), "ch_down")
        self.assertEqual(action_for_cec_line("key pressed: select (0)"), "select")
        self.assertIsNone(action_for_cec_line("key released: up (1)"))
