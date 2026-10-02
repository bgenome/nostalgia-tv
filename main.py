import sys
import os
from PyQt6.QtWidgets import QApplication
from src.config.parser import ConfigParser
from src.engine.scheduler import Scheduler
from src.ui.main_window import MainWindow

from src.remote.listener import CecListener

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'data', 'channels.yaml')
    
    parser = ConfigParser(config_path)
    try:
        parser.load()
    except FileNotFoundError:
        print(f"Warning: Config not found at {config_path}. Starting with empty channels.")
        
    scheduler = Scheduler(parser.get_all_channels())
    
    app = QApplication(sys.argv)
    
    # Hide cursor for kiosk mode
    app.setOverrideCursor(Qt.CursorShape.BlankCursor) if hasattr(Qt, 'CursorShape') else None
    
    window = MainWindow(parser, scheduler)
    
    # Start CEC Listener and connect signals
    cec_listener = CecListener()
    cec_listener.ch_up_pressed.connect(window.channel_up)
    cec_listener.up_pressed.connect(window.channel_up)
    cec_listener.ch_down_pressed.connect(window.channel_down)
    cec_listener.down_pressed.connect(window.channel_down)
    cec_listener.start()
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    from PyQt6.QtCore import Qt
    main()
