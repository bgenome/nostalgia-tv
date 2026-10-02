import threading
from PyQt6.QtCore import QObject, pyqtSignal

class CecListener(QObject):
    # Define Qt signals for remote events
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
        
    def start(self):
        try:
            import cec
            cec.init()
            self.running = True
            cec.add_callback(self._on_key_press, cec.EVENT_KEYPRESS)
            print("CEC listener started successfully.")
        except ImportError:
            print("Warning: python-cec not installed. CEC remote control disabled.")
        except Exception as e:
            print(f"Error initializing CEC: {e}")
            
    def stop(self):
        self.running = False
        
    def _on_key_press(self, event, *args):
        # event should contain the keycode
        # Keycodes are defined in cec module (e.g. cec.CEC_USER_CONTROL_CODE_UP)
        import cec
        keycode = event
        
        if keycode == cec.CEC_USER_CONTROL_CODE_UP:
            self.up_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_DOWN:
            self.down_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_LEFT:
            self.left_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_RIGHT:
            self.right_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_SELECT:
            self.select_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_EXIT or keycode == cec.CEC_USER_CONTROL_CODE_RETURN:
            self.back_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_CHANNEL_UP:
            self.ch_up_pressed.emit()
        elif keycode == cec.CEC_USER_CONTROL_CODE_CHANNEL_DOWN:
            self.ch_down_pressed.emit()
