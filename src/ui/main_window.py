import sys
import locale
import os
import mpv
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer

# Ensure correct locale for mpv
locale.setlocale(locale.LC_NUMERIC, 'C')

class MpvWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        
        # Initialize mpv
        self.player = mpv.MPV(
            wid=str(int(self.winId())),
            log_handler=print,
            loglevel='error',
            hwdec='auto',
            profile='gpu-hq',
            vo='gpu'
        )
        
        # Apply CRT Shader
        shader_path = os.path.join(os.path.dirname(__file__), "..", "..", "shaders", "crt-easymode.glsl")
        if os.path.exists(shader_path):
            self.player.glsl_shaders = shader_path
            
    def play(self, filepath, seek_time=0):
        if filepath == "OFF_AIR":
            self.player.stop()
            # Draw static or off-air image
            return
            
        if filepath == "GUIDE":
            self.player.stop()
            return
            
        self.player.play(filepath)
        
        # For simplicity, wait until playing then seek
        try:
            self.player.wait_until_playing()
            if seek_time > 0:
                self.player.seek(seek_time, reference='absolute')
        except Exception as e:
            print(f"Error seeking: {e}")
            
class MainWindow(QMainWindow):
    def __init__(self, config_parser, scheduler):
        super().__init__()
        self.config = config_parser
        self.scheduler = scheduler
        self.current_channel = 2 # Default starting channel
        
        self.setWindowTitle("Nostalgia TV")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        self.setStyleSheet("background-color: black; color: white;")
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_widget = MpvWidget(self)
        self.layout.addWidget(self.video_widget)
        
        # Overlay for channel info
        self.overlay = QLabel(self.central_widget)
        self.overlay.setStyleSheet("font-size: 48px; font-weight: bold; color: #00FF00; font-family: monospace; background-color: rgba(0, 0, 0, 150); padding: 10px;")
        self.overlay.setGeometry(50, 50, 500, 120)
        self.overlay.hide()
        
        self.overlay_timer = QTimer()
        self.overlay_timer.timeout.connect(self.overlay.hide)
        
        self.switch_channel(self.current_channel)
        
    def switch_channel(self, channel_num):
        if channel_num not in self.config.get_all_channels():
            self.show_overlay(f"CH {channel_num}\n(Static)")
            self.video_widget.play("OFF_AIR")
            return
            
        self.current_channel = channel_num
        channel_info = self.config.get_channel(channel_num)
        
        self.show_overlay(f"CH {channel_num}\n{channel_info.name}")
        
        filepath, seek_time = self.scheduler.get_currently_playing(channel_num)
        if filepath:
            print(f"Playing {filepath} at {seek_time}s")
            self.video_widget.play(filepath, seek_time)
            
    def show_overlay(self, text):
        self.overlay.setText(text)
        self.overlay.show()
        self.overlay.raise_()
        self.overlay_timer.start(3000) # Hide after 3 seconds
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            self.channel_up()
        elif event.key() == Qt.Key.Key_Down:
            self.channel_down()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
            
    def channel_up(self):
        channels = sorted(list(self.config.get_all_channels().keys()))
        if not channels: return
        try:
            idx = channels.index(self.current_channel)
            next_ch = channels[(idx + 1) % len(channels)]
        except ValueError:
            next_ch = channels[0]
        self.switch_channel(next_ch)
        
    def channel_down(self):
        channels = sorted(list(self.config.get_all_channels().keys()))
        if not channels: return
        try:
            idx = channels.index(self.current_channel)
            prev_ch = channels[(idx - 1) % len(channels)]
        except ValueError:
            prev_ch = channels[-1]
        self.switch_channel(prev_ch)
