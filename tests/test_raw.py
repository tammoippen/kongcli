import json
import os
import re

import pytest


@pytest.mark.parametrize("env", (True, False))
def test_raw_info(invoke, clean_kong, env, kong_admin):
    if env:
        extra = []
    else:
        os.environ.pop("KONG_BASE", None)
        extra = ["--url", kong_admin]
    result = invoke(extra + ["raw", "GET", "/"], mix_stderr=False)
    assert result.exit_code == 0
    assert result.stderr.startswith(f"> GET {kong_admin}/\n")
    lines = result.stdout.split("\n")

    for line in reversed(lines):
        if not line:
            continue
        if line:
            # last non-empty line is a json
            assert re.match(r"[01]\.\d+(\.\d+)?", json.loads(line)["version"])
            break


def test_raw_single_data(invoke, clean_kong, kong_admin):
    result = invoke(
        ["raw", "-d", "custom_id", "foobar", "POST", "/consumers"], mix_stderr=False
    )
    assert result.exit_code == 0
    assert result.stderr.startswith(f"> POST {kong_admin}/consumers\n")
    lines = result.stdout.split("\n")

    for line in reversed(lines):
        if not line:
            continue
        if line:
            # last non-empty line is a json
            data = json.loads(line)
            assert data["custom_id"] == "foobar"
            assert data.get("username") is None
            break


def test_raw_multiple_data(invoke, clean_kong, kong_admin):
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
        ],
        mix_stderr=False,
    )
    assert result.exit_code == 0
    assert result.stderr.startswith(f"> POST {kong_admin}/consumers\n")
    lines = result.stdout.split("\n")

    for line in reversed(lines):
        if not line:
            continue
        if line:
            # last non-empty line is a json
            data = json.loads(line)
            assert data["custom_id"] == "foobar"
            assert data["username"] == "barfoo"
            break


def test_raw_single_header(invoke, clean_kong, kong_admin):
    result = invoke(
        ["raw", "-H", "X-Custom-Header", "foobar", "GET", "/"], mix_stderr=False
    )
    assert result.exit_code == 0
    assert result.stderr.startswith(f"> GET {kong_admin}/\n")
    lines = result.stderr.split("\n")

    assert any(line == "> X-Custom-Header: foobar" for line in lines)


def test_raw_multiple_header(invoke, clean_kong, kong_admin):
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
        ],
        mix_stderr=False,
    )
    assert result.exit_code == 0
    assert result.stderr.startswith(f"> GET {kong_admin}/\n")
    lines = result.stderr.split("\n")

    assert any(line == "> X-Custom-Header: foobar" for line in lines)
    assert any(line == "> X-Custom-Header2: barfoo" for line in lines)
