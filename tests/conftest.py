import os

import psycopg2
from psycopg2.extras import DictCursor
import pytest

from kongcli._session import LiveServerSession


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
