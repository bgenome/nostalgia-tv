"""Clock aligned playback over a fixed list of items."""

from datetime import datetime

EPOCH = datetime(2020, 1, 1)
FALLBACK_DURATION = 1200.0


class ClockedLineup:
    def __init__(self, items):
        self.items = []
        total = 0.0
        for item in items:
            try:
                duration = float(item.get("duration", 0))
            except (TypeError, ValueError):
                duration = 0.0
            if duration <= 0:
                duration = FALLBACK_DURATION
            self.items.append({
                "url": item.get("url") or "OFF_AIR",
                "duration": duration,
                "start": total,
            })
            total += duration
        self.total = total

    def current(self, now=None):
        if not self.items or self.total <= 0:
            return "OFF_AIR", 0
        if now is None:
            now = datetime.now()
        position = (now - EPOCH).total_seconds() % self.total
        for item in self.items:
            end = item["start"] + item["duration"]
            if item["start"] <= position < end:
                return item["url"], position - item["start"]
        return "OFF_AIR", 0
