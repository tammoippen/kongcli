import pytest

from kongcli.kong.plugins import enable_on, schema


def test_schema(session, kong_version):
    resp = schema(session, "basic-auth")
    assert len(resp["fields"]) == 2
    if kong_version >= 0.15:
        assert {k for f in resp["fields"] for k in f.keys()} == {
            "hide_credentials",
            "anonymous",
        }
    else:
        assert resp["fields"].keys() == {"hide_credentials", "anonymous"}


def test_schema_unknown(session):
    with pytest.raises(Exception) as e:
        schema(session, "basic-auths")

    assert (
        str(e.value).strip()
        == '404 Not Found: {"message":"No plugin named \'basic-auths\'"}'
    )


@pytest.mark.parametrize("resource", ("consumers", "services", "routes"))
def test_enable_on(resource, session, sample, kong_version):
    service, route, consumer = sample
    mapping = {"consumers": consumer, "services": service, "routes": route}

    plugin = enable_on(
        session,
        resource,
        mapping[resource]["id"],
        "rate-limiting",
        config={"second": 5},
    )
    assert plugin["name"] == "rate-limiting"
    assert plugin["enabled"] is True
    assert plugin["config"]["second"] == 5
    if kong_version >= 0.15:
        assert plugin[resource[:-1]]["id"] == mapping[resource]["id"]
    else:
        assert plugin[f"{resource[:-1]}_id"] == mapping[resource]["id"]
