from datetime import datetime, timezone

import pytest

from kongcli._util import dict_from_dot, get, parse_datetimes


def test_get():
    called = False

    def _helper():
        nonlocal called
        if called:
            assert False, 'Already called - not cached.'
        called = True
        return 42

    assert 42 == get('fooo', _helper)
    assert 42 == get('fooo', _helper)  # get from cache and not from calling again


def test_dict_from_dot_hierarchy():
    # dots give deeper hierarchy of objects
    assert dict_from_dot([('foo', '12')]) == {'foo': 12}
    assert dict_from_dot([('foo.bar', '12')]) == {'foo': {'bar': 12}}
    assert dict_from_dot([('foo.bar.baz', '12')]) == {'foo': {'bar': {'baz': 12}}}


def test_dict_from_dot_json_parsing():
    # the RHS will be parsed as json
    assert dict_from_dot([('foo', '12')]) == {'foo': 12}
    assert dict_from_dot([('foo', '"12"')]) == {'foo': "12"}
    assert dict_from_dot([('foo', '12.5')]) == {'foo': 12.5}
    assert dict_from_dot([('foo', '[12]')]) == {'foo': [12]}
    assert dict_from_dot([('foo', 'true')]) == {'foo': True}
    assert dict_from_dot([('foo', 'false')]) == {'foo': False}
    assert dict_from_dot([('foo', '{"bar": 12}')]) == {'foo': {'bar': 12}}
    assert dict_from_dot([('foo', '{"bar": {"baz": 12}}')]) == {'foo': {'bar': {'baz': 12}}}

    # if it cannot be parsed, string is assumed
    assert dict_from_dot([('foo', '12"')]) == {'foo': '12"'}
    assert dict_from_dot([('foo', '12,7')]) == {'foo': '12,7'}


def test_dict_from_dot_duplicates():
    with pytest.raises(AssertionError):
        dict_from_dot([('foo', '12'), ('foo.bar', '12')])
    with pytest.raises(AssertionError):
        dict_from_dot([('foo.bar', '12'), ('foo', '12')])


def test_parse_datetimes_empty():
    d = {}
    parse_datetimes(d)
    assert d == {}


@pytest.mark.parametrize('key', ('created_at', 'updated_at'))
def test_parse_datetimes_key(key):
    now = datetime.now(tz=timezone.utc)

    # some have sec accuracy
    d = {key: now.timestamp()}
    parse_datetimes(d)
    assert d[key] == now

    # some have msec accuracy
    d = {key: now.timestamp() * 1000}
    parse_datetimes(d)
    assert d[key] == now
