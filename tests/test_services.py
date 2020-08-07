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

    assert (
        invoke(["services", "enable-acl", "--deny", "bar", service1["id"]]).exit_code
        == 0
    )
    assert (
        invoke(["services", "enable-acl", "--allow", "foo", service2["id"]]).exit_code
        == 0
    )

    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "services", "list"]
        + full_plugins
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 12
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
    for idx, service in enumerate((service1, service2)):
        assert [v.strip() for v in lines[8 + idx].split("|")] == [
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
