"""Map cec-client key lines to kiosk actions."""

import re

_PRESSED = re.compile(r"key pressed:\s*(.+?)\s*\(", re.IGNORECASE)

_ACTIONS = {
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "select": "select",
    "enter": "select",
    "ok": "select",
    "exit": "back",
    "return": "back",
    "back": "back",
    "channel up": "ch_up",
    "channel down": "ch_down",
}


def action_for_cec_line(line):
    match = _PRESSED.search(line or "")
    if not match:
        return None
    return _ACTIONS.get(match.group(1).strip().lower())
