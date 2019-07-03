from typing import Any, Callable

from cachetools import LRUCache


CACHE = None


def get(key: str, fkt: Callable[[], Any]) -> Any:
    global CACHE
    if CACHE is None:
        CACHE = LRUCache(maxsize=32)
    if key not in CACHE:
        CACHE[key] = fkt()
    return CACHE[key]
