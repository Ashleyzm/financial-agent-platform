"""Redis-backed task queue."""

from uuid import UUID

import redis


class RedisTaskQueue:
    def __init__(self, url: str, *, key: str = "tasks:queue") -> None:
        self._client = redis.Redis.from_url(url, decode_responses=True)
        self._key = key

    def enqueue(self, task_id: UUID) -> None:
        self._client.rpush(self._key, str(task_id))

    def dequeue(self, timeout: float) -> UUID | None:
        item = self._client.blpop(self._key, timeout=timeout)
        if item is None:
            return None
        _, task_id = item
        return UUID(task_id)

    def remove(self, task_id: UUID) -> None:
        self._client.lrem(self._key, 0, str(task_id))

    def close(self) -> None:
        self._client.close()
