import smoldb.storage.lmdb as lmdb
import pytest


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / 'test.db'
    db = lmdb.open(db_path)
    yield db

def test_put_then_get(test_db):
    key = b'key'
    value = b'value'
    test_db.put(key, value)
    assert test_db.get(key) == value
