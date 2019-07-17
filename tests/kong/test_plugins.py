import pytest

from kongcli.kong.plugins import enable_on, schema


def test_schema(session):
    resp = schema(session, "basic-auth")
    assert isinstance(resp, dict)
    assert resp == {
        "no_consumer": True,
        "fields": {
            "hide_credentials": {"default": False, "type": "boolean"},
            "anonymous": {"default": "", "func": "function", "type": "string"},
        },
    }


def test_schema_unknown(session):
    with pytest.raises(Exception) as e:
        schema(session, "basic-auths")

    assert (
        str(e.value).strip()
        == '404 Not Found: {"message":"No plugin named \'basic-auths\'"}'
    )


@pytest.mark.parametrize("resource", ("consumers", "services", "routes"))
def test_enable_on(resource, session, sample):
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
    assert plugin[f"{resource[:-1]}_id"] == mapping[resource]["id"]
