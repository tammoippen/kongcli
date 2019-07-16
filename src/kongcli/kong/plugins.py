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


def enable_on(
    session: requests.Session, resource: str, id_: str, plugin_name: str, **kwargs: Any
) -> Dict[str, Any]:
    assert resource in ("services", "routes", "consumers")
    logger.debug(f"Enable plugin {plugin_name} on {resource}.")
    kwargs["name"] = plugin_name
    resp = session.post(f"/{resource}/{id_}/plugins", json=kwargs)
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data
