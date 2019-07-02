import json
from typing import Any, Dict, List, Optional

from loguru import logger
import requests
from urllib3.util import parse_url


def _check_resp(resp: requests.Response) -> None:
    if not (200 <= resp.status_code < 300):
        raise Exception(f"{resp.status_code} {resp.reason}: {resp.text}")
    if resp.status_code != 204:  # HTTP 204 No Content if everything is ok
        assert "application/json" in resp.headers["content-type"], resp.headers[
            "content-type"
        ]


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


# consumer specific
def _consumer_get(
    session: requests.Session, id_: str, kind: str
) -> List[Dict[str, Any]]:
    logger.debug(f"Get `{kind}` of consumer with id = `{id_}` ... ")
    # TODO: paginate?
    resp = session.get(f"/consumers/{id_}/{kind}")
    _check_resp(resp)
    data: List[Dict[str, Any]] = resp.json().get("data", [])
    return data


# ACLS / groups
def consumer_groups(session: requests.Session, id_: str) -> List[str]:
    data = _consumer_get(session, id_, "acls")
    return [acl["group"] for acl in data]


def consumer_add_group(
    session: requests.Session, id_: str, group: str
) -> Dict[str, Any]:
    logger.debug(f"Add group `{group}` to consumer with id = `{id_}` ... ")
    resp = session.post(f"/consumers/{id_}/acls", json={"group": group})
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def consumer_delete_group(session: requests.Session, id_: str, group: str) -> None:
    logger.debug(f"Delete group `{group}` from consumer with id = `{id_}` ... ")
    resp = session.delete(f"/consumers/{id_}/acls/{group}")
    _check_resp(resp)


# basic auth
def consumer_basic_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "basic-auth")


def consumer_add_basic_auth(
    session: requests.Session, id_: str, username: str, password: str
) -> Dict[str, Any]:
    logger.debug(f"Add basic auth `{username}:xxx` to consumer with id = `{id_}` ... ")
    resp = session.post(
        f"/consumers/{id_}/basic-auth",
        json={"username": username, "password": password},
    )
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def consumer_update_basic_auth(
    session: requests.Session,
    consumer_id: str,
    basic_auth_id: str,
    username: Optional[str],
    password: Optional[str],
) -> Dict[str, Any]:
    logger.debug(
        f"Update basic auth `{consumer_id}` from consumer with id = `{consumer_id}` ... "
    )
    payload = {}
    if username:
        payload["username"] = username
    if password:
        payload["password"] = password
    assert payload, "Need at least one, username or password, for update."
    resp = session.patch(
        f"/consumers/{consumer_id}/basic-auth/{basic_auth_id}", json=payload
    )
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def consumer_delete_basic_auth(
    session: requests.Session, consumer_id: str, basic_auth_id: str
) -> None:
    logger.debug(
        f"Delete basic auth `{basic_auth_id}` from consumer with id = `{consumer_id}` ... "
    )
    resp = session.delete(f"/consumers/{consumer_id}/basic-auth/{basic_auth_id}")
    _check_resp(resp)


# key auth
def consumer_key_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "key-auth")


# plugins
def consumer_plugins(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "plugins")
