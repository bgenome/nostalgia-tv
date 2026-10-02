import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.youtube.client import YouTubeClient

class TestYouTubeClient(unittest.TestCase):
    def setUp(self):
        self.client = YouTubeClient()

    def test_youtube_status(self):
        status = self.client.get_status()
        self.assertIn("ytdlp_available", status)
        self.assertIn("is_simulation_mode", status)
        self.assertIn("cookies_configured", status)

    def test_youtube_inspect_url(self):
        sample_url = "https://www.youtube.com/@SuperSimpleSongs"
        data = self.client.inspect_url(sample_url)
        self.assertIn("title", data)
        self.assertIn("videos", data)
        self.assertGreaterEqual(len(data["videos"]), 1)
        self.assertIn("duration", data["videos"][0])

    def test_youtube_cookies_save_and_check(self):
        cookie_sample = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t1750000000\tSID\ttest_token_xyz\n"
        res = self.client.save_cookies_file(cookie_sample)
        self.assertTrue(res["success"])
        self.assertTrue(self.client.has_cookies())

if __name__ == "__main__":
    unittest.main()
