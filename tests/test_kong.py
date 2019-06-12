from kongcli._kong import information


def test_information(session):
    resp = information(session)
    assert isinstance(resp, dict)
    assert '0.13.1' == resp['version']
