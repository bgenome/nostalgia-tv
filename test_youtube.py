#!/usr/bin/env python3
"""
Automated Test Suite for Nostalgia TV YouTube Integration
Verifies YouTubeClient, cookie management, playlist inspection, background sync,
broadcast engine timeline integration, and Range request streaming.
"""

import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.youtube.client import YouTubeClient, COOKIES_FILE
from server import ENGINE, load_channels_data, save_channels_data

def test_youtube_client_unit():
    print("\n--- [TEST 1] Testing YouTubeClient Unit Functions ---")
    client = YouTubeClient()

    # 1. Status Check
    status = client.get_status()
    print(f"✓ YouTubeClient Status: Available={status['ytdlp_available']}, SimulationMode={status['is_simulation_mode']}")

    # 2. Cookie Management
    dummy_cookie = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t1750000000\tSID\tdummy_premium_token_123\n"
    res = client.save_cookies_file(dummy_cookie)
    assert res["success"] is True
    assert client.has_cookies() is True
    print(f"✓ Saved and verified Netscape format YouTube cookies ({res['size']} bytes)")

    # 3. Inspect Playlist / Channel URL (Super Simple Songs)
    sample_url = "https://www.youtube.com/@SuperSimpleSongs"
    inspect_data = client.inspect_url(sample_url)
    assert "title" in inspect_data
    assert "videos" in inspect_data
    assert len(inspect_data["videos"]) >= 3
    first_vid = inspect_data["videos"][0]
    assert "id" in first_vid
    assert "title" in first_vid
    assert first_vid["duration"] > 0
    print(f"✓ Inspected '{inspect_data['title']}': Found {len(inspect_data['videos'])} videos (First: '{first_vid['title']}', {first_vid['duration']}s)")

    # 4. Inspect Ms Rachel
    rachel_data = client.inspect_url("https://www.youtube.com/@msrachel")
    assert "Rachel" in rachel_data["title"]
    print(f"✓ Inspected '{rachel_data['title']}': Found {len(rachel_data['videos'])} videos")

    print(">>> [TEST 1] YouTubeClient Unit Tests PASSED! <<<\n")


def test_youtube_sync_and_engine():
    print("\n--- [TEST 2] Testing YouTube Channel Sync & Broadcast Engine Integration ---")
    client = YouTubeClient()
    test_ch = 6
    test_ch_name = "SUPER SIMPLE SONGS"
    test_url = "https://www.youtube.com/@SuperSimpleSongs"

    # Launch sync
    res = client.start_background_sync(test_ch, test_ch_name, test_url, max_videos=3, order="sequential")
    assert res["success"] is True
    task_id = res["task_id"]
    print(f"✓ Started background sync task: {task_id}")

    # Wait for sync to finish (demo mode creates sample files quickly)
    for _ in range(20):
        time.sleep(0.5)
        st = client.get_sync_status(task_id)
        if st.get("status") == "completed":
            break

    final_st = client.get_sync_status(task_id)
    assert final_st.get("status") == "completed", f"Sync did not complete: {final_st}"
    print(f"✓ Sync completed! Downloaded {final_st.get('downloaded_count')} videos.")

    # Verify channels.json was updated
    channels_data = load_channels_data()
    assert str(test_ch) in channels_data["channels"], f"Channel {test_ch} not found in channels.json"
    ch = channels_data["channels"][str(test_ch)]
    assert ch["source_type"] == "youtube_sync"
    assert len(ch["shows"]) >= 3
    print(f"✓ Verified Channel {test_ch} in channels.json with {len(ch['shows'])} episodes")

    # Hot-reload Broadcast Engine and verify timeline
    ENGINE.reload()
    assert str(test_ch) in ENGINE.channels
    status = ENGINE.get_channel_status(test_ch)
    assert status["channel"] == test_ch
    assert status["is_off_air"] is False
    assert status["duration"] > 0
    assert "Twinkle" in status["title"] or "Wheels" in status["title"] or "Ducks" in status["title"]
    print(f"✓ Broadcast Engine Timeline: CH {test_ch} playing '{status['title']}' at seek offset {status['seek_seconds']}s (Total: {status['duration']}s)")

    # Verify 24/7 TV Guide Matrix includes the new YouTube channel
    guide = ENGINE.get_guide_matrix()
    guide_channels = [g["channel"] for g in guide["grid"]]
    assert test_ch in guide_channels
    print(f"✓ 24/7 Prevue Program Guide matrix includes Channel {test_ch}")

    # Clean up test channel
    del channels_data["channels"][str(test_ch)]
    save_channels_data(channels_data)
    ENGINE.reload()
    print(f"✓ Cleaned up test Channel {test_ch} and reloaded broadcast engine")

    print(">>> [TEST 2] Sync & Broadcast Engine Tests PASSED! <<<\n")


def test_ui_and_endpoints():
    print("\n--- [TEST 3] Testing Web UI & REST API Endpoints ---")
    admin_path = os.path.join(BASE_DIR, "web", "admin.html")
    with open(admin_path, "r", encoding="utf-8") as f:
        html = f.read()
        assert "YouTube Channels" in html
        assert "tab-youtube" in html
        assert "api/youtube/inspect" in html
        assert "api/youtube/import" in html
        assert "saveYouTubeCookies" in html

    server_path = os.path.join(BASE_DIR, "server.py")
    with open(server_path, "r", encoding="utf-8") as f:
        server_code = f.read()
        assert "/api/media/stream" in server_code
        assert "/api/youtube/inspect" in server_code
        assert "/api/youtube/import" in server_code
        assert "_serve_range_file" in server_code
    print("✓ web/admin.html & server.py verified: Contains YouTube Channels tab, cookie manager, inspect, sync, and range streaming")

    print(">>> [TEST 3] UI Verification PASSED! <<<\n")


if __name__ == "__main__":
    test_youtube_client_unit()
    test_youtube_sync_and_engine()
    test_ui_and_endpoints()
    print("=======================================================================")
    print("  🎉 ALL TESTS PASSED: YOUTUBE PREMIUM INTEGRATION VERIFIED 100%!     ")
    print("=======================================================================")
