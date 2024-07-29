from dataclasses import dataclass
from typing import Self, cast
from uuid import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus, ContextEventProtocol, impl_event
from bakery_ecommerce.internal.identity.token import PrivateKeyProtocol
from bakery_ecommerce.internal.store.crud_queries import CrudOperation
from bakery_ecommerce.internal.store.query import QueryProcessor

from .private_key import PrivateKeyES256K1
from .store.private_key_session_model import PrivateKeySession


@dataclass
@impl_event(ContextEventProtocol)
class PrivateKeyCreatedEvent:
    pkey: PrivateKeyProtocol
    user_id: UUID

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class CreatePrivateKeyEvent:
    user_id: UUID

    @property
    def payload(self) -> Self:
        return self


class CreatePrivateKey:
    def __init__(
        self, context: ContextBus, sesssion: AsyncSession, queries: QueryProcessor
    ) -> None:
        self.__context = context
        self.__session = sesssion
        self.__queries = queries

    async def execute(self, params: CreatePrivateKeyEvent) -> PrivateKeySession:
        pkey = PrivateKeyES256K1.from_random()

        pkey_session = PrivateKeySession()
        pkey_session.user_id = params.user_id

        kid = pkey.kid()
        if not kid:
            raise ValueError(f"Not found pkey kid for {params.user_id}")

        pkey_session.kid = kid
        pkey_session.signature = pkey.jwk_sign_message()

        operation = CrudOperation(
            PrivateKeySession, lambda q: q.create_one(pkey_session)
        )
        await self.__queries.process(self.__session, operation)
        await self.__session.flush()
        await self.__context.publish(PrivateKeyCreatedEvent(pkey, pkey_session.user_id))
        return pkey_session
