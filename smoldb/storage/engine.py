from types import TracebackType
from typing import Self
from typing import Protocol

class KVIterator(Protocol):
    def __iter__(self) -> Self:
        ...
    
    def __next__(self) -> tuple[bytes, bytes]:
        ...

    def close(self) -> None:
        ...
    
    def __enter__(self) -> Self:
        ...
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        ...

class Engine(Protocol):
    def get(self, key: bytes) -> bytes | None:
        ...
    
    def put(self, key: bytes, value: bytes) -> None:
        ...
    
    def scan_prefix(self, prefix: bytes) -> KVIterator:
        ...
    
    def close(self) -> None:
        ...