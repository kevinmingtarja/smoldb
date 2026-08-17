import pytest

from smoldb.storage import lmdb
from smoldb.storage.encoding import Value
from smoldb.storage.tables import Column
from smoldb.storage.tables import DataType
from smoldb.storage.tables import Row
from smoldb.storage.tables import Table
from smoldb.storage.tables import TableAlreadyExistsError
from smoldb.storage.tables import create_table
from smoldb.storage.tables import deserialize_row
from smoldb.storage.tables import deserialize_table
from smoldb.storage.tables import get_table
from smoldb.storage.tables import insert_row
from smoldb.storage.tables import list_tables
from smoldb.storage.tables import row_prefix
from smoldb.storage.tables import serialize_row
from smoldb.storage.tables import serialize_table


@pytest.fixture
def test_db(tmp_path):
    db = lmdb.open(tmp_path / "test.db")
    yield db
    db.close()


def test_row_roundtrip():
    fields = ("missing", "enabled", "name", "count")
    row = Row(
        fields=fields,
        values=(Value(None), Value(True), Value(b"smoldb"), Value(123)),
    )

    assert deserialize_row(serialize_row(row), fields) == row


def test_table_roundtrip():
    table = Table(
        name="users",
        columns=(
            Column("enabled", DataType.BOOLEAN),
            Column("id", DataType.INTEGER),
            Column("name", DataType.TEXT),
        ),
    )

    assert deserialize_table(table.name, serialize_table(table)) == table
    assert table.fields == ("enabled", "id", "name")


def test_create_and_get_table(test_db):
    table = Table(
        name="users",
        columns=(
            Column("id", DataType.INTEGER),
            Column("name", DataType.TEXT),
        ),
    )

    create_table(test_db, table)

    assert get_table(test_db, "users") == table
    assert get_table(test_db, "missing") is None


def test_create_table_rejects_duplicate(test_db):
    original = Table("users", (Column("id", DataType.INTEGER),))
    replacement = Table("users", (Column("name", DataType.TEXT),))

    create_table(test_db, original)

    with pytest.raises(TableAlreadyExistsError, match="table already exists: users"):
        create_table(test_db, replacement)

    assert get_table(test_db, "users") == original


def test_list_tables(test_db):
    posts = Table("posts", (Column("body", DataType.TEXT),))
    users = Table("users", (Column("id", DataType.INTEGER),))

    create_table(test_db, users)
    create_table(test_db, posts)

    assert list_tables(test_db) == [posts, users]


def test_insert_row(test_db):
    row = Row(
        fields=("id", "name"),
        values=(Value(1), Value(b"Ada")),
    )

    insert_row(test_db, "users", row)

    prefix = row_prefix("users")
    with test_db.scan_prefix(prefix) as entries:
        stored = list(entries)

    assert len(stored) == 1
    key, data = stored[0]
    assert key.startswith(prefix)
    assert len(key) == len(prefix) + 16
    assert deserialize_row(data, row.fields) == row


def test_rows_are_isolated_by_table(test_db):
    users_row = Row(("id",), (Value(1),))
    posts_row = Row(("id",), (Value(2),))

    insert_row(test_db, "users", users_row)
    insert_row(test_db, "posts", posts_row)

    with test_db.scan_prefix(row_prefix("users")) as entries:
        users_data = [data for _, data in entries]
    with test_db.scan_prefix(row_prefix("posts")) as entries:
        posts_data = [data for _, data in entries]

    assert [deserialize_row(data, users_row.fields) for data in users_data] == [
        users_row
    ]
    assert [deserialize_row(data, posts_row.fields) for data in posts_data] == [
        posts_row
    ]
