import shutil
import subprocess
import threading

from PyQt6.QtCore import QObject, pyqtSignal

from src.remote.keys import action_for_cec_line

try:
    import cec as cec_module
except ImportError:
    cec_module = None


class CecListener(QObject):
    up_pressed = pyqtSignal()
    down_pressed = pyqtSignal()
    left_pressed = pyqtSignal()
    right_pressed = pyqtSignal()
    select_pressed = pyqtSignal()
    back_pressed = pyqtSignal()
    ch_up_pressed = pyqtSignal()
    ch_down_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = False
        self.thread = None
        self._process = None

    def start(self):
        if cec_module is not None:
            try:
                cec_module.init()
                self.running = True
                cec_module.add_callback(self._on_key_press, cec_module.EVENT_KEYPRESS)
                print("CEC listener started successfully.")
                return
            except Exception as exc:
                print(f"Error initializing CEC: {exc}")
        if shutil.which("cec-client"):
            self.running = True
            self.thread = threading.Thread(target=self._read_cec_client, daemon=True)
            self.thread.start()
            print("CEC listener started with cec-client.")
            return
        print("Warning: python-cec not installed. CEC remote control disabled.")

    def stop(self):
        self.running = False
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()

    def _emit_action(self, action):
        if action == "up":
            self.up_pressed.emit()
        elif action == "down":
            self.down_pressed.emit()
        elif action == "left":
            self.left_pressed.emit()
        elif action == "right":
            self.right_pressed.emit()
        elif action == "select":
            self.select_pressed.emit()
        elif action == "back":
            self.back_pressed.emit()
        elif action == "ch_up":
            self.ch_up_pressed.emit()
        elif action == "ch_down":
            self.ch_down_pressed.emit()

    def _on_key_press(self, event, *args):
        if cec_module is None:
            return
        keycode = event
        if keycode == cec_module.CEC_USER_CONTROL_CODE_UP:
            self.up_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_DOWN:
            self.down_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_LEFT:
            self.left_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_RIGHT:
            self.right_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_SELECT:
            self.select_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_EXIT or keycode == cec_module.CEC_USER_CONTROL_CODE_RETURN:
            self.back_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_CHANNEL_UP:
            self.ch_up_pressed.emit()
        elif keycode == cec_module.CEC_USER_CONTROL_CODE_CHANNEL_DOWN:
            self.ch_down_pressed.emit()

    def _read_cec_client(self):
        try:
            self._process = subprocess.Popen(
                ["cec-client", "-d", "1"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except OSError as exc:
            print(f"Error starting cec-client: {exc}")
            return
        stream = self._process.stdout
        if stream is None:
            return
        for line in stream:
            if not self.running:
                break
            self._emit_action(action_for_cec_line(line))
