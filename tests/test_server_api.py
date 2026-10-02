import unittest
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from server import load_channels_data, get_local_ip, SimulatedBroadcastEngine

class TestServerAPI(unittest.TestCase):
    def test_load_channels_data(self):
        data = load_channels_data()
        self.assertIn("channels", data)
        self.assertIn("global", data)
        self.assertIn("1", data["channels"])

    def test_get_local_ip(self):
        ip = get_local_ip()
        self.assertIsInstance(ip, str)
        self.assertEqual(len(ip.split(".")), 4)

    def test_engine_dynamic_tune(self):
        engine = SimulatedBroadcastEngine()
        engine.active_channel = 3
        self.assertEqual(engine.active_channel == 3, True)
        status = engine.get_channel_status(3)
        self.assertEqual(status["channel"], 3)

if __name__ == "__main__":
    unittest.main()
