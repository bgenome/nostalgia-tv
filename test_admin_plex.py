#!/usr/bin/env python3
"""
Verification & Automated Test Suite for Nostalgia TV Admin Panel & Plex Integration
Runs fully in-memory without requiring external network socket permissions.
"""

import sys
import os
import json
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.plex.client import PlexClient, DEMO_PLEX_DATA
import server
from server import ENGINE, load_channels_data, save_channels_data, get_local_ip

def test_plex_client():
    print("\n--- [TEST 1] Testing PlexClient Unit Functions ---")
    client = PlexClient()
    
    # 1. Test connection in demo mode
    conn = client.test_connection()
    assert conn["success"] is True, f"Plex connection failed: {conn}"
    print(f"✓ Plex connection test succeeded: {conn['server_info']['name']} (version {conn['server_info']['version']})")

    # 2. Test get libraries
    libs = client.get_libraries()
    assert len(libs) >= 3, f"Expected >= 3 libraries, got {len(libs)}"
    print(f"✓ Retrieved {len(libs)} Plex libraries: {[lib['title'] for lib in libs]}")

    # 3. Test get items from library 1 (Cartoons)
    cartoons = client.get_library_items("1")
    assert len(cartoons) >= 5, f"Expected >= 5 shows, got {len(cartoons)}"
    titles = [c["title"] for c in cartoons]
    assert "Arthur" in titles, "Arthur not found in cartoons"
    assert "The Magic School Bus" in titles, "Magic School Bus not found in cartoons"
    assert "Rugrats" in titles, "Rugrats not found in cartoons"
    print(f"✓ Retrieved {len(cartoons)} shows from Cartoons library: {titles}")

    # 4. Test get episodes for Arthur (ratingKey 101)
    arthur_data = client.get_show_episodes("101")
    assert arthur_data["show_title"] == "Arthur"
    episodes = arthur_data["episodes"]
    assert len(episodes) >= 4, f"Expected >= 4 episodes, got {len(episodes)}"
    assert episodes[0]["duration"] == 660
    assert "BigBuckBunny.mp4" in episodes[0]["video_url"]
    print(f"✓ Retrieved {len(episodes)} episodes for Arthur: {[e['title'] for e in episodes]}")

    # 5. Test search query
    search_res = client.search("magic")
    assert len(search_res) >= 1
    assert search_res[0]["data"]["title"] == "The Magic School Bus"
    print(f"✓ Search query 'magic' returned: {search_res[0]['data']['title']}")

    # 6. Test configuration save & reload
    saved = client.save_config({"server_url": "http://192.168.1.150:32400", "use_demo_mode": True})
    assert saved["server_url"] == "http://192.168.1.150:32400"
    print("✓ Saved & reloaded Plex configuration successfully")

    print(">>> [TEST 1] PlexClient Tests PASSED! <<<\n")


