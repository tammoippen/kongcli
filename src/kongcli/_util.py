import json
from typing import Any, Callable, Dict, Tuple

from cachetools import LRUCache
from loguru import logger

CACHE = None


def get(key: str, fkt: Callable[[], Any]) -> Any:
    global CACHE
    if CACHE is None:
        CACHE = LRUCache(maxsize=32)
    if key not in CACHE:
        CACHE[key] = fkt()
    return CACHE[key]


def dict_from_dot(data: Tuple[Tuple[str, str], ...]) -> Dict[str, Any]:
    result = {}
    for k, v in data:
        key_parts = k.split(".")
        curr = result
        for key in key_parts[:-1]:
            if key not in result:
                curr[key] = {}
            curr = curr[key]
            assert isinstance(
                curr, dict
            ), f"The key `{key}` is previously assigned to something else than a dict."
        value = v
        try:
            value = json.loads(v)
        except json.JSONDecodeError:
            logger.info(f"Cannot parse `{v}` to json, assuming string.")
            pass
        curr[key_parts[-1]] = value

    return result