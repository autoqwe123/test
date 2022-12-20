from threading import Lock

class Messenger:
    MAX_CACHE = 1000

    def __init__(self):
        self.cache = []
        self.lock = Lock()

    def handler(self, key):
        return True

    def filter(self, operation, *keys):
        return "\x1e".join(map(str, [operation.createdTime] + list(keys)))

    def __call__(self, operation, *keys):
        key = self.filter(operation, *keys)
        with self.lock:
            if key in self.cache:
                return False
            else:
                self.cache.append(key)
        if len(self.cache) > self.MAX_CACHE:
            self.cache = self.cache[self.MAX_CACHE//2]
        return self.handler(key)