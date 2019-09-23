import pytest

from kongcli.kong import consumers, plugins


def test_list_empty(invoke, clean_kong):
    result = invoke(["--font", "cyberlarge", "consumers", "list"])

    assert result.exit_code == 0
    assert (
        result.output
        == """\
 _______  _____  __   _ _______ _     _ _______ _______  ______ _______
 |       |     | | \  | |______ |     | |  |  | |______ |_____/ |______
 |_____  |_____| |  \_| ______| |_____| |  |  | |______ |    \_ ______|
                                                                       \n\n\n"""
    )


def test_list_single_empty(invoke, sample):
    service, route, consumer = sample
    result = invoke(["--font", "cyberlarge", "--tablefmt", "psql", "consumers", "list"])

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 11
    assert [v.strip() for v in lines[6].split("|")] == [
        "",
        "id",
        "custom_id",
        "username",
        "acl_groups",
        "plugins",
        "basic_auth",
        "key_auth",
        "",
    ]
    assert [v.strip() for v in lines[8].split("|")] == [
        "",
        consumer["id"],
        consumer["custom_id"],
        consumer["username"],
        "",
        "",
        "",
        "",
        "",
    ]


@pytest.mark.parametrize("full_keys", [[], ["--full-keys"]])
def test_list_single_filled(invoke, sample, session, full_keys):
    service, route, consumer = sample
    consumers.add_group(session, consumer["id"], "group2")
    consumers.add_group(session, consumer["id"], "group1")
    consumers.add_basic_auth(session, consumer["id"], "username", "passwd")
    consumers.add_key_auth(session, consumer["id"], "key-abcdefg")
    consumers.add_key_auth(session, consumer["id"], "key-hijklmn")

    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "consumers", "list"] + full_keys
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 12
    assert [v.strip() for v in lines[6].split("|")] == [
        "",
        "id",
        "custom_id",
        "username",
        "acl_groups",
        "plugins",
        "basic_auth",
        "key_auth",
        "",
    ]
    assert [v.strip() for v in lines[8].split("|")] == [
        "",
        consumer["id"],
        consumer["custom_id"],
        consumer["username"],
        "group1",
        "",
        "username:xxx",
        "key-abcdefg" if full_keys else "key-ab...",
        "",
    ]
    assert [v.strip() for v in lines[9].split("|")] == [
        "",
        "",
        "",
        "",
        "group2",
        "",
        "",
        "key-hijklmn" if full_keys else "key-hi...",
        "",
    ]


@pytest.mark.parametrize("full_plugins", [[], ["--full-plugins"]])
def test_list_single_plugins(invoke, sample, session, full_plugins):
    service, route, consumer = sample
    plugins.enable_on(
        session, "consumers", consumer["id"], "rate-limiting", config={"minute": 20}
    )
    plugins.enable_on(
        session, "routes", route["id"], "rate-limiting", config={"minute": 25}
    )

    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "consumers", "list"]
        + full_plugins
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 28 if full_plugins else 11
    assert [v.strip() for v in lines[6].split("|")] == [
        "",
        "id",
        "custom_id",
        "username",
        "acl_groups",
        "plugins",
        "basic_auth",
        "key_auth",
        "",
    ]
    assert [v.strip() for v in lines[8].split("|")] == [
        "",
        consumer["id"],
        consumer["custom_id"],
        consumer["username"],
        "",
        "rate-limiting:" if full_plugins else "rate-limiting",
        "",
        "",
        "",
    ]
    if full_plugins:
        rest = [line.split("|")[5].strip() for line in lines[9:26]]
        assert rest[0] == "{"
        assert rest[6] == '"minute": 20,'
        assert rest[-1] == "}"
