import pytest

from kongcli._util import parse_datetimes
from kongcli.kong import general


def test_list_empty(invoke, clean_kong):
    result = invoke(["--font", "cyberlarge", "services", "list"])

    assert result.exit_code == 0
    assert (
        result.output
        == """\
 _______ _______  ______ _    _ _____ _______ _______
 |______ |______ |_____/  \\  /    |   |       |______
 ______| |______ |    \\_   \\/   __|__ |_____  |______
                                                     \n\n\n"""
    )


def test_list_single_empty(invoke, sample):
    service, route, consumer = sample
    result = invoke(["--font", "cyberlarge", "--tablefmt", "psql", "services", "list"])

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 11
    assert [v.strip() for v in lines[6].split("|")] == [
        "",
        "service_id",
        "name",
        "protocol",
        "host",
        "port",
        "path",
        "whitelist",
        "blacklist",
        "plugins",
        "",
    ]
    assert [v.strip() for v in lines[8].split("|")] == [
        "",
        service["id"],
        service["name"],
        service["protocol"],
        service["host"],
        str(service["port"]),
        "",
        "",
        "",
        "",
        "",
    ]


@pytest.mark.parametrize("full_plugins", [[], ["--full-plugins"]])
def test_list_two_filled(invoke, sample, session, full_plugins, httpbin):
    service1, route, consumer = sample
    service2 = general.add("services", session, name="httpbin2", url=httpbin)
    parse_datetimes(service2)

    res = invoke(["services", "enable-acl", "--deny", "bar", service1["id"]])
    assert res.exit_code == 0, res.output
    res = invoke(["services", "enable-acl", "--allow", "foo", service2["id"]])
    assert res.exit_code == 0, res.output

    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "services", "list"]
        + full_plugins
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    rows = [[v.strip() for v in line.split("|")] for line in lines]

    assert len(lines) == 12
    assert rows[6] == [
        "",
        "service_id",
        "name",
        "protocol",
        "host",
        "port",
        "path",
        "whitelist",
        "blacklist",
        "plugins",
        "",
    ]
    for idx in range(2):
        row = rows[8 + idx]
        if row[2] == "httpbin":
            service = service1
        elif row[2] == "httpbin2":
            service = service2
        else:
            raise AssertionError(f"Expect service name in row: {row}")

        assert row == [
            "",
            service["id"],
            service["name"],
            service["protocol"],
            service["host"],
            str(service["port"]),
            "",
            "foo" if idx == 1 else "",
            "bar" if idx == 0 else "",
            "",
            "",
        ]


@pytest.mark.parametrize("full_plugins", [[], ["--full-plugins"]])
def test_list_two_plugins(invoke, sample, session, full_plugins, httpbin):
    service1, route, consumer = sample
    service2 = general.add("services", session, name="httpbin2", url=httpbin)
    parse_datetimes(service2)

    for service in (service1, service2):
        assert invoke(["services", "enable-key-auth", service["id"]]).exit_code == 0
        assert invoke(["services", "enable-basic-auth", service["id"]]).exit_code == 0

    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "services", "list"]
        + full_plugins
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert full_plugins or len(lines) == 14
    assert not full_plugins or len(lines) == 40
    rows = [[v.strip() for v in line.split("|")] for line in lines]
    assert rows[6] == [
        "",
        "service_id",
        "name",
        "protocol",
        "host",
        "port",
        "path",
        "whitelist",
        "blacklist",
        "plugins",
        "",
    ]
    second_id_line = [
        idx
        for idx, row in enumerate(rows[9:])
        if len(row) >= 2 and (row[1] == service1["id"] or row[1] == service2["id"])
    ][0]
    for idx in (8, 8 + second_id_line + 1):
        row = rows[idx]
        if row[2] == "httpbin":
            service = service1
        elif row[2] == "httpbin2":
            service = service2
        else:
            raise AssertionError(f"Expect service name in row: {row}")

        if not full_plugins:
            plugins = {"key-auth": None, "basic-auth": None}
            assert row[:-2] == [
                "",
                service["id"],
                service["name"],
                service["protocol"],
                service["host"],
                str(service["port"]),
                "",
                "",
                "",
            ]
            assert plugins.pop(row[-2]) is None
            row = rows[idx + 1]
            assert row[:-2] == [
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
            assert plugins.pop(row[-2]) is None
        else:
            plugins = {"key-auth:": None, "basic-auth:": None}
            assert row[:-2] == [
                "",
                service["id"],
                service["name"],
                service["protocol"],
                service["host"],
                str(service["port"]),
                "",
                "",
                "",
            ]
            assert plugins.pop(row[-2]) is None
            for j in range(1, second_id_line + 1):
                row = rows[idx + j]
                if row[-2] in plugins:
                    plugins.pop(row[-2])
                    break
            assert not plugins, f"Some plugin not found: {plugins}"


def test_add_no_required(invoke, clean_kong):
    result = invoke(["services", "add"])
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert (
        "If not using the shorthand-attribute `url`, at least `host` has to be set."
        in result.stderr
    )


@pytest.mark.parametrize("other", ["protocol", "host", "port", "path"])
def test_add_url_and_other(invoke, clean_kong, httpbin, other):
    result = invoke(["services", "add", "--url", httpbin, f"--{other}", "fooo"])
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert (
        "If using the shorthand-attribute `url` the other options `protocol`, `host`, `port` and `path` will be ignored."
        in result.stderr
    )


def test_add_url(invoke, clean_kong, httpbin_parsed, httpbin, now):
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "services",
            "add",
            "--url",
            httpbin,
        ]
    )
    assert result.exit_code == 0
    lines = [
        [elem.strip() for elem in line.split("|")] for line in result.stdout.split("\n")
    ]
    assert lines[1] == [
        "",
        "id",
        "name",
        "tags",
        "created_at",
        "updated_at",
        "protocol",
        "host",
        "port",
        "path",
        "retries",
        "connect_timeout",
        "read_timeout",
        "write_timeout",
        "",
    ]
    assert lines[3][4] >= now
    assert lines[3][5] >= now
    assert lines[3] == [
        "",
        lines[3][1],  # "id",
        "",
        "",
        lines[3][4],
        lines[3][5],
        httpbin_parsed.scheme,
        httpbin_parsed.hostname,
        str(httpbin_parsed.port),
        "",
        "5",
        "60000",
        "60000",
        "60000",
        "",
    ]
