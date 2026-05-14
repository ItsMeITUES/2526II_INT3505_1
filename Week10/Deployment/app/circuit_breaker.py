"""
Circuit Breaker pattern — prevents cascading failures when a dependency is down.

States:
  CLOSED  → normal operation, calls pass through
  OPEN    → dependency is failing, calls fail fast
  HALF    → testing if dependency recovered (one probe call allowed)
"""

import time
import logging
import threading
from enum import Enum

logger = logging.getLogger('books_api.circuit_breaker')


class State(Enum):
    CLOSED = 'closed'
    OPEN   = 'open'
    HALF   = 'half_open'


class CircuitBreakerError(Exception):
    """Raised when the circuit is OPEN and calls are rejected."""


class CircuitBreaker:
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        success_threshold: int = 2,
        on_state_change=None,
    ):
        self.name              = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout  = recovery_timeout
        self.success_threshold = success_threshold
        self.on_state_change   = on_state_change

        self._state          = State.CLOSED
        self._failure_count  = 0
        self._success_count  = 0
        self._last_failure   = None
        self._lock           = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def call(self, func, *args, **kwargs):
        """Execute func through the circuit breaker."""
        with self._lock:
            self._maybe_attempt_reset()

            if self._state == State.OPEN:
                raise CircuitBreakerError(
                    f'Circuit [{self.name}] is OPEN — call rejected'
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except CircuitBreakerError:
            raise
        except Exception as exc:
            self._on_failure(exc)
            raise

    @property
    def is_open(self):
        return self._state == State.OPEN

    @property
    def state(self):
        return self._state.value

    # ── Internals ─────────────────────────────────────────────────────────────

    def _maybe_attempt_reset(self):
        if (
            self._state == State.OPEN
            and self._last_failure
            and time.monotonic() - self._last_failure >= self.recovery_timeout
        ):
            self._transition(State.HALF)

    def _on_success(self):
        with self._lock:
            if self._state == State.HALF:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._failure_count = 0
                    self._success_count = 0
                    self._transition(State.CLOSED)
            elif self._state == State.CLOSED:
                self._failure_count = 0

    def _on_failure(self, exc):
        with self._lock:
            self._last_failure = time.monotonic()
            self._success_count = 0

            if self._state == State.HALF:
                self._transition(State.OPEN)
            else:
                self._failure_count += 1
                logger.warning(
                    f'Circuit [{self.name}] failure {self._failure_count}/{self.failure_threshold}: {exc}'
                )
                if self._failure_count >= self.failure_threshold:
                    self._transition(State.OPEN)

    def _transition(self, new_state: State):
        old = self._state
        self._state = new_state
        logger.warning(f'Circuit [{self.name}] → {new_state.value.upper()}')
        if self.on_state_change and old != new_state:
            try:
                self.on_state_change(self.name, old.value, new_state.value)
            except Exception:
                pass
