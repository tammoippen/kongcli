import json
from typing import Any, Dict, List

from loguru import logger
import requests
from urllib3.util import parse_url


def information(session: requests.Session) -> Dict[str, Any]:
    logger.debug("Collecting information about kong ...")
    resp = session.get("/")
    resp.raise_for_status()
    assert "application/json" in resp.headers["content-type"], resp.headers[
        "content-type"
    ]
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
        resp.raise_for_status()
        assert "application/json" in resp.headers["Content-Type"]
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
    headers = {"content-type": "application/json"}
    logger.debug(f"Add `{resource}` with `{json.dumps(kwargs)}` ... ")
    resp = session.post(f"/{resource}/", headers=headers, json=kwargs)
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
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
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
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
    resp.raise_for_status()  # HTTP 204 No Content if everything is ok


# consumer specific
def _consumer_get(
    session: requests.Session, id_: str, kind: str
) -> List[Dict[str, Any]]:
    logger.debug(f"Get `{kind}` of consumer with id = `{id_}` ... ")
    # TODO: paginate?
    resp = session.get(f"/consumers/{id_}/{kind}")
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
    data: List[Dict[str, Any]] = resp.json().get("data", [])
    return data


# ACLS / groups
def consumer_acls(session: requests.Session, id_: str) -> List[str]:
    data = _consumer_get(session, id_, "acls")
    return [acl["group"] for acl in data]


def consumer_add_group(
    session: requests.Session, id_: str, group: str
) -> Dict[str, Any]:
    headers = {"content-type": "application/json"}
    logger.debug(f"Add group `{group}` to consumer with id = `{id_}` ... ")
    resp = session.post(
        f"/consumers/{id_}/acls", headers=headers, json={"group": group}
    )
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
    data: Dict[str, Any] = resp.json()
    return data


def consumer_delete_group(session: requests.Session, id_: str, group: str) -> None:
    logger.debug(f"Delete group `{group}` from consumer with id = `{id_}` ... ")
    resp = session.delete(f"/consumers/{id_}/acls/{group}")
    resp.raise_for_status()  # HTTP 204 No Content if everything is ok


# basic auth
def consumer_basic_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "basic-auth")


# key auth
def consumer_key_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "key-auth")


# plugins
def consumer_plugins(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "plugins")
