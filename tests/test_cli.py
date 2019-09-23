import json
import re
from uuid import uuid4


def test_info(invoke):
    result = invoke(["info"])
    assert result.exit_code == 0
    assert re.match(r"[01]\.\d+(\.\d+)?", json.loads(result.output)["version"])


def test_version(invoke):
    result = invoke(["version"])
    assert result.exit_code == 0
    assert re.match(r"^kongcli v\d+\.\d+.\d+$", result.output.strip())


def test_logging_debug(invoke):
    # debug at -vvv
    for vs in ([], ["-v"], ["-vv"]):
        result = invoke(vs + ["info"])
        assert result.exit_code == 0
        assert result.stderr_bytes == b""
    result = invoke(["-vvv", "info"])
    assert result.exit_code == 0
    assert b" | DEBUG    | " in result.stderr_bytes


def test_logging_info(invoke):
    # info at -vv
    for vs in ([], ["-v"]):
        result = invoke(vs + ["routes", "update", str(uuid4())])
        assert isinstance(result.exception, Exception)
        assert result.stderr_bytes == b""
    result = invoke(["-vv", "routes", "update", str(uuid4())])
    assert isinstance(result.exception, Exception)
    assert b" | INFO     | " in result.stderr_bytes


def test_info_apikey(invoke):
    ctx = {}
    result = invoke(["--apikey", "xxx", "info"], obj=ctx)
    assert result.exit_code == 0
    assert ctx["session"].headers["apikey"] == "xxx"
    # with env
    ctx = {}
    result = invoke(["info"], obj=ctx, env={"KONG_APIKEY": "xxx"})
    assert result.exit_code == 0
    assert ctx["session"].headers["apikey"] == "xxx"


def test_info_simple_auth(invoke):
    ctx = {}
    result = invoke(["--basic", "user", "--passwd", "xxx", "info"], obj=ctx)
    assert result.exit_code == 0
    assert ctx["session"].auth == ("user", "xxx")
    # with env
    ctx = {}
    result = invoke(
        ["info"], obj=ctx, env={"KONG_BASIC_USER": "user", "KONG_BASIC_PASSWD": "xxx"}
    )
    assert result.exit_code == 0
    assert ctx["session"].auth == ("user", "xxx")
    # with prompt
    ctx = {}
    result = invoke(["info"], obj=ctx, env={"KONG_BASIC_USER": "user"}, input="xxx\n")
    assert result.exit_code == 0
    assert ctx["session"].auth == ("user", "xxx")


def test_list_cmd(invoke, clean_kong):
    result = invoke(["--font", "cyberlarge", "list", "consumers"])
    assert result.output == """\
 _______  _____  __   _ _______ _     _ _______ _______  ______ _______
 |       |     | | \  | |______ |     | |  |  | |______ |_____/ |______
 |_____  |_____| |  \_| ______| |_____| |  |  | |______ |    \_ ______|
                                                                       \n\n\n"""
