"""Cancellable, per-session post-match callback coordinator."""
from __future__ import annotations

import threading
from collections.abc import Callable


class PostMatchCoordinator:
    """Keep one timer per post-match phase and reject stale callbacks."""

    def __init__(self, timer_factory=None):
        self._lock = threading.RLock()
        self._timer_factory = timer_factory or threading.Timer
        self._generation = 0
        self._timers: dict[str, threading.Timer] = {}

    def begin(self) -> int:
        """Start a new match-end cycle, invalidating every callback before it."""
        with self._lock:
            self._generation += 1
            self._cancel_all_locked()
            return self._generation

    def invalidate(self) -> int:
        """Invalidate current callbacks, for Stop, new session, or new match."""
        return self.begin()

    def current(self, generation: int) -> bool:
        with self._lock:
            return generation == self._generation

    def schedule(
        self, generation: int, key: str, delay: float, callback: Callable[[], None]
    ) -> bool:
        with self._lock:
            if generation != self._generation:
                return False
            old = self._timers.pop(key, None)
            if old is not None:
                old.cancel()

            timer = self._timer_factory(
                max(0.0, float(delay)),
                lambda: self._fire(generation, key, timer, callback),
            )
            timer.daemon = True
            self._timers[key] = timer
            timer.start()
            return True

    def cancel(self, key: str) -> None:
        with self._lock:
            timer = self._timers.pop(key, None)
            if timer is not None:
                timer.cancel()

    def _fire(self, generation: int, key: str, timer, callback) -> None:
        with self._lock:
            if generation != self._generation or self._timers.get(key) is not timer:
                return
            self._timers.pop(key, None)
        callback()

    def _cancel_all_locked(self) -> None:
        timers, self._timers = self._timers, {}
        for timer in timers.values():
            timer.cancel()
