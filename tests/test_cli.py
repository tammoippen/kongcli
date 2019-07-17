import json
from os import environ


def test_info(invoke):
    result = invoke(["info"])
    assert result.exit_code == 0
    assert json.loads(result.output)["version"].startswith(
        environ.get("KONG_VERSION_TAG", "0.13")
    )
