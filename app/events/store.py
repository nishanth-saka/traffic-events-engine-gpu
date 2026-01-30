from typing import List
from app.events.schema import TrafficEvent
import threading


class InMemoryEventStore:
    """
    Simple in-memory event store for MVP.

    - Thread-safe
    - Process-local
    - NOT persistent (by design)
    """

    def __init__(self):
        self._events: List[TrafficEvent] = []
        self._lock = threading.Lock()

    def add(self, event: TrafficEvent):
        with self._lock:
            self._events.append(event)

    def all(self) -> List[TrafficEvent]:
        with self._lock:
            return list(self._events)

    def clear(self):
        with self._lock:
            self._events.clear()


# 🔑 Canonical store instance (what routes import)
EVENT_STORE = InMemoryEventStore()
