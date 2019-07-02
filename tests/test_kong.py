from math import ceil
from operator import itemgetter
import os
from time import time
import uuid

import pytest

from kongcli._kong import (
    add,
    all_of,
    consumer_groups,
    consumer_add_group,
    delete,
    information,
    retrieve,
)


def test_information(session, clean_kong):
    resp = information(session)
    assert isinstance(resp, dict)
    assert os.environ.get("KONG_VERSION_TAG", "0.13.1") == resp["version"]


@pytest.mark.parametrize(
    "resource",
    ("consumers", "services", "routes", "plugins", "acls", "key-auths", "basic-auths"),
)
def test_all_of_empty(resource, session, clean_kong):
    assert all_of(resource, session) == []


def test_add_all_of_consumer(session, clean_kong):
    consumer1 = add("consumers", session, username="test-user", custom_id="1234")
    assert consumer1["username"] == "test-user"
    assert consumer1["custom_id"] == "1234"
    assert uuid.UUID(consumer1["id"])
    assert consumer1["created_at"] <= ceil(time()) * 1000

    consumer2 = add("consumers", session, custom_id="12345")
    assert "username" not in consumer2
    assert consumer2["custom_id"] == "12345"
    assert uuid.UUID(consumer2["id"])
    assert consumer2["created_at"] <= ceil(time()) * 1000

    consumer3 = add("consumers", session, username="test-user2")
    assert consumer3["username"] == "test-user2"
    assert "custom_id" not in consumer3
    assert uuid.UUID(consumer3["id"])
    assert consumer3["created_at"] <= ceil(time()) * 1000

    consumers = all_of("consumers", session)
    assert 3 == len(consumers)
    assert sorted([consumer1, consumer2, consumer3], key=itemgetter("id")) == sorted(
        consumers, key=itemgetter("id")
    )


def test_add_all_of_consumer_paginate(session, clean_kong):
    for i in range(201):
        add("consumers", session, custom_id=str(i))

    consumers = all_of("consumers", session)
    assert 201 == len(consumers)


def test_retrieve_consumer(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    rconsumer = retrieve("consumers", session, consumer["id"])
    assert consumer == rconsumer


def test_delete_consumer(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    delete("consumers", session, consumer["id"])
    assert [] == all_of("consumers", session)
