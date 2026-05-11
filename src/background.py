import threading
from collections.abc import Callable

_lock = threading.Lock()
_active_thread: threading.Thread | None = None
_stop_event = threading.Event()


def is_background_running() -> bool:
  return _active_thread is not None and _active_thread.is_alive()


def prevent_duplicate_instance() -> bool:
  """이미 백그라운드 작업이 실행 중이면 True 반환."""
  return is_background_running()


def start_background_task(target: Callable, *args, **kwargs) -> bool:
  """백그라운드 스레드를 시작한다. 이미 실행 중이면 False 반환."""
  global _active_thread

  with _lock:
    if is_background_running():
      return False
    _stop_event.clear()
    _active_thread = threading.Thread(
      target=_guarded(target),
      args=args,
      kwargs=kwargs,
      daemon=True,
    )
    _active_thread.start()
    return True


def stop_background_task() -> None:
  _stop_event.set()


def get_stop_event() -> threading.Event:
  """모니터링 루프가 종료 신호를 확인하는 데 사용하는 Event 반환."""
  return _stop_event


def _guarded(target: Callable) -> Callable:
  def wrapper(*args, **kwargs):
    try:
      target(*args, **kwargs)
    except Exception:
      pass
  return wrapper
