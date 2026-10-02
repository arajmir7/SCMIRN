"""Redis client placeholder."""

class RedisClient:
    def __init__(self, url=None):
        self.url = url

    def get(self, key):
        raise NotImplementedError('Redis client not configured')
