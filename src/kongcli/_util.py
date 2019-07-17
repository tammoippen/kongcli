from datetime import datetime, timezone
import json
from typing import Any, Callable, Dict, Sequence, Tuple

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


def dict_from_dot(data: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
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

        assert (
            key_parts[-1] not in curr
        ), f"The key `{key}` is previously assigned to something else."
        curr[key_parts[-1]] = value

    return result


def parse_datetimes(obj: Dict[str, Any]) -> None:
    try:
        if "created_at" in obj:
            obj["created_at"] = datetime.fromtimestamp(obj["created_at"], timezone.utc)

        if "updated_at" in obj:
            obj["updated_at"] = datetime.fromtimestamp(obj["updated_at"], timezone.utc)
    except ValueError:
        if "created_at" in obj:
            obj["created_at"] = datetime.fromtimestamp(
                obj["created_at"] / 1000, timezone.utc
            )

        if "updated_at" in obj:
            obj["updated_at"] = datetime.fromtimestamp(
                obj["updated_at"] / 1000, timezone.utc
            )
