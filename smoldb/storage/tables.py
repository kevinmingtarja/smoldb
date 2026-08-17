from smoldb.storage import encoding
from dataclasses import dataclass
from enum import Enum
from smoldb.storage.engine import Engine
import secrets

@dataclass(frozen=True, slots=True)
class Row:
    fields: tuple[str, ...] # immutable
    values: tuple[encoding.Value, ...]

def serialize_row(row: Row) -> bytes:
    buffer = bytearray()
    for value in row.values:
        payload = value.serialize()
        encoding.write_frame(buffer, payload)
    return bytes(buffer)

def deserialize_row(data: bytes, fields: tuple[str, ...]) -> Row:
    offset = 0
    values: list[encoding.Value] = []
    while offset < len(data):
        raw_payload, offset = encoding.read_frame(data, offset)
        value = encoding.Value.deserialize(raw_payload)
        values.append(value)
    return Row(fields, tuple(values))

def generate_id() -> bytes:
    return secrets.token_bytes(16)

def row_prefix(table: str) -> bytes:
    return f"row/{table}/".encode()

def row_key(table: str, row_id: bytes) -> bytes:
    return row_prefix(table) + row_id

def insert_row(db: Engine, table: str, row: Row) -> None:
    row_id = generate_id()
    key = row_key(table, row_id)
    row_bytes = serialize_row(row)
    db.put(key, row_bytes)


class DataType(Enum):
    BOOLEAN = "BOOLEAN"
    INTEGER = "INTEGER"
    TEXT = "TEXT"

@dataclass(frozen=True, slots=True)
class Column:
    name: str
    dtype: DataType

@dataclass(frozen=True, slots=True)
class Table:
    name: str
    columns: tuple[Column, ...]


    @property
    def fields(self) -> tuple[str, ...]:
        return tuple(col.name for col in self.columns)


class TableAlreadyExistsError(Exception):
    def __init__(self, table: str):
        self.table = table
        super().__init__(f"table already exists: {table}")


TABLE_PREFIX = "table/"

def table_prefix() -> bytes:
    return TABLE_PREFIX.encode('utf-8')

def table_key(name: str) -> bytes:
    return table_prefix() + name.encode('utf-8')


def serialize_table(table: Table) -> bytes:
    buffer = bytearray()
    for col in table.columns:
        encoding.write_frame(buffer, col.name.encode('utf-8'))
        encoding.write_frame(buffer, col.dtype.value.encode('utf-8'))
    return bytes(buffer)

def deserialize_table(name: str, data: bytes) -> Table:
    offset = 0
    columns = []
    while offset < len(data):
        raw_payload, offset = encoding.read_frame(data, offset)
        col_name = raw_payload.decode('utf-8')
        raw_payload, offset = encoding.read_frame(data, offset)
        dtype = DataType(raw_payload.decode('utf-8'))
        columns.append(Column(col_name, dtype))
    return Table(name, tuple(columns))



def create_table(db: Engine, table: Table) -> None:
    if get_table(db, table.name) is not None:
        raise TableAlreadyExistsError(table.name)
    key = table_key(table.name)
    table_bytes = serialize_table(table)
    db.put(key, table_bytes)

def get_table(db: Engine, name: str) -> Table | None:
    key = table_key(name)
    table_bytes = db.get(key)
    if table_bytes is None:
        return None
    return deserialize_table(name, table_bytes)

def list_tables(db: Engine) -> list[Table]:
    tables = []
    with db.scan_prefix(table_prefix()) as entries:
        for (key, table_bytes) in entries:
            name = key[len(TABLE_PREFIX):].decode('utf-8')
            tables.append(deserialize_table(name, table_bytes))
    return tables
