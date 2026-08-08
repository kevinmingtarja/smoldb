import lmdb as lmdb_lib

class Lmdb:
    def __init__(self, env: lmdb_lib.Environment):
        self.env: lmdb_lib.Environment = env
    
    def begin(self, write: bool) -> lmdb_lib.Transaction:
        return self.env.begin(write=write)


def open(path: str) -> Lmdb:
    env = lmdb_lib.open(path)
    return Lmdb(env)
