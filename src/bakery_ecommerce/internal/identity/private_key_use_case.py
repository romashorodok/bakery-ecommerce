from dataclasses import dataclass
from json import loads
import json
from typing import Self
from uuid import UUID
from nats.aio.client import Client as NATS
from nats.js.api import KeyValueConfig, StorageType
from nats.js.errors import BucketNotFoundError
from nats.js.kv import KeyValue
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus, ContextEventProtocol, impl_event
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
    def __init__(
        self, nc: NATS, session: AsyncSession, queries: QueryProcessor
    ) -> None:
        self.__js = nc.jetstream()
        self.__session = session
        self.__queries = queries

    async def execute(self, params: GetPrivateKeySessionEvent):
        signature = None

        if cache := await self.__get_from_cache(params):
            signature = loads(cache)
            print("get from cache")

        if not isinstance(signature, dict) or len(signature) == 0:
            operation = CrudOperation(
                PrivateKeySession, lambda q: q.get_one_by_field("kid", params.kid)
            )
            result = await self.__queries.process(self.__session, operation)
            if not result:
                raise NotFoundPrivateKeyError()
            signature = result.signature
            print("get from db")

        if not signature:
            raise ValueError("Not found private key")

        token = PrivateKeyES256K1.from_bytes(signature)

        signature = token.sign_signature()
        kid = token.kid()
        if not kid:
            raise ValueError("Not found kid for token")

        await self.__set_in_cache(params.user_id, kid, signature)
        return token

    # TODO: this must wrap queries
    async def __get_from_cache(self, params: GetPrivateKeySessionEvent) -> bytes | None:
        try:
            private_keys_bucket = await self.__js.key_value("private_keys")
            jws_bytes = await private_keys_bucket.get(f"{params.user_id}:{params.kid}")
            return jws_bytes.value
        except BucketNotFoundError:
            return None
        except Exception as e:
            print(f"Bucket error nats {e}")
            return None

    async def __set_in_cache(self, user_id: str, kid: str, signature: dict):
        bucket: KeyValue | None = None

        try:
            bucket = await self.__js.key_value("private_keys")
        except Exception as e:
            print(f"set in cache bucket. Err: {e}")

        try:
            if not bucket:
                bucket = await self.__js.create_key_value(
                    KeyValueConfig(
                        bucket="private_keys",
                        storage=StorageType.MEMORY,
                    )
                )
        except Exception as e:
            print(f"Bucket create error {e}")
            return

        revision = await bucket.put(f"{user_id}:{kid}", json.dumps(signature).encode())
        print(f"Store reuslt in check {revision}")


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
