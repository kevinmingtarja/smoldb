import struct
from smoldb.storage.encoding import Value
from dataclasses import dataclass
from smoldb.storage.engine import Engine
import secrets

# Big endian
U64 = struct.Struct(">Q")

@dataclass(frozen=True, slots=True)
class Row:
    fields: tuple[str, ...] # immutable
    values: list[Value]

def serialize_row(row: Row) -> bytes:
    buffer = bytearray()
    for value in row.values:
        payload = value.serialize()
        write_frame(buffer, payload)
    return bytes(buffer)

def deserialize_row(data: bytes, fields: tuple[str, ...]) -> Row:
    offset = 0
    values: list[Value] = []
    while offset < len(data):
        raw_payload, offset = read_frame(data, offset)
        value = Value.deserialize(raw_payload)
        values.append(value)
    return Row(fields=fields, values=values)

def write_frame(buf: bytearray, payload: bytes) -> None:
    length = len(payload)
    buf.extend(U64.pack(length))
    buf.extend(payload)

def read_frame(data: bytes, offset: int) -> tuple[bytes, int]:
    """Read [u64 length][payload] and return (payload, next offset)."""
    header_end = offset + U64.size
    if header_end > len(data):
        raise ValueError("truncated frame header")

    length = U64.unpack_from(data, offset)[0]
    payload_end = header_end + length

    if payload_end > len(data):
        raise ValueError("truncated frame payload")

    payload = data[header_end:payload_end]
    return (payload, payload_end)

def generate_id() -> bytes:
    return secrets.token_bytes(16)

def table_key(name: str) -> bytes:
    return f"table/{name}".encode()

def row_prefix(table: str) -> bytes:
    return f"row/{table}/".encode()

def row_key(table: str, row_id: bytes) -> bytes:
    return row_prefix(table) + row_id

def insert_row(db: Engine, table: str, row: Row) -> None:
    row_id = generate_id()
    key = row_key(table, row_id)
    row_bytes = serialize_row(row)
    db.put(key, row_bytes)
