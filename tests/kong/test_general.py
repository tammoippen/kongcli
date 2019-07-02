from math import ceil
from operator import itemgetter
import os
from time import time
import uuid

import pytest

from kongcli.kong.general import add, all_of, delete, information, retrieve, update


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


@pytest.mark.parametrize(
    "resource, params",
    (
        ("consumers", {"username": "foobar"}),
        (
            "services",
            {"host": "localhost", "path": "/", "protocol": "http", "name": "foobar"},
        ),
        # ("routes", {'hosts': ['localhost'], 'service': {'id': str(uuid.uuid4())}}),  # need to create service first
        ("plugins", {"name": "key-auth"}),
    ),
)
def test_update_no_data(resource, params, session, clean_kong):
    r1 = add(resource, session, **params)

    if resource in ("services", "plugins"):
        r2 = update(resource, session, r1["id"])
        assert r1 == r2
    else:
        with pytest.raises(Exception):
            update(resource, session, r1["id"])


def test_update_consumer_username(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    uconsumer = update("consumers", session, consumer["id"], username="foobar")
    assert uconsumer.pop("username") == "foobar"
    consumer.pop("username")
    assert uconsumer == consumer


def test_update_consumer_custom_id(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    uconsumer = update("consumers", session, consumer["id"], custom_id="foobar")
    assert uconsumer.pop("custom_id") == "foobar"
    consumer.pop("custom_id")
    assert uconsumer == consumer
