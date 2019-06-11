from functools import lru_cache
import json
from typing import Any, Dict, List

from loguru import logger
import requests
from urllib3.util import parse_url


@lru_cache()
def information(url: str, apikey: str) -> Dict[str, Any]:
    logger.debug("Collecting information about kong ...")
    resp = requests.get(url, headers={"apikey": apikey})
    resp.raise_for_status()
    assert "application/json" in resp.headers["content-type"], resp.headers[
        "content-type"
    ]
    data: Dict[str, Any] = resp.json()
    return data


@lru_cache()
def all_of(resource: str, url: str, apikey: str) -> List[Dict[str, Any]]:
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
    headers = {"apikey": apikey}
    while next_:
        resp = requests.get(f"{url}{next_}", headers=headers)
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


def add(resource: str, url: str, apikey: str, **kwargs: Any) -> Dict[str, Any]:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "acls",
        "key-auths",
        "basic-auths",
    )
    headers = {"apikey": apikey, "content-type": "application/json"}
    logger.debug(f"Add `{resource}` with `{json.dumps(kwargs)}` ... ")
    resp = requests.post(f"{url}/{resource}/", headers=headers, json=kwargs)
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
    return resp.json()


def retrieve(resource: str, url: str, apikey: str, id_: str) -> Dict[str, Any]:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "key-auths",
        "basic-auths",
    )
    headers = {"apikey": apikey}
    logger.debug(f"Retrieve `{resource}` with id = `{id_}` ... ")
    resp = requests.get(f"{url}/{resource}/{id_}", headers=headers)
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
    return resp.json()


def delete(resource: str, url: str, apikey: str, id_: str) -> None:
    assert resource in (
        "consumers",
        "services",
        "routes",
        "plugins",
        "key-auths",
        "basic-auths",
    )
    headers = {"apikey": apikey}
    logger.debug(f"Delete `{resource}` with id = `{id_}` ... ")
    resp = requests.delete(f"{url}/{resource}/{id_}", headers=headers)
    resp.raise_for_status()  # HTTP 204 No Content if everything is ok


# consumer specific

def consumer_acls(url: str, apikey: str, id_: str) -> List[str]:
    headers = {"apikey": apikey}
    logger.debug(f"Get acls of consumer with id = `{id_}` ... ")
    # TODO: paginate?
    resp = requests.get(f'{url}/consumers/{id_}/acls', headers=headers)
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
    data = resp.json()
    return [acl['group'] for acl in data.get('data', [])]


def consumer_add_group(url: str, apikey: str, id_: str, group: str) -> None:
    headers = {"apikey": apikey, 'content-type': 'application/json'}
    logger.debug(f"Add group `{group}` to consumer with id = `{id_}` ... ")
    resp = requests.post(f'{url}/consumers/{id_}/acls', headers=headers, json={'group': group})
    resp.raise_for_status()
    assert "application/json" in resp.headers["Content-Type"]
    return resp.json()


def consumer_delete_group(url: str, apikey: str, id_: str, group: str) -> None:
    headers = {"apikey": apikey}
    logger.debug(f"Delete group `{group}` from consumer with id = `{id_}` ... ")
    resp = requests.delete(f'{url}/consumers/{id_}/acls/{group}', headers=headers)
    resp.raise_for_status()  # HTTP 204 No Content if everything is ok
