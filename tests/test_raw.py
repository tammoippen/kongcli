import json
from os import environ


def test_raw_info(invoke, clean_kong):
    result = invoke(["raw", "GET", "/"])
    assert result.exit_code == 0
    assert result.output.startswith("> GET http://localhost:8001/\n")
    lines = result.output.split("\n")

    for line in reversed(lines):
        if not line:
            continue
        if line:
            # last non-empty line is a json
            assert json.loads(line)["version"].startswith(
                environ.get("KONG_VERSION_TAG", "0.13")
            )
            break


def test_raw_single_data(invoke, clean_kong):
    result = invoke(["raw", "-d", "custom_id", "foobar", "POST", "/consumers"])
    assert result.exit_code == 0
    assert result.output.startswith("> POST http://localhost:8001/consumers\n")
    lines = result.output.split("\n")

    for line in reversed(lines):
        if not line:
            continue
        if line:
            # last non-empty line is a json
            data = json.loads(line)
            assert data["custom_id"] == "foobar"
            assert "username" not in data
            break


def test_raw_multiple_data(invoke, clean_kong):
    result = invoke(
        [
            "raw",
            "-d",
            "custom_id",
            "foobar",
            "-d",
            "username",
            "barfoo",
            "POST",
            "/consumers",
        ]
    )
    assert result.exit_code == 0
    assert result.output.startswith("> POST http://localhost:8001/consumers\n")
    lines = result.output.split("\n")

    for line in reversed(lines):
        if not line:
            continue
        if line:
            # last non-empty line is a json
            data = json.loads(line)
            assert data["custom_id"] == "foobar"
            assert data["username"] == "barfoo"
            break


def test_raw_single_header(invoke, clean_kong):
    result = invoke(["raw", "-H", "X-Custom-Header", "foobar", "GET", "/"])
    assert result.exit_code == 0
    assert result.output.startswith("> GET http://localhost:8001/\n")
    lines = result.output.split("\n")

    assert any(line == "> X-Custom-Header: foobar" for line in lines)


def test_raw_multiple_header(invoke, clean_kong):
    result = invoke(
        [
            "raw",
            "-H",
            "X-Custom-Header",
            "foobar",
            "-H",
            "X-Custom-Header2",
            "barfoo",
            "GET",
            "/",
        ]
    )
    assert result.exit_code == 0
    assert result.output.startswith("> GET http://localhost:8001/\n")
    lines = result.output.split("\n")

    assert any(line == "> X-Custom-Header: foobar" for line in lines)
    assert any(line == "> X-Custom-Header2: barfoo" for line in lines)
