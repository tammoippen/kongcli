import json
import re


def test_info(invoke):
    result = invoke(["info"])
    assert result.exit_code == 0
    assert re.match(r"[01]\.\d+(\.\d+)?", json.loads(result.output)["version"])
