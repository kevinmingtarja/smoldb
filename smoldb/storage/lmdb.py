from types import TracebackType
from typing import Self
from collections.abc import Iterator
import lmdb as lmdb_lib


class LmdbIterator:
    def __init__(self, env: lmdb_lib.Environment, prefix: bytes):
        self._prefix = prefix
        self._closed = False
        self._txn = env.begin(write=False)
    
        try:
            self._cursor = self._txn.cursor()
        except BaseException:
            self._txn.abort()
            raise
        
        self._items: Iterator[tuple[bytes, bytes]] = iter(())

        try:
            if self._cursor.set_range(prefix):
                self._items = self._cursor.iternext()
            else:
                self.close()
        except BaseException:
            self.close()
            raise
    
    def __iter__(self) -> Self:
        return self
    
    def __next__(self) -> tuple[bytes, bytes]:
        if self._closed:
            raise StopIteration
        
        try:
            key, value = next(self._items)
        except BaseException:
            self.close()
            raise
        
        # we've reached the end of the prefix boundary.
        if not key.startswith(self._prefix):
            self.close()
            raise StopIteration
        
        return key, value
    
    def close(self) -> None:
        if self._closed:
            return
        
        self._closed = True
        try:
            self._cursor.close()
        finally:
            self._txn.abort()
    
    def __enter__(self) -> Self:
        return self
    
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class Lmdb:
    def __init__(self, env: lmdb_lib.Environment):
        self.env: lmdb_lib.Environment = env
    
    def get(self, key: bytes) -> bytes | None:
        with self.env.begin(write=False) as txn:
            return txn.get(key)
    
    def put(self, key: bytes, value: bytes) -> None:
        with self.env.begin(write=True) as txn:
            txn.put(key, value)
    
    def scan_prefix(self, prefix: bytes) -> LmdbIterator:
        return LmdbIterator(self.env, prefix)

    def close(self) -> None:
        self.env.close()



def open(path: str) -> Lmdb:
    env = lmdb_lib.open(path)
    return Lmdb(env)
