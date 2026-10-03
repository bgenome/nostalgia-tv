import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QLabel

from src.config.parser import ConfigParser
from src.engine.scheduler import Scheduler
from src.plex.client import PlexClient
from src.remote.listener import CecListener
from src.station import messages
from src.station.plex_lineup import PlexScheduler, build_plex_channels, write_plex_channel_names
from src.station.store import read_station, station_ready
from src.ui.main_window import MainWindow
from src.ui.setup_window import SetupWindow


def app_dir():
    return os.path.dirname(os.path.abspath(__file__))


def load_parser(root):
    config_path = os.path.join(root, "data", "channels.yaml")
    parser = ConfigParser(config_path)
    try:
        parser.load()
    except FileNotFoundError:
        print(f"Warning: Config not found at {config_path}. Starting with empty channels.")
    return parser


def prepare_playback(root):
    station = read_station(root)
    source = station.get("source")
    if source == "files":
        parser = load_parser(root)
        return parser, Scheduler(parser), ""
    if source == "plex":
        client = PlexClient()
        built = build_plex_channels(client)
        if not built:
            if client.get_libraries():
                return None, None, messages.EMPTY_LIBRARY
            return None, None, messages.PLEX_DOWN
        write_plex_channel_names(os.path.join(root, "data", "channels.yaml"), built)
        return load_parser(root), PlexScheduler(built), ""
    return None, None, ""


def _loading_label():
    label = QLabel(messages.LOADING)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setWindowState(Qt.WindowState.WindowFullScreen)
    label.setStyleSheet(
        "background-color: black; color: #00FF00; font-size: 48px; font-family: monospace;"
    )
    return label


def main():
    root = app_dir()
    app = QApplication(sys.argv)
    app.setOverrideCursor(Qt.CursorShape.BlankCursor)

    cec_listener = CecListener()
    cec_listener.start()

    notice = ""
    parser = None
    scheduler = None
    while parser is None or scheduler is None:
        if notice or not station_ready(root):
            setup = SetupWindow(root, cec_listener, notice)
            if setup.exec() != QDialog.DialogCode.Accepted:
                cec_listener.stop()
                sys.exit(0)
            setup.detach()
            notice = ""
        loading = _loading_label()
        loading.showFullScreen()
        app.processEvents()
        parser, scheduler, notice = prepare_playback(root)
        loading.close()

    window = MainWindow(parser, scheduler)
    cec_listener.ch_up_pressed.connect(window.channel_up)
    cec_listener.up_pressed.connect(window.channel_up)
    cec_listener.ch_down_pressed.connect(window.channel_down)
    cec_listener.down_pressed.connect(window.channel_down)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
