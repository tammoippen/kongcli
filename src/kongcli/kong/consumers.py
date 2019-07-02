from typing import Any, Dict, List, Optional

from loguru import logger
import requests

from ._util import _check_resp


def _consumer_get(
    session: requests.Session, id_: str, kind: str
) -> List[Dict[str, Any]]:
    logger.debug(f"Get `{kind}` of consumer with id = `{id_}` ... ")
    # TODO: paginate?
    resp = session.get(f"/consumers/{id_}/{kind}")
    _check_resp(resp)
    data: List[Dict[str, Any]] = resp.json().get("data", [])
    return data


def _consumer_delete(
    session: requests.Session, consumer_id: str, resource: str, resource_id: str
) -> None:
    logger.debug(
        f"Delete {resource} `{resource_id}` from consumer with id = `{consumer_id}` ... "
    )
    resp = session.delete(f"/consumers/{consumer_id}/{resource}/{resource_id}")
    _check_resp(resp)


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
    _consumer_delete(session, id_, "acls", group)


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


def consumer_delete_basic_auth(
    session: requests.Session, consumer_id: str, basic_auth_id: str
) -> None:
    _consumer_delete(session, consumer_id, "basic-auth", basic_auth_id)


# key auth
def consumer_key_auths(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "key-auth")


def consumer_add_key_auth(
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


def consumer_update_key_auth(
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


def consumer_delete_key_auth(
    session: requests.Session, consumer_id: str, key_auth_id: str
) -> None:
    _consumer_delete(session, consumer_id, "key-auth", key_auth_id)


# plugins
def consumer_plugins(session: requests.Session, id_: str) -> List[Dict[str, Any]]:
    return _consumer_get(session, id_, "plugins")