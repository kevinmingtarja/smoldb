from smoldb.storage.tables import deserialize_row
from smoldb.storage.encoding import Value
from smoldb.storage.tables import Row
from smoldb.storage.tables import serialize_row

def test_serde():
    fields = ("id", )
    row = Row(fields=fields, values=[Value(123)])
    b = serialize_row(row)
    row2 = deserialize_row(b, fields)
    assert row == row2