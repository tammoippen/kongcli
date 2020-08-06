from datetime import datetime
from uuid import UUID

import pytest

from kongcli._util import parse_datetimes
from kongcli.kong import consumers, general, plugins


def test_list_empty(invoke, clean_kong):
    result = invoke(["--font", "cyberlarge", "consumers", "list"])

    assert result.exit_code == 0
    assert (
        result.output
        == """\
 _______  _____  __   _ _______ _     _ _______ _______  ______ _______
 |       |     | | \\  | |______ |     | |  |  | |______ |_____/ |______
 |_____  |_____| |  \\_| ______| |_____| |  |  | |______ |    \\_ ______|
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
def test_list_two_filled(invoke, sample, session, full_keys):
    service, route, consumer1 = sample
    consumer2 = general.add("consumers", session, username="foobar2", custom_id="4321")
    parse_datetimes(consumer2)

    for idx, consumer in enumerate((consumer1, consumer2)):
        consumers.add_group(session, consumer["id"], "group2")
        consumers.add_group(session, consumer["id"], "group1")
        consumers.add_basic_auth(session, consumer["id"], f"username{idx}", "passwd")
        consumers.add_key_auth(session, consumer["id"], f"key-abcdefg{idx}")
        consumers.add_key_auth(session, consumer["id"], f"key-hijklmn{idx}")

    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "consumers", "list"] + full_keys
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 14
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
    for idx, consumer in enumerate((consumer1, consumer2)):
        assert [v.strip() for v in lines[8 + idx * 2].split("|")] == [
            "",
            consumer["id"],
            consumer["custom_id"],
            consumer["username"],
            "group1",
            "",
            f"username{idx}:xxx",
            f"key-abcdefg{idx}" if full_keys else "key-ab...",
            "",
        ]
        assert [v.strip() for v in lines[9 + idx * 2].split("|")] == [
            "",
            "",
            "",
            "",
            "group2",
            "",
            "",
            f"key-hijklmn{idx}" if full_keys else "key-hi...",
            "",
        ]


@pytest.mark.parametrize("full_plugins", [[], ["--full-plugins"]])
def test_list_two_plugins(invoke, sample, session, full_plugins):
    service, route, consumer1 = sample
    consumer2 = general.add("consumers", session, username="foobar2", custom_id="4321")
    for consumer in (consumer1, consumer2):
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
    assert len(lines) >= 32 if full_plugins else 11
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
        consumer1["id"],
        consumer1["custom_id"],
        consumer1["username"],
        "",
        "rate-limiting:" if full_plugins else "rate-limiting",
        "",
        "",
        "",
    ]
    if full_plugins:
        rest = [[elem.strip() for elem in line.split("|")] for line in lines[9:]]
        second_id_line = [
            idx
            for idx, line in enumerate(rest)
            if len(line) >= 2 and line[1] == consumer2["id"]
        ][0]
        assert any(line[5] == '"minute": 20,' for line in rest[:second_id_line])

        assert rest[second_id_line] == [
            "",
            consumer2["id"],
            consumer2["custom_id"],
            consumer2["username"],
            "",
            "rate-limiting:",
            "",
            "",
            "",
        ]
        assert any(line[5] == '"minute": 20,' for line in rest[second_id_line:])

    else:
        assert [v.strip() for v in lines[9].split("|")] == [
            "",
            consumer2["id"],
            consumer2["custom_id"],
            consumer2["username"],
            "",
            "rate-limiting",
            "",
            "",
            "",
        ]


def test_create_no_required(invoke, clean_kong):
    result = invoke(["consumers", "create"])
    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert (
        result.stderr
        == "You must set either `--username` or `--custom_id` with the request.\nAborted!\n"
    )


@pytest.mark.parametrize(
    "username,custom", [("xyz", "1234"), (None, "1234"), ("xyz", None)]
)
def test_create(invoke, clean_kong, username, custom):
    extra = []
    if username:
        extra += ["--username", username]
    if custom:
        extra += ["--custom_id", custom]
    result = invoke(
        ["--font", "cyberlarge", "--tablefmt", "psql", "consumers", "create"] + extra
    )
    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 6
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "created_at",
        "custom_id",
        "id",
        "tags",
        "username",
        "",
    ]
    values = [v.strip() for v in lines[3].split("|")]
    assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
    assert values[2] == "" if custom is None else custom
    assert UUID(values[3])
    assert values[4] == ""
    assert values[5] == "" if username is None else username


def test_update_empty(invoke, clean_kong, sample):
    service, route, consumer = sample

    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "update",
            consumer["id"],
        ]
    )
    assert result.exit_code == 1
    assert (
        result.stderr
        == "You must set either `--username` or `--custom_id` with the request.\nAborted!\n"
    )
    assert isinstance(result.exception, SystemExit)


@pytest.mark.parametrize(
    "username,custom", [("xyz", "4321"), (None, "4321"), ("xyz", None)]
)
def test_update(invoke, clean_kong, username, custom, sample):
    service, route, consumer = sample
    extra = []
    if username:
        extra += ["--username", username]
    if custom:
        extra += ["--custom_id", custom]
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "update",
            consumer["id"],
        ]
        + extra
    )
    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 6
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "created_at",
        "custom_id",
        "id",
        "tags",
        "username",
        "",
    ]
    values = [v.strip() for v in lines[3].split("|")]
    assert values[2] == consumer["custom_id"] if custom is None else custom
    assert UUID(values[3])
    assert values[4] == ""
    assert values[5] == consumer["username"] if username is None else username


@pytest.mark.parametrize("acls", (True, False))
@pytest.mark.parametrize("ba", (True, False))
@pytest.mark.parametrize("ka", (True, False))
@pytest.mark.parametrize("pl", (True, False))
def test_retrive(invoke, sample, session, acls, ba, ka, pl):
    service, route, consumer = sample
    consumers.add_group(session, consumer["id"], "group2")
    consumers.add_group(session, consumer["id"], "group1")
    consumers.add_basic_auth(session, consumer["id"], "username", "passwd")
    consumers.add_key_auth(session, consumer["id"], "key-abcdefg")
    consumers.add_key_auth(session, consumer["id"], "key-hijklmn")
    plugins.enable_on(
        session, "consumers", consumer["id"], "rate-limiting", config={"minute": 20}
    )
    plugins.enable_on(
        session, "routes", route["id"], "rate-limiting", config={"minute": 25}
    )

    extra = []
    if acls:
        extra += ["--acls"]
    if ba:
        extra += ["--basic-auths"]
    if ka:
        extra += ["--key-auths"]
    if pl:
        extra += ["--plugins"]

    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "retrieve",
            consumer["id"],
        ]
        + extra
    )
    assert result.exit_code == 0
    values = [
        [v.strip() for v in line.split("|")] for line in result.output.split("\n")
    ]
    assert values[1][:6] == ["", "created_at", "custom_id", "id", "tags", "username"]
    rest = values[1][6:]
    if acls:
        assert rest.pop(0) == "acls"
    if ba:
        assert rest.pop(0) == "basic_auth"
    if ka:
        assert rest.pop(0) == "key_auth"
    if pl:
        assert rest.pop(0) == "plugins"

    assert values[3][:6] == [
        "",
        consumer["created_at"].isoformat(),
        consumer["custom_id"],
        consumer["id"],
        "",
        consumer["username"],
    ]

    incr = 0
    if acls:
        values[3][6 + incr] == "group1"
        values[4][6 + incr] == "group2"
        incr += 1
    if ba:
        values[3][6 + incr] == "username:xxx"
        incr += 1
    if ka:
        values[3][6 + incr] == "key-abcdefg"
        values[4][6 + incr] == "key-hijklmn"
        incr += 1
    if pl:
        values[3][6 + incr] == "request-limit:"
        values[4][6 + incr] == "{"
        incr += 1


def test_add_groups_none(invoke, sample):
    service, route, consumer = sample
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "add-groups",
            consumer["id"],
        ]
    )
    assert result.exit_code == 0
    assert result.output == ""


def test_add_groups_multiple(invoke, sample):
    service, route, consumer = sample
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "add-groups",
            consumer["id"],
            "group2",
            "group1",
        ]
    )
    assert result.exit_code == 0
    values = [
        [v.strip() for v in line.split("|")] for line in result.output.split("\n")
    ]
    assert values[1] == [
        "",
        "created_at",
        "custom_id",
        "id",
        "tags",
        "username",
        "acls",
        "",
    ]
    assert values[3] == [
        "",
        consumer["created_at"].isoformat(),
        consumer["custom_id"],
        consumer["id"],
        "",
        consumer["username"],
        "group1",
        "",
    ]
    assert values[4] == ["", "", "", "", "", "", "group2", ""]


def test_delete_groups_none(invoke, sample):
    service, route, consumer = sample
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "delete-groups",
            consumer["id"],
        ]
    )
    assert result.exit_code == 0
    assert result.output == ""


def test_delete_groups_multiple(invoke, sample, session):
    service, route, consumer = sample
    consumers.add_group(session, consumer["id"], "group2")
    consumers.add_group(session, consumer["id"], "group1")
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "delete-groups",
            consumer["id"],
            "group2",
            "group1",
        ]
    )
    assert result.exit_code == 0
    values = [
        [v.strip() for v in line.split("|")] for line in result.output.split("\n")
    ]
    assert values[1] == [
        "",
        "created_at",
        "custom_id",
        "id",
        "tags",
        "username",
        "acls",
        "",
    ]
    assert values[3] == [
        "",
        consumer["created_at"].isoformat(),
        consumer["custom_id"],
        consumer["id"],
        "",
        consumer["username"],
        "",
        "",
    ]


def test_delete(invoke, sample, session):
    service, route, consumer = sample
    result = invoke(["consumers", "delete", consumer["id"]])
    assert result.exit_code == 0
    assert result.output == f"Deleted consumer `{consumer['id']}`!\n"

    with pytest.raises(Exception) as e:
        general.retrieve("consumers", session, consumer["id"])

    assert str(e.value).strip() == '404 Not Found: {"message":"Not found"}'


def test_key_auth_lists_none(invoke, sample):
    service, route, consumer = sample
    result = invoke(["consumers", "key-auth", "list", consumer["id"]])

    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_key_auth_lists_some(invoke, sample, session):
    service, route, consumer = sample
    keys = []
    for _i in range(5):
        keys.append(consumers.add_key_auth(session, consumer["id"]))
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "key-auth",
            "list",
            consumer["id"],
        ]
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 10
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "consumer.id",
        "created_at",
        "id",
        "key",
        "",
    ]
    for line in lines[3:8]:
        values = [v.strip() for v in line.split("|")][1:-1]
        assert values[0] == consumer["id"]
        assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
        id_ = values[2]
        key = next(k for k in keys if k["id"] == id_)
        assert key["key"] == values[3]


def test_key_auth_add(invoke, sample, session):
    service, route, consumer = sample
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "key-auth",
            "add",
            consumer["id"],
        ]
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 6
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "consumer.id",
        "created_at",
        "id",
        "key",
        "",
    ]
    values = [v.strip() for v in lines[3].split("|")][1:-1]
    assert values[0] == consumer["id"]
    assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
    id_ = values[2]
    keys = consumers.key_auths(session, consumer["id"])
    key = next(k for k in keys if k["id"] == id_)
    assert values[3] == key["key"]


def test_key_auth_delete(invoke, sample, session):
    service, route, consumer = sample
    key = consumers.add_key_auth(session, consumer["id"])
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "key-auth",
            "delete",
            consumer["id"],
            key["id"],
        ]
    )

    assert result.exit_code == 0
    assert (
        result.output == f"Deleted key `{key['id']}` of consumer `{consumer['id']}`!\n"
    )
    keys = consumers.key_auths(session, consumer["id"])
    assert keys == []


def test_key_auth_update(invoke, sample, session):
    service, route, consumer = sample
    key = consumers.add_key_auth(session, consumer["id"])
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "key-auth",
            "update",
            consumer["id"],
            key["id"],
            "key-12345",
        ]
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 6
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "consumer.id",
        "created_at",
        "id",
        "key",
        "",
    ]
    values = [v.strip() for v in lines[3].split("|")][1:-1]
    assert values[0] == consumer["id"]
    assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
    id_ = values[2]
    keys = consumers.key_auths(session, consumer["id"])
    key = next(k for k in keys if k["id"] == id_)
    assert values[3] == key["key"]
    assert values[3] == "key-12345"


def test_basic_auth_lists_none(invoke, sample):
    service, route, consumer = sample
    result = invoke(["consumers", "basic-auth", "list", consumer["id"]])

    assert result.exit_code == 0
    assert result.output.strip() == ""


def test_basic_auth_lists_some(invoke, sample, session):
    service, route, consumer = sample
    bas = []
    for i in range(5):
        bas.append(
            consumers.add_basic_auth(session, consumer["id"], f"user{i}", "passwd")
        )
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "basic-auth",
            "list",
            consumer["id"],
        ]
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 10
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "consumer.id",
        "created_at",
        "id",
        "password",
        "username",
        "",
    ]
    for line in lines[3:8]:
        values = [v.strip() for v in line.split("|")][1:-1]
        assert values[0] == consumer["id"]
        assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
        id_ = values[2]
        ba = next(k for k in bas if k["id"] == id_)
        assert ba["password"] == values[3]
        assert ba["username"] == values[4]


def test_basic_auth_add(invoke, sample, session):
    service, route, consumer = sample
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "basic-auth",
            "add",
            consumer["id"],
            "--username",
            "user",
            "--password",
            "passwd",
        ]
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 6
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "consumer.id",
        "created_at",
        "id",
        "password",
        "username",
        "",
    ]
    values = [v.strip() for v in lines[3].split("|")][1:-1]
    assert values[0] == consumer["id"]
    assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
    id_ = values[2]
    bas = consumers.basic_auths(session, consumer["id"])
    ba = next(k for k in bas if k["id"] == id_)
    assert ba["password"] == values[3]
    assert ba["username"] == values[4]


def test_basic_auth_delete(invoke, sample, session):
    service, route, consumer = sample
    ba = consumers.add_basic_auth(session, consumer["id"], "user", "passwd")
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "basic-auth",
            "delete",
            consumer["id"],
            ba["id"],
        ]
    )

    assert result.exit_code == 0
    assert (
        result.output
        == f"Deleted credentials `{ba['id']}` of consumer `{consumer['id']}`!\n"
    )
    bas = consumers.basic_auths(session, consumer["id"])
    assert bas == []


@pytest.mark.parametrize(
    "username,passwd", [("xyz", "4321"), (None, "4321"), ("xyz", None)]
)
def test_basic_auth_update(invoke, sample, session, username, passwd):
    service, route, consumer = sample
    ba = consumers.add_basic_auth(session, consumer["id"], "user", "passwd")
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "basic-auth",
            "update",
            consumer["id"],
            ba["id"],
            "--username",
            username,
            "--password",
            passwd,
        ]
    )

    assert result.exit_code == 0
    lines = result.output.split("\n")
    assert len(lines) == 6
    assert [v.strip() for v in lines[1].split("|")] == [
        "",
        "consumer.id",
        "created_at",
        "id",
        "password",
        "username",
        "",
    ]
    values = [v.strip() for v in lines[3].split("|")][1:-1]
    assert values[0] == consumer["id"]
    assert datetime.strptime(values[1], "%Y-%m-%dT%H:%M:%S+00:00") <= datetime.now()
    id_ = values[2]
    bas = consumers.basic_auths(session, consumer["id"])
    ba = next(k for k in bas if k["id"] == id_)
    assert ba["password"] == values[3]
    assert ba["password"] == passwd or "passwd"
    assert ba["username"] == values[4]
    assert ba["username"] == username or "user"


def test_basic_auth_update_no_data(invoke, sample, session):
    service, route, consumer = sample
    ba = consumers.add_basic_auth(session, consumer["id"], "user", "passwd")
    result = invoke(
        [
            "--font",
            "cyberlarge",
            "--tablefmt",
            "psql",
            "consumers",
            "basic-auth",
            "update",
            consumer["id"],
            ba["id"],
        ]
    )

    assert result.exit_code == 1
    assert isinstance(result.exception, SystemExit)
    assert (
        result.stderr
        == "You must set either `--username` or `--password` with the request.\nAborted!\n"
    )
