from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict


TickCallback = Callable[[], Dict[str, Any]]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SimulationRunner:
    """Runs simulated telemetry generation in a small background thread."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._interval_seconds = 4.5
        self._ticks = 0
        self._started_at: str | None = None
        self._stopped_at: str | None = None
        self._last_tick_at: str | None = None
        self._last_error: str | None = None
        self._last_result_summary: Dict[str, Any] | None = None
        self._latest_result: Dict[str, Any] | None = None

    def start(self, tick_callback: TickCallback, interval_seconds: float = 4.5) -> Dict[str, Any]:
        interval_seconds = max(1.0, float(interval_seconds))
        with self._lock:
            if self._thread and self._thread.is_alive():
                self._interval_seconds = interval_seconds
                return self.status()

            self._stop_event.clear()
            self._interval_seconds = interval_seconds
            self._started_at = _utc_now_iso()
            self._stopped_at = None
            self._last_error = None
            self._thread = threading.Thread(
                target=self._run,
                args=(tick_callback,),
                name="iomt-simulation-runner",
                daemon=True,
            )
            self._thread.start()
            return self.status()

    def stop(self) -> Dict[str, Any]:
        with self._lock:
            self._stop_event.set()
            thread = self._thread

        if thread and thread.is_alive():
            thread.join(timeout=3)

        with self._lock:
            self._stopped_at = _utc_now_iso()
            return self.status()

    def status(self) -> Dict[str, Any]:
        thread = self._thread
        return {
            "running": bool(thread and thread.is_alive() and not self._stop_event.is_set()),
            "interval_seconds": self._interval_seconds,
            "ticks": self._ticks,
            "started_at": self._started_at,
            "stopped_at": self._stopped_at,
            "last_tick_at": self._last_tick_at,
            "last_error": self._last_error,
            "last_result": self._last_result_summary,
        }

    def latest(self) -> Dict[str, Any] | None:
        with self._lock:
            return self._latest_result

    def _run(self, tick_callback: TickCallback) -> None:
        while not self._stop_event.is_set():
            try:
                result = tick_callback()
                summary = self._summarize_result(result)
                with self._lock:
                    self._ticks += 1
                    self._last_tick_at = _utc_now_iso()
                    self._last_error = None
                    self._last_result_summary = summary
                    self._latest_result = result
            except Exception as exc:  # pragma: no cover - defensive background safety
                with self._lock:
                    self._last_error = str(exc)
                    self._last_tick_at = _utc_now_iso()

            self._stop_event.wait(self._interval_seconds)

    @staticmethod
    def _summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
        event = result.get("event") or {}
        analysis = result.get("analysis") or {}
        alert = analysis.get("alert") or {}
        attack = analysis.get("attack_prediction") or {}
        decision = analysis.get("decision") or {}
        state_update = result.get("state_update") or {}
        return {
            "device_id": event.get("device_id"),
            "device_type": event.get("device_type"),
            "priority": alert.get("priority"),
            "attack_label": attack.get("predicted_label"),
            "action": decision.get("action"),
            "state": state_update.get("state"),
            "skipped": bool(result.get("skipped")),
            "message": result.get("message"),
        }
