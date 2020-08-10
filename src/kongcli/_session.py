from typing import Any

from requests import Response, Session


class LiveServerSession(Session):
    def __init__(self, prefix_url: str) -> None:
        super(LiveServerSession, self).__init__()
        while prefix_url.endswith("/"):
            prefix_url = prefix_url[:-1]
        self.prefix_url = prefix_url

    def request(  # type: ignore
        self, method: str, url: str, *args: Any, **kwargs: Any
    ) -> Response:
        url = f"{self.prefix_url}{url}"
        return super(LiveServerSession, self).request(method, url, *args, **kwargs)
