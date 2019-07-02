import requests


def _check_resp(resp: requests.Response) -> None:
    if not (200 <= resp.status_code < 300):
        raise Exception(f"{resp.status_code} {resp.reason}: {resp.text}")
    if resp.status_code != 204:  # HTTP 204 No Content if everything is ok
        assert "application/json" in resp.headers["content-type"], resp.headers[
            "content-type"
        ]
