from typing import Any

from loguru import logger
from requests import Response, Session


class LiveServerSession(Session):
    def __init__(self, prefix_url: str) -> None:
        super(LiveServerSession, self).__init__()
        while prefix_url.endswith("/"):
            prefix_url = prefix_url[:-1]
        logger.debug(f"Will use `{prefix_url}` as prefix for every request.")
        self.prefix_url = prefix_url

    def request(self, method: str, url: str, *args: Any, **kwargs: Any) -> Response:
        url = f"{self.prefix_url}{url}"
        return super(LiveServerSession, self).request(method, url, *args, **kwargs)
