from smoldb.storage import encoding
import pytest


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, b"11"),
        (None, b"0"),
        (b"abc", b"2" + b"abc"),
        (123, b"3" + b"\x00\x00\x00\x00\x00\x00\x00{"),
    ],
)
def test_serialize(value: object, expected: bytes) -> None:
    assert encoding.Value(value).serialize() == expected


@pytest.mark.parametrize("value", [None, True, b"abc", 123])
def test_roundtrip(value: object) -> None:
    val = encoding.Value(value)
    assert encoding.Value.deserialize(val.serialize()) == val
