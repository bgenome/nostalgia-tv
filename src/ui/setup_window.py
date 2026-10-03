"""On screen choice of the buyer's Plex server or USB files."""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

from src.station import messages
from src.station.files import find_library
from src.station.plex_link import PlexLink, PlexLinkError
from src.station.store import (
    apply_timezone,
    client_id,
    mount_library,
    save_files_station,
    save_plex_station,
)


class SetupWindow(QDialog):
    def __init__(self, app_dir, cec_listener, notice=""):
        super().__init__()
        self.app_dir = app_dir
        self.cec = cec_listener
        self.notice = notice
        self.completed = False
        self.step = "choose"
        self.index = 0
        self.choices = []
        self.prompt = messages.CHOOSE
        self.pending = None
        self.pin_id = None
        self.pin_code = ""
        self.account_token = None
        self.servers = []
        self._connections = []

        self.setWindowTitle(messages.TITLE)
        self.setStyleSheet("background-color: black; color: #00FF00;")
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.label.setStyleSheet(
            "font-size: 36px; font-weight: bold; color: #00FF00;"
            "font-family: monospace; background-color: black; padding: 48px;"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(2000)
        self.poll_timer.timeout.connect(self._poll_pin)

        self._bind(self.cec.up_pressed, self.move_up)
        self._bind(self.cec.down_pressed, self.move_down)
        self._bind(self.cec.ch_up_pressed, self.move_up)
        self._bind(self.cec.ch_down_pressed, self.move_down)
        self._bind(self.cec.select_pressed, self.confirm)
        self._bind(self.cec.back_pressed, self.go_back)
        self._show_choose()

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowState(Qt.WindowState.WindowFullScreen)

    def _bind(self, signal, slot):
        signal.connect(slot)
        self._connections.append((signal, slot))

    def detach(self):
        self.poll_timer.stop()
        for signal, slot in self._connections:
            try:
                signal.disconnect(slot)
            except TypeError:
                pass
        self._connections = []

    def _render(self):
        lines = [messages.TITLE, ""]
        if self.notice:
            lines.extend([self.notice, ""])
        lines.extend([self.prompt, ""])
        if self.step == "plex_wait" and self.pin_code:
            lines.extend([self.pin_code, ""])
        for offset, choice in enumerate(self.choices):
            mark = ">" if offset == self.index else " "
            lines.append(f"{mark} {choice}")
        lines.extend(["", messages.REMOTE_HELP])
        self.label.setText("\n".join(lines))

    def _show_choose(self):
        self.step = "choose"
        self.index = 0
        self.prompt = messages.CHOOSE
        self.choices = [messages.CHOICE_FILES, messages.CHOICE_PLEX]
        self.poll_timer.stop()
        self._render()

    def move_up(self):
        if not self.choices:
            return
        self.index = (self.index - 1) % len(self.choices)
        self._render()

    def move_down(self):
        if not self.choices:
            return
        self.index = (self.index + 1) % len(self.choices)
        self._render()

    def go_back(self):
        if self.step != "choose":
            self.notice = ""
            self._show_choose()

    def confirm(self):
        if self.step == "choose":
            self._confirm_choice()
        elif self.step == "files":
            self._confirm_files()
        elif self.step == "plex_wait":
            self._start_pin()
        elif self.step == "plex_pick":
            self._confirm_server()
        elif self.step == "clock":
            self._confirm_clock()

    def _confirm_choice(self):
        self.notice = ""
        if self.index == 0:
            self.step = "files"
            self.choices = []
            self.prompt = messages.FILES_PROMPT
            self._render()
            return
        self._start_pin()

    def _confirm_files(self):
        mount_library()
        channels = find_library()
        if not channels:
            self.notice = messages.NO_VIDEOS
            self._render()
            return
        self.pending = {"source": "files", "channels": channels}
        self._show_clock()

    def _start_pin(self):
        link = PlexLink(client_id(self.app_dir))
        try:
            self.pin_id, self.pin_code = link.create_pin()
        except PlexLinkError as exc:
            self.notice = _link_message(exc.code)
            self._show_choose()
            return
        self.account_token = None
        self.step = "plex_wait"
        self.choices = []
        self.prompt = messages.PLEX_PROMPT
        self.notice = messages.PLEX_WAIT
        self._render()
        self.poll_timer.start()

    def _poll_pin(self):
        if self.step != "plex_wait" or self.pin_id is None:
            return
        link = PlexLink(client_id(self.app_dir))
        try:
            token = link.poll_pin(self.pin_id)
        except PlexLinkError as exc:
            self.poll_timer.stop()
            if exc.code == "expired":
                self.notice = messages.PLEX_CODE_EXPIRED
                self.prompt = messages.PLEX_CODE_EXPIRED
                self._render()
                return
            self.notice = _link_message(exc.code)
            self._show_choose()
            return
        if not token:
            return
        self.poll_timer.stop()
        self.account_token = token
        try:
            self.servers = link.list_servers(token)
        except PlexLinkError as exc:
            self.notice = _link_message(exc.code)
            self._show_choose()
            return
        if not self.servers:
            self.notice = messages.PLEX_NO_SERVER
            self._show_choose()
            return
        if len(self.servers) == 1:
            self._use_server(self.servers[0])
            return
        self.step = "plex_pick"
        self.index = 0
        self.notice = ""
        self.prompt = messages.PICK_SERVER
        self.choices = [server["name"] for server in self.servers]
        self._render()

    def _confirm_server(self):
        if not self.servers:
            return
        self._use_server(self.servers[self.index])

    def _use_server(self, server):
        self.pending = {
            "source": "plex",
            "server_url": server["server_url"],
            "token": server["token"],
        }
        self._show_clock()

    def _show_clock(self):
        self.step = "clock"
        self.index = 0
        self.notice = ""
        self.prompt = messages.PICK_CLOCK
        self.choices = [label for label, _zone in messages.CLOCKS]
        self._render()

    def _confirm_clock(self):
        _label, zone = messages.CLOCKS[self.index]
        apply_timezone(zone)
        pending = self.pending or {}
        if pending.get("source") == "files":
            save_files_station(self.app_dir, pending["channels"], zone)
        elif pending.get("source") == "plex":
            save_plex_station(self.app_dir, pending["server_url"], pending["token"], zone)
        else:
            return
        self.completed = True
        self.detach()
        self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.move_up()
        elif event.key() == Qt.Key.Key_Down:
            self.move_down()
        elif event.key() in _select_keys():
            self.confirm()
        elif event.key() == Qt.Key.Key_Escape:
            self.detach()
            self.reject()
        else:
            super().keyPressEvent(event)

    def reject(self):
        self.detach()
        super().reject()


def _select_keys():
    keys = {Qt.Key.Key_Return, Qt.Key.Key_Enter}
    select_key = getattr(Qt.Key, "Key_Select", None)
    if select_key is not None:
        keys.add(select_key)
    return keys


def _link_message(code):
    if code == "network":
        return messages.PLEX_NETWORK
    if code == "expired":
        return messages.PLEX_CODE_EXPIRED
    return messages.PLEX_BAD_RESPONSE
