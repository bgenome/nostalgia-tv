import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.plex.client import PlexClient

class TestPlexClient(unittest.TestCase):
    def setUp(self):
        self.client = PlexClient()

    def test_plex_connection_demo_mode(self):
        conn = self.client.test_connection()
        self.assertTrue(conn["success"])
        self.assertIn("server_info", conn)
        self.assertIsNotNone(conn["server_info"]["name"])

    def test_plex_get_libraries(self):
        libs = self.client.get_libraries()
        self.assertIsInstance(libs, list)
        self.assertGreaterEqual(len(libs), 1)
        titles = [l["title"] for l in libs]
        self.assertTrue(any("Cartoons" in t for t in titles))

    def test_plex_get_items(self):
        cartoons = self.client.get_library_items("1")
        self.assertIsInstance(cartoons, list)
        self.assertGreaterEqual(len(cartoons), 1)
        titles = [c["title"] for c in cartoons]
        self.assertIn("Arthur", titles)

    def test_plex_get_show_episodes(self):
        arthur_data = self.client.get_show_episodes("101")
        self.assertEqual(arthur_data["show_title"], "Arthur")
        self.assertGreaterEqual(len(arthur_data["episodes"]), 1)
        first_ep = arthur_data["episodes"][0]
        self.assertGreater(first_ep["duration"], 0)
        self.assertIn("video_url", first_ep)

    def test_plex_search(self):
        results = self.client.search("Arthur")
        self.assertGreaterEqual(len(results), 1)
        self.assertTrue(any("Arthur" in r["data"]["title"] for r in results))

    def test_live_mode_without_token_is_empty(self):
        self.client.config["use_demo_mode"] = False
        self.client.config["token"] = ""
        self.client.config["server_url"] = ""
        self.assertEqual(self.client.get_libraries(), [])
        self.assertEqual(self.client.get_library_items("1"), [])
        self.assertEqual(self.client.get_show_episodes("101")["episodes"], [])

    def test_live_mode_failure_does_not_use_demo_library(self):
        self.client.config["use_demo_mode"] = False
        self.client.config["server_url"] = "http://plex.example:32400"
        self.client.config["token"] = "device-token"

        def fail(*args, **kwargs):
            raise OSError("down")

        self.client._make_request = fail
        self.assertEqual(self.client.get_libraries(), [])
        self.assertEqual(self.client.get_library_items("1"), [])
        self.assertEqual(self.client.get_show_episodes("101")["episodes"], [])

if __name__ == "__main__":
    unittest.main()
