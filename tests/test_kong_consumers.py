from uuid import uuid4

import pytest

from kongcli._kong import (
    add,
    consumer_add_basic_auth,
    consumer_add_group,
    consumer_add_key_auth,
    consumer_basic_auths,
    consumer_delete_basic_auth,
    consumer_delete_group,
    consumer_delete_key_auth,
    consumer_groups,
    consumer_key_auths,
    consumer_plugins,
    consumer_update_basic_auth,
    consumer_update_key_auth,
)


def test_no_acl_for_new_consumer(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    assert [] == consumer_groups(session, consumer["id"])


def test_add_acl_to_consumer(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    consumer_add_group(session, consumer["id"], "some-nice-group")
    assert ["some-nice-group"] == consumer_groups(session, consumer["id"])


def test_add_acl_twice_to_consumer(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    consumer_add_group(session, consumer["id"], "some-nice-group")
    with pytest.raises(Exception) as e:
        consumer_add_group(session, consumer["id"], "some-nice-group")
    assert (
        str(e.value).strip()
        == '400 Bad Request: {"group":"ACL group already exist for this consumer"}'
    )


def test_add_multiple_acl_to_consumer(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    consumer_add_group(session, consumer["id"], "some-nice-group1")
    consumer_add_group(session, consumer["id"], "some-nice-group2")
    consumer_add_group(session, consumer["id"], "some-nice-group3")
    assert ["some-nice-group1", "some-nice-group2", "some-nice-group3"] == sorted(
        consumer_groups(session, consumer["id"])
    )


def test_delete_non_exsiting_acl(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    with pytest.raises(Exception) as e:
        consumer_delete_group(session, consumer["id"], "some-group")
    assert str(e.value).strip() == '404 Not Found: {"message":"Not found"}'
    # also with other group we get an error
    consumer_add_group(session, consumer["id"], "some-nice-group1")
    with pytest.raises(Exception) as e:
        consumer_delete_group(session, consumer["id"], "some-group")
    assert str(e.value).strip() == '404 Not Found: {"message":"Not found"}'


def test_no_basic_auths(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    assert [] == consumer_basic_auths(session, consumer["id"])


def test_add_basic_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_basic_auth(session, consumer["id"], "some.username", "password")
    assert [ba] == consumer_basic_auths(session, consumer["id"])
    assert ba["consumer_id"] == consumer["id"]
    assert ba["username"] == "some.username"
    assert ba["password"] != "password"  # some hash


def test_delete_non_existing_basic_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    with pytest.raises(Exception) as e:
        consumer_delete_basic_auth(session, consumer["id"], str(uuid4()))
    assert str(e.value).strip() == '404 Not Found: {"message":"Not found"}'


def test_delete_basic_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_basic_auth(session, consumer["id"], "some.username", "password")
    consumer_delete_basic_auth(session, consumer["id"], ba["id"])
    assert [] == consumer_basic_auths(session, consumer["id"])


def test_update_basic_auth_no_params(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_basic_auth(session, consumer["id"], "some.username", "password")
    with pytest.raises(AssertionError):
        consumer_update_basic_auth(session, consumer["id"], ba["id"])


def test_update_basic_auth_username(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_basic_auth(session, consumer["id"], "some.username", "password")
    consumer_update_basic_auth(
        session, consumer["id"], ba["id"], username="username.some"
    )
    bas = consumer_basic_auths(session, consumer["id"])
    assert len(bas) == 1
    assert "username.some" == bas[0].pop("username")
    ba.pop("username")
    assert ba == bas[0]


def test_update_basic_auth_password(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_basic_auth(session, consumer["id"], "some.username", "password")
    consumer_update_basic_auth(session, consumer["id"], ba["id"], password="4321")
    bas = consumer_basic_auths(session, consumer["id"])
    assert len(bas) == 1
    assert ba.pop("password") != bas[0].pop("password")
    assert ba == bas[0]


def test_update_basic_auth_username_password(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_basic_auth(session, consumer["id"], "some.username", "password")
    consumer_update_basic_auth(
        session, consumer["id"], ba["id"], username="username.some", password="4321"
    )
    bas = consumer_basic_auths(session, consumer["id"])
    assert len(bas) == 1
    assert ba.pop("password") != bas[0].pop("password")
    assert "username.some" == bas[0].pop("username")
    ba.pop("username")
    assert ba == bas[0]


def test_no_key_auths(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    assert [] == consumer_key_auths(session, consumer["id"])


def test_add_key_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ka = consumer_add_key_auth(session, consumer["id"])
    assert [ka] == consumer_key_auths(session, consumer["id"])
    assert ka["consumer_id"] == consumer["id"]
    assert ka["key"]


def test_add_key_auth_with_key(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ka = consumer_add_key_auth(session, consumer["id"], key="1234567890")
    assert [ka] == consumer_key_auths(session, consumer["id"])
    assert ka["consumer_id"] == consumer["id"]
    assert "1234567890" == ka["key"]


def test_delete_non_existing_key_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    with pytest.raises(Exception) as e:
        consumer_delete_key_auth(session, consumer["id"], str(uuid4()))
    assert str(e.value).strip() == '404 Not Found: {"message":"Not found"}'


def test_delete_key_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ba = consumer_add_key_auth(session, consumer["id"])
    consumer_delete_key_auth(session, consumer["id"], ba["id"])
    assert [] == consumer_key_auths(session, consumer["id"])


def test_update_key_auth(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    ka = consumer_add_key_auth(session, consumer["id"])
    consumer_update_key_auth(session, consumer["id"], ka["id"], key="4321")
    kas = consumer_key_auths(session, consumer["id"])
    assert len(kas) == 1
    assert "4321" == kas[0].pop("key")
    ka.pop("key")
    assert ka == kas[0]


def test_no_plugins(session, clean_kong):
    consumer = add("consumers", session, username="test-user", custom_id="1234")
    assert [] == consumer_plugins(session, consumer["id"])
