"""Original application artwork and explicit Windows identity, independent of game assets."""
from pathlib import Path
import sys

APP_ID='MasterRallye.VehicleSDK.RallyWorkshop'
ICON=Path(__file__).resolve().parents[3]/'assets/workshop/rally-workshop.ico'

def taskbar_identity():
    if sys.platform=='win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

def apply_icon(window):
    if sys.platform=='win32' and ICON.is_file():window.iconbitmap(str(ICON))
