"""Pair this television with the buyer's own Plex account.

The token returned by Plex is written only on the device.
"""

import json
import urllib.error
import urllib.request

PLEX_API = "https://plex.tv/api/v2"


class PlexLinkError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


class PlexLink:
    def __init__(self, client_id, opener=None, timeout=15):
        self.client_id = client_id
        self.opener = opener or urllib.request.urlopen
        self.timeout = timeout

    def create_pin(self):
        payload = self._request("POST", f"{PLEX_API}/pins?strong=true", token=None)
        pin_id = payload.get("id")
        code = payload.get("code")
        if pin_id is None or not code:
            raise PlexLinkError("response")
        return pin_id, str(code)

    def poll_pin(self, pin_id):
        payload = self._request("GET", f"{PLEX_API}/pins/{pin_id}", token=None)
        token = payload.get("authToken")
        if token:
            return str(token)
        return None

    def list_servers(self, account_token):
        payload = self._request(
            "GET",
            f"{PLEX_API}/resources?includeHttps=1&includeRelay=1",
            token=account_token,
        )
        if isinstance(payload, dict):
            devices = payload.get("MediaContainer", {}).get("Device") or payload.get("devices") or []
        else:
            devices = payload
        if not isinstance(devices, list):
            raise PlexLinkError("response")
        return choose_servers(devices, account_token)

    def _request(self, method, url, token):
        request = urllib.request.Request(url, data=b"" if method == "POST" else None, method=method)
        request.add_header("Accept", "application/json")
        request.add_header("X-Plex-Product", "Nostalgia TV")
        request.add_header("X-Plex-Client-Identifier", self.client_id)
        request.add_header("X-Plex-Version", "1.0.0")
        request.add_header("X-Plex-Platform", "Linux")
        request.add_header("X-Plex-Device", "Raspberry Pi")
        request.add_header("X-Plex-Device-Name", "Nostalgia TV")
        if token:
            request.add_header("X-Plex-Token", token)
        try:
            with self.opener(request, timeout=self.timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise PlexLinkError("expired") from exc
            raise PlexLinkError("network") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise PlexLinkError("network") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise PlexLinkError("response") from exc


def choose_servers(devices, account_token):
    chosen = []
    for device in devices:
        provides = str(device.get("provides") or "")
        if "server" not in [part.strip() for part in provides.split(",")]:
            continue
        connection = pick_connection(device.get("connections") or [])
        if connection is None:
            continue
        token = device.get("accessToken") or account_token
        if not token:
            continue
        chosen.append({
            "name": device.get("name") or "Plex",
            "server_url": connection["uri"].rstrip("/"),
            "token": token,
        })
    return chosen


def pick_connection(connections):
    def rank(connection):
        return (
            0 if connection.get("local") else 1,
            0 if not connection.get("relay") else 1,
            0 if connection.get("protocol") == "https" else 1,
        )

    for connection in sorted(connections, key=rank):
        uri = connection.get("uri")
        if isinstance(uri, str) and uri.startswith("http"):
            return connection
    return None
