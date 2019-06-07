from functools import lru_cache
from typing import Any, Dict, List

import requests
from urllib3.util import parse_url


@lru_cache()
def information(url: str, apikey: str) -> Dict[str, Any]:
    resp = requests.get(url, headers={"apikey": apikey})
    resp.raise_for_status()
    assert "application/json" in resp.headers["content-type"], resp.headers[
        "content-type"
    ]
    data: Dict[str, Any] = resp.json()
    return data


@lru_cache()
def all_of(resource: str, url: str, apikey: str) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    next_ = f"/{resource}"
    headers = {"apikey": apikey}
    while next_:
        u = parse_url(next_)
        next_ = u.request_uri
        resp = requests.get(f"{url}{next_}", headers=headers)
        resp.raise_for_status()
        assert "application/json" in resp.headers["Content-Type"]
        jresp = resp.json()
        data += jresp["data"]
        next_ = jresp.get("next")
    return data
