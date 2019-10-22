import os
from typing import List

from click.testing import CliRunner
import psycopg2
from psycopg2.extras import DictCursor
import pytest

from kongcli._cli import cli
from kongcli._session import LiveServerSession
from kongcli._util import _reset_cache
from kongcli.kong.general import add, information


@pytest.fixture()
def invoke():
    runner = CliRunner(mix_stderr=False)

    def _invoke(args: List[str], **kwargs):
        return runner.invoke(cli, args, **kwargs)

    return _invoke


@pytest.fixture()
def kong_pg_host():
    return os.environ.get("KONG_PG_HOST", "localhost")


@pytest.fixture(autouse=True)
def kong_admin():
    host = os.environ.get("KONG_HOST", "localhost")
    port = os.environ.get("KONG_ADMIN_PORT", "8001")
    os.environ["KONG_BASE"] = f"http://{host}:{port}"
    yield os.environ["KONG_BASE"]
    os.environ.pop("KONG_BASE", None)


@pytest.fixture()
def kong_regular():
    host = os.environ.get("KONG_HOST", "localhost")
    port = os.environ.get("KONG_PORT", "8000")
    return f"http://{host}:{port}"


@pytest.fixture()
def httpbin():
    host = os.environ.get("HTTPBIN_HOST", "localhost")
    port = os.environ.get("HTTPBIN_PORT", "8080")
    return f"http://{host}:{port}"


@pytest.fixture()
def session(kong_admin):
    session = LiveServerSession(kong_admin)
    yield session
    session.close()


@pytest.fixture()
def clean_kong(kong_pg_host):
    _reset_cache()
    with psycopg2.connect(
        database=os.environ.get("KONG_PG_DATABASE", "kong"),
        user=os.environ.get("KONG_PG_USER", "kong"),
        password=os.environ.get("KONG_PG_PASSWORD", "kong"),
        host=kong_pg_host,
        cursor_factory=DictCursor,
    ) as conn, conn.cursor() as cursor:
        cursor.execute(
            """SELECT table_name
               FROM information_schema.tables
               WHERE table_schema = 'public' AND table_name <> 'schema_migrations';"""
        )
        tables = [row[0] for row in cursor.fetchall()]
        cursor.execute(f"TRUNCATE TABLE {', '.join(tables)} CASCADE;")


@pytest.fixture()
def kong_version(session):
    return float(".".join(information(session)["version"].split(".")[:2]))


@pytest.fixture()
def sample(clean_kong, session, httpbin):
    service = add("services", session, name="httpbin", url=httpbin)
    route = add("routes", session, service={"id": service["id"]}, paths=["/httpbin"])
    consumer = add("consumers", session, username="foobar", custom_id="1234")

    return service, route, consumer
