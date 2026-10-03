"""Build a clock aligned station from the buyer's Plex libraries."""

from src.station.clock import ClockedLineup
from src.station.files import write_channels_yaml


class PlexScheduler:
    def __init__(self, channels):
        self.lineups = {}
        for channel in channels:
            self.lineups[int(channel["number"])] = ClockedLineup(channel.get("items") or [])

    def get_currently_playing(self, channel_num, current_dt=None):
        lineup = self.lineups.get(int(channel_num))
        if lineup is None:
            return "OFF_AIR", 0
        return lineup.current(current_dt)


def build_plex_channels(client):
    if client.config.get("use_demo_mode", True) or not client.is_configured():
        return []
    libraries = client.get_libraries()
    channels = []
    number = 2
    for library in libraries:
        section_id = library.get("key") or library.get("id")
        kind = library.get("type")
        items = _items_for_library(client, section_id, kind)
        if not items:
            continue
        channels.append({
            "number": number,
            "name": library.get("title") or f"Channel {number}",
            "type": "movies" if kind == "movie" else "tv_shows",
            "directory": "",
            "items": items,
        })
        number += 1
    return channels


def write_plex_channel_names(path, channels):
    write_channels_yaml(path, channels)


def _items_for_library(client, section_id, kind):
    entries = client.get_library_items(section_id)
    items = []
    if kind == "movie":
        for entry in entries:
            url = entry.get("video_url") or ""
            if not url:
                continue
            items.append({
                "url": url,
                "duration": entry.get("duration") or 0,
                "title": entry.get("title") or "",
            })
        return items

    for show in entries:
        rating_key = show.get("ratingKey")
        if not rating_key:
            continue
        payload = client.get_show_episodes(rating_key)
        for episode in payload.get("episodes") or []:
            url = episode.get("video_url") or ""
            if not url:
                continue
            items.append({
                "url": url,
                "duration": episode.get("duration") or 0,
                "title": episode.get("title") or "",
            })
    return items
