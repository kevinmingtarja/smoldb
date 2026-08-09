from types import TracebackType
from typing import Protocol, Self


class KVIterator(Protocol):
    """Ordered key-value iterator that owns its storage resources.

    The iterator closes its resources when exhausted. Callers that may stop
    iteration early must use it as a context manager or call close().
    """

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
    """Byte-oriented key-value storage engine."""

    def get(self, key: bytes) -> bytes | None:
        """Return the value stored for key, or None when key is absent."""
        ...

    def put(self, key: bytes, value: bytes) -> None:
        """Store value, replacing any value already stored for key."""
        ...

    def scan_prefix(self, prefix: bytes) -> KVIterator:
        """Iterate over matching entries in ascending key order.

        An empty prefix matches every entry.
        """
        ...

    def close(self) -> None:
        ...
