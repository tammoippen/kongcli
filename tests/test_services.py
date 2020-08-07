def test_list_empty(invoke, clean_kong):
    result = invoke(["--font", "cyberlarge", "services", "list"])

    assert result.exit_code == 0
    assert (
        result.output
        == """\
 _______ _______  ______ _    _ _____ _______ _______
 |______ |______ |_____/  \  /    |   |       |______
 ______| |______ |    \_   \/   __|__ |_____  |______
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
