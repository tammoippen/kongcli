import os
from typing import List

from click.testing import CliRunner
import psycopg2
from psycopg2.extras import DictCursor
import pytest

from kongcli._cli import cli
from kongcli._session import LiveServerSession
from kongcli.kong.general import add, information


@pytest.fixture()
def invoke():
    runner = CliRunner()

    def _invoke(args: List[str]):
        return runner.invoke(cli, args)

    return _invoke


@pytest.fixture()
def session():
    return LiveServerSession("http://localhost:8001")


@pytest.fixture()
def clean_kong():
    with psycopg2.connect(
        database=os.environ.get("KONG_PG_DATABASE", "kong"),
        user=os.environ.get("KONG_PG_USER", "kong"),
        password=os.environ.get("KONG_PG_PASSWORD", "kong"),
        host="localhost",
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
def sample(clean_kong, session):
    service = add("services", session, name="httpbin", url="http://localhost:8080")
    route = add("routes", session, service={"id": service["id"]}, paths=["/httpbin"])
    consumer = add("consumers", session, username="foobar", custom_id="1234")

    return service, route, consumer
