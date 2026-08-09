import smoldb.storage.lmdb as lmdb
import pytest


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / 'test.db'


@pytest.fixture
def test_db(db_path):
    db = lmdb.open(db_path)
    yield db
    db.close()


def test_put_then_get(test_db):
    key = b'key'
    value = b'value'
    test_db.put(key, value)
    assert test_db.get(key) == value


def test_missing_key_returns_none(test_db):
    assert test_db.get(b'absent') is None


def test_overwrite_existing_key(test_db):
    test_db.put(b'key', b'first')
    test_db.put(b'key', b'second')
    assert test_db.get(b'key') == b'second'


def test_scan_prefix_matching(test_db):
    test_db.put(b'foo:a', b'1')
    test_db.put(b'foo:b', b'2')
    test_db.put(b'bar:x', b'3')

    actual = list(test_db.scan_prefix(b'foo:'))
    assert actual == [(b'foo:a', b'1'), (b'foo:b', b'2')]


def test_scan_prefix_no_match(test_db):
    test_db.put(b'foo:a', b'1')
    test_db.put(b'bar:b', b'2')

    assert list(test_db.scan_prefix(b'baz:')) == []


def test_scan_prefix_empty_prefix(test_db):
    # Empty prefix should behave like "all keys", and this also verifies
    # lmdb iteration order is lexical (not insertion order).
    test_db.put(b'foo:a', b'1')
    test_db.put(b'bar:b', b'2')

    assert list(test_db.scan_prefix(b'')) == [(b'bar:b', b'2'), (b'foo:a', b'1')]


def test_scan_prefix_sorted_iteration(test_db):
    test_db.put(b'a:3', b'3')
    test_db.put(b'a:1', b'1')
    test_db.put(b'a:2', b'2')
    test_db.put(b'b:0', b'0')

    actual = list(test_db.scan_prefix(b'a:'))
    assert actual == [(b'a:1', b'1'), (b'a:2', b'2'), (b'a:3', b'3')]


def test_scan_prefix_early_close(test_db):
    # Explicitly closing the iterator should release cursor/txn so further use
    # raises StopIteration instead of leaking resources or yielding stale data.
    test_db.put(b'a:1', b'1')
    test_db.put(b'a:2', b'2')

    it = test_db.scan_prefix(b'a:')
    assert next(it) == (b'a:1', b'1')
    it.close()

    with pytest.raises(StopIteration):
        next(it)


def test_persistence_after_close_and_reopen(db_path):
    # Exercise durable semantics: commit to env, close process-local handles,
    # reopen the same path, then verify data is still readable.
    db = lmdb.open(db_path)
    db.put(b'persist', b'yes')
    db.close()

    reopened = lmdb.open(db_path)
    try:
        assert reopened.get(b'persist') == b'yes'
    finally:
        reopened.close()
