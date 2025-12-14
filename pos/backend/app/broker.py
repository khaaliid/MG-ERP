import threading
import time
from queue import Queue, Empty
from typing import Dict, Any, Callable

class Broker:
    def __init__(self):
        self.q: Queue[Dict[str, Any]] = Queue()
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()

    def publish_sale(self, sale_payload: Dict[str, Any]):
        self.q.put({"type": "sale", "payload": sale_payload})

    def start(self, handler: Callable[[Dict[str, Any]], None]):
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = threading.Thread(target=self._run, args=(handler,), daemon=True)
        self._worker.start()

    def stop(self):
        self._stop.set()
        if self._worker:
            self._worker.join(timeout=2)

    def _run(self, handler: Callable[[Dict[str, Any]], None]):
        while not self._stop.is_set():
            try:
                msg = self.q.get(timeout=0.5)
                try:
                    handler(msg)
                except Exception:
                    # simple retry
                    time.sleep(1.0)
                    self.q.put(msg)
            except Empty:
                continue
