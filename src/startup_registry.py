import sys
import winreg

_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_APP_NAME = "BuildSense"


def _is_frozen() -> bool:
  return getattr(sys, "frozen", False)


def register_startup() -> None:
  if not _is_frozen():
    return
  try:
    exe_path = sys.executable
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
      winreg.SetValueEx(key, _APP_NAME, 0, winreg.REG_SZ, exe_path)
  except Exception:
    pass


def unregister_startup() -> None:
  try:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
      winreg.DeleteValue(key, _APP_NAME)
  except FileNotFoundError:
    pass
  except Exception:
    pass
