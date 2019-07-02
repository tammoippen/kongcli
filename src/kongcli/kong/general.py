import json
from typing import Any, Dict, List

from loguru import logger
import requests
from urllib3.util import parse_url

from ._util import _check_resp


def information(session: requests.Session) -> Dict[str, Any]:
    logger.debug("Collecting information about kong ...")
    resp = session.get("/")
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def all_of(resource: str, session: requests.Session) -> List[Dict[str, Any]]:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "acls",
        "key-auths",
        "basic-auths",
    )
    logger.debug(f"Collecting all entries from `{resource}` ...")
    data: List[Dict[str, Any]] = []
    next_ = f"/{resource}"
    while next_:
        resp = session.get(f"{next_}")
        _check_resp(resp)
        jresp = resp.json()
        data += jresp["data"]
        next_ = jresp.get("next")
        if next_:
            u = parse_url(next_)
            next_ = u.request_uri
            logger.debug(f"... next page `{next_}`")
    return data


def add(resource: str, session: requests.Session, **kwargs: Any) -> Dict[str, Any]:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "acls",
        "key-auths",
        "basic-auths",
    )
    logger.debug(f"Add `{resource}` with `{json.dumps(kwargs)}` ... ")
    resp = session.post(f"/{resource}/", json=kwargs)
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def retrieve(resource: str, session: requests.Session, id_: str) -> Dict[str, Any]:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "key-auths",
        "basic-auths",
    )
    logger.debug(f"Retrieve `{resource}` with id = `{id_}` ... ")
    resp = session.get(f"/{resource}/{id_}")
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def delete(resource: str, session: requests.Session, id_: str) -> None:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "key-auths",
        "basic-auths",
    )
    logger.debug(f"Delete `{resource}` with id = `{id_}` ... ")
    resp = session.delete(f"/{resource}/{id_}")
    _check_resp(resp)


def update(
    resource: str, session: requests.Session, id_: str, **kwargs: Any
) -> Dict[str, Any]:
    assert resource in ("consumers", "services", "routes", "plugins")
    logger.debug(f"Update `{resource}` with id = `{id_}` ... ")
    resp = session.patch(f"/{resource}/{id_}", json=kwargs)
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data
