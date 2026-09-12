"""Minimal JSON persistence: one file, one lock. Nothing else.

ponytail: single JSON file with a process lock; swap for SQLite only if two
workers ever share the state (the demo runs one uvicorn process).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "state.json"
_LOCK = threading.Lock()
_EMPTY = {"sales": {}, "verdicts": {}, "confirmations": {}, "events": [], "alerts_done": []}


def load() -> dict:
    if not STATE_PATH.exists():
        return json.loads(json.dumps(_EMPTY))
    with STATE_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    for key, default in _EMPTY.items():
        data.setdefault(key, json.loads(json.dumps(default)))
    return data


def save(data: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(STATE_PATH)


def update(fn):
    """Apply fn(data) under the lock and persist. Returns fn's result."""
    with _LOCK:
        data = load()
        result = fn(data)
        save(data)
        return result
