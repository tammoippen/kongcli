from typing import Any, Dict, List, Optional

from loguru import logger
import requests

from ._util import _check_resp
from .general import get_assoziated


def _delete(
    session: requests.Session, consumer_id: str, resource: str, resource_id: str
) -> None:
    logger.debug(
        f"Delete {resource} `{resource_id}` from consumer with id = `{consumer_id}` ... "
    )
    resp = session.delete(f"/consumers/{consumer_id}/{resource}/{resource_id}")
    _check_resp(resp)


# ACLS / groups
def groups(session: requests.Session, id_: str) -> List[str]:
    data = get_assoziated("consumers", session, id_, "acls")
    return [acl["group"] for acl in data]


def add_group(session: requests.Session, id_: str, group: str) -> Dict[str, Any]:
    logger.debug(f"Add group `{group}` to consumer with id = `{id_}` ... ")
    resp = session.post(f"/consumers/{id_}/acls", json={"group": group})
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def delete_group(session: requests.Session, id_: str, group: str) -> None:
    _delete(session, id_, "acls", group)


# basic auth
def basic_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return get_assoziated("consumers", session, id_, "basic-auth")


def add_basic_auth(
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


def update_basic_auth(
    session: requests.Session,
    consumer_id: str,
    basic_auth_id: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
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


def delete_basic_auth(
    session: requests.Session, consumer_id: str, basic_auth_id: str
) -> None:
    _delete(session, consumer_id, "basic-auth", basic_auth_id)


# key auth
def key_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return get_assoziated("consumers", session, id_, "key-auth")


def add_key_auth(
    session: requests.Session, id_: str, key: Optional[str] = None
) -> Dict[str, Any]:
    logger.debug(f"Add key auth to consumer with id = `{id_}` ... ")
    payload = None
    if key:
        payload = {"key": key}
    resp = session.post(f"/consumers/{id_}/key-auth", json=payload)
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def update_key_auth(
    session: requests.Session, consumer_id: str, key_auth_id: str, key: str
) -> Dict[str, Any]:
    logger.debug(
        f"Update key auth `{consumer_id}` from consumer with id = `{consumer_id}` ... "
    )
    payload = {"key": key}
    resp = session.patch(
        f"/consumers/{consumer_id}/key-auth/{key_auth_id}", json=payload
    )
    _check_resp(resp)
    data: Dict[str, Any] = resp.json()
    return data


def delete_key_auth(
    session: requests.Session, consumer_id: str, key_auth_id: str
) -> None:
    _delete(session, consumer_id, "key-auth", key_auth_id)


# plugins
def plugins(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return get_assoziated("consumers", session, id_, "plugins")
