import logging
import threading
import time
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DebouncedScanHandler(FileSystemEventHandler):
    def __init__(self, scan: Callable[[], None], debounce_seconds: float = 1.0) -> None:
        self.scan = scan
        self.debounce_seconds = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        self._scan_lock = threading.Lock()

    def _run_scan(self) -> None:
        if not self._scan_lock.acquire(blocking=False):
            logging.getLogger("ai_file_manager").info("Scan already running; a later filesystem event will retry.")
            return
        try:
            self.scan()
        except Exception:
            logging.getLogger("ai_file_manager").exception("Watcher-triggered scan failed")
        finally:
            self._scan_lock.release()

    def on_any_event(self, event) -> None:
        if event.is_directory and event.event_type == "modified":
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self.debounce_seconds, self._run_scan)
            self._timer.daemon = True
            self._timer.start()

    def close(self) -> None:
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()


def watch(knowledge_root: Path, scan: Callable[[], None], debounce_seconds: float = 1.0) -> None:
    knowledge_root.mkdir(parents=True, exist_ok=True)
    handler = DebouncedScanHandler(scan, debounce_seconds)
    observer = Observer()
    observer.schedule(handler, str(knowledge_root), recursive=True)
    observer.start()
    logging.getLogger("ai_file_manager").info("Watching %s. Press Ctrl+C to stop.", knowledge_root)
    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        pass
    finally:
        handler.close()
        observer.stop()
        observer.join()


def schedule(scan: Callable[[], None], interval_seconds: float) -> None:
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than zero")
    try:
        while True:
            scan()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        return
