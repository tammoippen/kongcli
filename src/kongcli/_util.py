from datetime import datetime, timezone
from typing import Any, Callable, Dict, Sequence, Tuple

from cachetools import LRUCache
from loguru import logger
import orjson

CACHE = None


def get(key: str, fkt: Callable[[], Any]) -> Any:
    global CACHE
    if CACHE is None:
        CACHE = LRUCache(maxsize=32)
    if key not in CACHE:
        CACHE[key] = fkt()
    return CACHE[key]


def _reset_cache() -> None:
    if CACHE is not None:
        CACHE.clear()


def dict_from_dot(data: Sequence[Tuple[str, str]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for k, v in data:
        key_parts = k.split(".")
        curr = result
        for key in key_parts[:-1]:
            if key not in curr:
                curr[key] = {}
            curr = curr[key]
            assert isinstance(
                curr, dict
            ), f"The key `{key}` is previously assigned to something else than a dict."

        value = v
        try:
            value = json_loads(v)
        except orjson.JSONDecodeError:
            logger.info(f"Cannot parse `{v}` to json, assuming string.")

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


def sort_dict(obj: Any) -> Any:
    return json_loads(json_dumps(obj))


def json_dumps(obj: Any) -> str:
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS).decode()


def json_pretty(obj: Any) -> str:
    return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS | orjson.OPT_INDENT_2).decode()


def json_loads(sobj: str) -> Any:
    return orjson.loads(sobj)


def substitude_ids(obj: Dict[str, Any]) -> None:
    for key in ("consumer", "route", "service"):
        if key in obj:
            # version 1. sets `consumer` to none, if not assigned to a consumer
            if obj[key] and "id" in obj[key]:
                obj[f"{key}.id"] = obj[key]["id"]
            obj.pop(key)
        elif f"{key}_id" in obj:
            obj[f"{key}.id"] = obj.pop(f"{key}_id")
