from typing import Any, Dict, List, Optional

_THREADS: Dict[str, Dict[str, Any]] = {}


def save_thread(thread_id: str, snapshot: Dict[str, Any]) -> None:
    _THREADS[thread_id] = snapshot


def get_thread(thread_id: str) -> Optional[Dict[str, Any]]:
    return _THREADS.get(thread_id)


def clear_threads() -> None:
    _THREADS.clear()
