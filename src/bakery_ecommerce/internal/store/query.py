"""
That pattern apply Single Responsibility Principle, Open/Closed Principle, Interface Segregation Principle.

And remove that repository pattern

The QueryProcessor Mediator pattern allow to not know a concrete query handler type
"""

import inspect
from abc import ABC, abstractmethod
from typing import Generic, Protocol, Type, TypeVar, TypeAlias, runtime_checkable

from nats.js.api import KeyValueConfig
from nats.js.errors import BucketNotFoundError
from nats.js.kv import KeyValue
from sqlalchemy.ext.asyncio import AsyncSession

from nats.aio.client import Client as NATS

QueryResult_T = TypeVar(
    "QueryResult_T",
    infer_variance=True,
    # bound=persistence.base.PersistanceBase
)


class Query(ABC, Generic[QueryResult_T]): ...


@runtime_checkable
class QueryCacheKeyProtocol(Protocol[QueryResult_T]):
    def cache_key(self) -> str: ...
    def cache_config(self) -> KeyValueConfig: ...
    def cache_serialize(self, model: QueryResult_T) -> str: ...
    def cache_deserialize(self, value: str) -> QueryResult_T: ...


Query_T = TypeVar("Query_T", bound=Query)


class QueryHandler(ABC, Generic[Query_T, QueryResult_T]):
    @abstractmethod
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    @abstractmethod
    async def handle(self, query: Query_T) -> QueryResult_T: ...


class QueryCache:
    def __init__(self, nats: NATS) -> None:
        self.__js = nats.jetstream()

    async def get_cache_or_none(
        self, query: Query[QueryResult_T]
    ) -> QueryResult_T | None:
        cacheable_query = isinstance(query, QueryCacheKeyProtocol)
        if not cacheable_query:
            return None

        try:
            bucket = await self.__create_or_get_kv_bucket(query.cache_config())
            kv = await bucket.get(query.cache_key())

            if kv.value is None:
                return None

            # TODO: Too much unsafe place
            value = query.cache_deserialize(kv.value.decode())
            assert value
            print(f"Get from cache bucket {query.cache_key()} data: {value}")
            return value
        except BucketNotFoundError:
            return None
        except Exception as e:
            print(f"Bucket error nats {e}")
            return None

    async def set_cache(
        self, query: Query[QueryResult_T], value: QueryResult_T
    ) -> int | None:
        cacheable_query = isinstance(query, QueryCacheKeyProtocol)
        if not cacheable_query:
            return None

        try:
            bucket = await self.__create_or_get_kv_bucket(query.cache_config())
            data = query.cache_serialize(value).encode()
            print(f"Store in cache bucket {query.cache_key()} data: {data}")
            return await bucket.put(query.cache_key(), data)
        except Exception as e:
            print(f"Unable store cache for {query}. Err: {e}")
            return None

    async def __create_or_get_kv_bucket(self, config: KeyValueConfig) -> KeyValue:
        try:
            return await self.__js.key_value(config.bucket)
        except BucketNotFoundError:
            return await self.__js.create_key_value(config)


QueryProcessorHandlers: TypeAlias = dict[type[Query], type[QueryHandler]]


class QueryProcessor:
    def __init__(self, handlers: QueryProcessorHandlers, cache: QueryCache):
        self.__handlers = handlers
        self.__cache = cache

    async def process(
        self, executor: AsyncSession, query: Query[QueryResult_T]
    ) -> QueryResult_T:
        query_type = type(query)

        cache_result = await self.__cache.get_cache_or_none(query)
        if cache_result is not None:
            return cache_result

        handler_type = self.__handlers.get(query_type)
        if not handler_type:
            raise ValueError(f"No handler found for query type {query_type}")

        handler = handler_type(executor)
        value = await handler.handle(query)

        if isinstance(query, QueryCacheKeyProtocol):
            await self.__cache.set_cache(query, value)

        return value


__ignore_protocol_member = ["copy_with"]


def _signatures_match(sig1, sig2):
    """Check if two signatures match, including type hints and generic types."""
    if sig1.parameters.keys() != sig2.parameters.keys():
        return False

    for param_name in sig1.parameters:
        param1 = sig1.parameters[param_name]
        param2 = sig2.parameters[param_name]

        if param1.annotation != param2.annotation:
            if isinstance(param1.annotation, TypeVar) or isinstance(
                param2.annotation, TypeVar
            ):
                continue
            return False

    if sig1.return_annotation != sig2.return_annotation:
        # print(sig1.return_annotation, sig2.return_annotation)

        if isinstance(sig1.return_annotation, TypeVar) or isinstance(
            sig2.return_annotation, TypeVar
        ):
            # TODO: error place
            return True

        return False

    return True


# TODO: same code for impl_event
def impl_cache(protocol: Type):
    def decorator(cls):
        protocol_members = {
            member
            for member in dir(protocol)
            if not (member.startswith("__") and member.endswith("__"))
            and not member.startswith("_")
            and member not in __ignore_protocol_member
        }

        cls_members = {member for member in dir(cls)}
        if not protocol_members.issubset(cls_members):
            missing_members = protocol_members - cls_members
            raise TypeError(
                f"Class {cls.__name__} is missing members required by the protocol: {missing_members}"
            )

        for member in protocol_members:
            protocol_member = getattr(protocol, member, None)
            cls_member = getattr(cls, member, None)
            if protocol_member is None or cls_member is None:
                continue

            if callable(protocol_member):
                if not callable(cls_member):
                    raise TypeError(
                        f"Member '{member}' in class '{cls.__name__}' should be callable as required by the protocol."
                    )
                protocol_member_sig = inspect.signature(protocol_member)
                cls_member_sig = inspect.signature(cls_member)
                if not _signatures_match(protocol_member_sig, cls_member_sig):
                    raise TypeError(
                        f"Signature of member '{member}' in class '{cls.__name__}' does not match the protocol."
                    )

            elif isinstance(protocol_member, property):
                if not isinstance(cls_member, property):
                    raise TypeError(
                        f"Member '{member}' in class '{cls.__name__}' should be a property as required by the protocol."
                    )

        return cls

    return decorator