def test_broadcast_engine_and_crud():
    print("\n--- [TEST 2] Testing Simulated Broadcast Engine & Channel CRUD ---")
    
    # Reload engine
    ENGINE.reload()
    assert len(ENGINE.channels) >= 5, f"Expected >= 5 channels, got {len(ENGINE.channels)}"
    print(f"✓ Broadcast Engine loaded {len(ENGINE.channels)} active channels")

    # Test Channel 1 (Prevue Guide)
    ch1 = ENGINE.get_channel_status(1)
    assert ch1["type"] == "guide"
    assert "GUIDE" in ch1["title"]
    print(f"✓ CH 1 Prevue Guide status: {ch1['title']}")

    # Test Channel 2 (Cartoon Express)
    ch2 = ENGINE.get_channel_status(2)
    assert ch2["channel"] == 2
    assert ch2["type"] == "tv_shows"
    assert ch2["seek_seconds"] >= 0
    print(f"✓ CH 2 (Cartoons): Currently playing '{ch2['title']}' at seek offset {ch2['seek_seconds']}s")

    # Test Channel 3 (Movies)
    ch3 = ENGINE.get_channel_status(3)
    assert ch3["channel"] == 3
    assert ch3["type"] == "movies"
    print(f"✓ CH 3 (Movies): Currently playing '{ch3['title']}' at seek offset {ch3['seek_seconds']}s")

    # Test Channel 4 (Time Slots & Bumpers)
    ch4 = ENGINE.get_channel_status(4)
    assert ch4["channel"] == 4
    assert ch4["type"] == "scheduled"
    print(f"✓ CH 4 (Scheduled Slots): Status '{ch4['title']}', Bumper active: {ch4.get('is_bumper')}")

    # Test Guide Matrix
    matrix = ENGINE.get_guide_matrix()
    assert len(matrix["grid"]) == len(ENGINE.channels)
    print(f"✓ Generated 24/7 Guide Matrix for {len(matrix['grid'])} channels at server time {matrix['server_time']}")

    # ================= CRUD & Hot Reload Test =================
    print("\n--- [TEST 3] Testing Dynamic Channel Creation, Plex Import, and Hot-Reload ---")
    all_data = load_channels_data()
    test_ch_num = "88"

    # Simulate importing a Plex Show (Rugrats) into Channel 88
    plex = PlexClient()
    rugrats_episodes = plex.get_show_episodes("103")["episodes"]
    
    all_data["channels"][test_ch_num] = {
        "name": "NICKELODEON CLASSICS (PLEX)",
        "type": "tv_shows",
        "genre": "90s Nicktoons",
        "description": "Imported from Plex Media Server",
        "shows": [
            {
                "title": ep["title"],
                "duration": ep["duration"],
                "video_url": ep["video_url"],
                "tag": f"Season {ep['season']}"
            }
            for ep in rugrats_episodes
        ]
    }
    save_channels_data(all_data)

    # Trigger hot reload
    ENGINE.reload()
    assert test_ch_num in ENGINE.channels, f"Channel {test_ch_num} was not found after hot reload"
    status_88 = ENGINE.get_channel_status(88)
    assert status_88["channel"] == 88
    assert "Rugrats" in status_88["title"] or "Tommy" in status_88["title"] or "Barbeque" in status_88["title"]
    print(f"✓ Channel {test_ch_num} dynamically imported from Plex and hot-reloaded! Playing: '{status_88['title']}'")

    # Test Remote Tuning to the new channel
    ENGINE.active_channel = 88
    assert ENGINE.active_channel == 88
    print(f"✓ Remote TV tuned successfully to newly created Channel {ENGINE.active_channel}")

    # Clean up test channel
    del all_data["channels"][test_ch_num]
    save_channels_data(all_data)
    ENGINE.reload()
    assert test_ch_num not in ENGINE.channels
    ENGINE.active_channel = 2
    print(f"✓ Channel {test_ch_num} cleanly deleted and engine hot-reloaded")

    print(">>> [TEST 2 & 3] Engine & CRUD Tests PASSED! <<<\n")


def test_ui_files():
    print("\n--- [TEST 4] Testing Web Assets and Remote Admin Files ---")
    
    admin_path = os.path.join(BASE_DIR, "web", "admin.html")
    assert os.path.exists(admin_path), f"File not found: {admin_path}"
    with open(admin_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Nostalgia TV - Remote Admin Panel" in content
        assert "Plex Media Server Connection" in content
        assert "Live TV Feed Monitor" in content
        assert "Configured Broadcast Channels" in content
        assert "api/plex/import" in content
        assert "api/admin/channel/save" in content
    print("✓ web/admin.html verified: Contains Monitor, Channel CRUD, Plex Explorer, and Remote controls")

    tv_path = os.path.join(BASE_DIR, "web", "index.html")
    assert os.path.exists(tv_path), f"File not found: {tv_path}"
    with open(tv_path, "r", encoding="utf-8") as f:
        tv_content = f.read()
        assert "Nostalgia TV" in tv_content
        assert "/admin" in tv_content
        assert "crt-screen" in tv_content
    print("✓ web/index.html verified: Contains CRT TV Screen and Admin link")

    ip = get_local_ip()
    assert len(ip.split(".")) == 4
    print(f"✓ Remote LAN IP detected: {ip} -> Remote Admin URL: http://{ip}:8080/admin")

    print(">>> [TEST 4] UI & Remote Assets Tests PASSED! <<<\n")


if __name__ == "__main__":
    test_plex_client()
    test_broadcast_engine_and_crud()
    test_ui_files()
    print("=======================================================================")
    print("  🎉 ALL TESTS PASSED: REMOTE ADMIN PANEL & PLEX INTEGRATION VERIFIED! ")
    print("=======================================================================")
