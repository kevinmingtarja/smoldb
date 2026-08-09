from typing import Self
from dataclasses import dataclass
import struct

# Big endian
I64 = struct.Struct(">q")
U64 = struct.Struct(">Q")

@dataclass(frozen=True, slots=True)
class Value:
    data: None | bool | bytes | int

    def serialize(self) -> bytes:
        """Serialize the value into a tagged bytes payload.

        Format:
        - ``None`` -> ``b'0'``
        - ``bool`` -> ``b'1' + b'1'`` for True, ``b'1' + b'0'`` for False
        - ``bytes`` -> ``b'2' + <raw bytes>``
        - ``int`` -> ``b'3' + <8-byte big-endian signed integer>``

        Raises:
            TypeError: if ``data`` is not one of the supported types.
        """
        if self.data is None:
            return b'0'
        if isinstance(self.data, bool):
            return b'1' + (b'1' if self.data else b'0')
        if isinstance(self.data, bytes):
            return b'2' + self.data
        if isinstance(self.data, int):
            return b'3' + I64.pack(self.data)
        
        raise TypeError(f"unsupported value: {type(self.data).__name__}")
    
    @classmethod
    def deserialize(cls, data: bytes) -> Self:
        # Note: bytes behaves differently depending on whether you index
        # it or slice it. Example:
        # >>> data = b'11'
        # >>> data[0]
        # 49
        # >>> data[:1]
        # b'1'
        tag = data[:1]
        if tag not in (b"0", b"1", b"2", b"3"):
            raise ValueError(f"unknown Value tag: {tag!r}")
        if tag == b'0':
            return Value(None)
        if tag == b'1':
            return Value(data[1:2] == b'1')
        if tag == b'2':
            return Value(data[1:])
        if tag == b'3':
            return Value(I64.unpack_from(data, 1)[0])
