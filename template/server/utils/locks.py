import asyncio


class LockedMap:
    def __init__(self):
        self.map_lock = asyncio.Lock()
        self.map = {}
        self.locks = {}

    def get(self, key):
        return self.map.get(key)

    def set(self, key, value):
        self.map[key] = value

    async def get_lock(self, key):
        await self.map_lock.acquire()
        if key not in self.locks:
            self.locks[key] = asyncio.Lock()

        lock = self.locks[key]
        print(f"Lock acquired for {key}")
        self.map_lock.release()
        return lock

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)
