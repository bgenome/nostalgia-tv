import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from server import SimulatedBroadcastEngine, load_channels_data

class TestBroadcastEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SimulatedBroadcastEngine()

    def test_engine_initialization(self):
        self.assertIsNotNone(self.engine.channels)
        self.assertIsInstance(self.engine.channels, dict)
        self.assertGreater(len(self.engine.channels), 0)

    def test_channel_guide_status(self):
        status = self.engine.get_channel_status(1)
        self.assertEqual(status["channel"], 1)
        self.assertEqual(status["type"], "guide")
        self.assertIn("GUIDE", status["title"].upper())

    def test_channel_off_air(self):
        status = self.engine.get_channel_status(9999)
        self.assertTrue(status["is_off_air"])
        self.assertEqual(status["type"], "static")

    def test_channel_playback_timeline(self):
        status = self.engine.get_channel_status(2)
        self.assertEqual(status["channel"], 2)
        self.assertEqual(status["type"], "tv_shows")
        self.assertGreaterEqual(status["seek_seconds"], 0)
        self.assertGreater(status["duration"], 0)
        self.assertLessEqual(status["seek_seconds"], status["duration"])

    def test_guide_matrix_generation(self):
        matrix = self.engine.get_guide_matrix()
        self.assertIn("server_time", matrix)
        self.assertIn("grid", matrix)
        self.assertGreaterEqual(len(matrix["grid"]), 1)

if __name__ == "__main__":
    unittest.main()
