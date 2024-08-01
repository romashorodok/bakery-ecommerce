from dataclasses import dataclass
from typing import Self
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus, ContextEventProtocol, impl_event
from bakery_ecommerce.internal.identity.store.private_key_session_queries import (
    GetPrivateKeySignature,
)
from bakery_ecommerce.internal.identity.token import PrivateKeyProtocol
from bakery_ecommerce.internal.store.crud_queries import CrudOperation
from bakery_ecommerce.internal.store.query import QueryProcessor

from .private_key import PrivateKeyES256K1
from .store.private_key_session_model import PrivateKeySession


@dataclass
@impl_event(ContextEventProtocol)
class GetPrivateKeySessionEvent:
    user_id: str
    kid: str

    @property
    def payload(self) -> Self:
        return self


class NotFoundPrivateKeyError(Exception): ...


class GetPrivateKeySession:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(self, params: GetPrivateKeySessionEvent):
        signature = None

        query = GetPrivateKeySignature(params.user_id, params.kid)

        signature = await self.__queries.process(self.__session, query)

        if signature is None or len(signature) == 0:
            raise ValueError("Not found private key or empty signature")

        token = PrivateKeyES256K1.from_bytes(signature)

        signature = token.sign_signature()
        kid = token.kid()
        if not kid:
            raise ValueError("Not found kid for token")

        return token


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
        pkey_session.signature = pkey.sign_signature()

        operation = CrudOperation(
            PrivateKeySession, lambda q: q.create_one(pkey_session)
        )
        await self.__queries.process(self.__session, operation)
        await self.__session.flush()
        await self.__context.publish(PrivateKeyCreatedEvent(pkey, pkey_session.user_id))
        return pkey_session
