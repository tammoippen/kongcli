from random import randint

from kongcli._session import LiveServerSession


def test_remove_multiple_slash():
    session = LiveServerSession("https://httpbin.org" + "/" * randint(0, 100))

    assert session.prefix_url == "https://httpbin.org"
    session.close()
