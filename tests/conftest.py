import pytest

from kongcli._session import LiveServerSession


@pytest.fixture()
def session():
    return LiveServerSession('http://localhost:8001')
