import secrets

import redis.asyncio as redis
from pydantic import BaseModel


class UpstreamSession(BaseModel):
    instance_url: str
    tac_id: str
    user_id: str
    upstream_jwt: str
    iam_access_id: str
    iam_access_secret: str
    business_name: str
    user_email: str


class SessionStore:
    def __init__(self, redis_url: str, ttl_seconds: int) -> None:
        self._redis: redis.Redis = redis.from_url(redis_url, decode_responses=True)
        self._ttl = ttl_seconds

    async def create(self, session: UpstreamSession) -> str:
        sid = secrets.token_urlsafe(32)
        await self._redis.set(self._key(sid), session.model_dump_json(), ex=self._ttl)
        return sid

    async def get(self, sid: str) -> UpstreamSession | None:
        raw = await self._redis.get(self._key(sid))
        if not raw:
            return None
        return UpstreamSession.model_validate_json(raw)

    async def delete(self, sid: str) -> None:
        await self._redis.delete(self._key(sid))

    async def ping(self) -> bool:
        return bool(await self._redis.ping())

    async def close(self) -> None:
        await self._redis.aclose()

    @staticmethod
    def _key(sid: str) -> str:
        return f"appify-connector:session:{sid}"
