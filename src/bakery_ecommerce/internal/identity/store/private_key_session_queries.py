from dataclasses import dataclass
import json
from typing import Any, override

from nats.js.api import KeyValueConfig, StorageType
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal.identity.store.private_key_session_model import (
    PrivateKeySession,
)
from bakery_ecommerce.internal.store import query


@dataclass
@query.impl_cache(query.QueryCacheKeyProtocol[dict[str, Any] | None])
class GetPrivateKeySignature(query.Query[dict[str, Any] | None]):
    user_id: str
    kid: str

    def cache_key(self) -> str:
        return f"{self.user_id}.{self.kid}"

    def cache_config(self) -> KeyValueConfig:
        return KeyValueConfig(
            bucket="private_key_signatures",
            storage=StorageType.MEMORY,
            ttl=60 * 5,
        )

    def cache_serialize(self, model: dict[str, Any] | None) -> str:
        if model is None:
            raise ValueError("Private key signature is none")
        return json.dumps(model)

    def cache_deserialize(self, value: str) -> dict[str, Any] | None:
        return json.loads(value)


class GetPrivateKeySignatureHandler(
    query.QueryHandler[GetPrivateKeySignature, dict[str, Any] | None]
):
    @override
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    @override
    async def handle(self, query: GetPrivateKeySignature) -> dict[str, Any] | None:
        stmt = select(PrivateKeySession.signature).where(
            and_(
                PrivateKeySession.user_id == query.user_id,
                PrivateKeySession.kid == query.kid,
            )
        )

        result = await self.__executor.execute(stmt)
        return result.scalar_one_or_none()
