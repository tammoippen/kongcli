from typing import Any, Dict

from loguru import logger
import requests

from ._util import _check_resp


def schema(session: requests.Session, plugin_name: str) -> Dict[str, Any]:
    logger.debug(f"Plugin schema for `{plugin_name}`.")
    resp = session.get(f"/plugins/schema/{plugin_name}")
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data
