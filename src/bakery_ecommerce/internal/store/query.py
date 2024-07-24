"""
That pattern apply Single Responsibility Principle, Open/Closed Principle, Interface Segregation Principle.

And remove that repository pattern

The QueryProcessor Mediator pattern allow to not know a concrete query handler type
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, TypeAlias

from sqlalchemy.ext.asyncio import AsyncSession

QueryResult_T = TypeVar(
    "QueryResult_T",
    # bound=persistence.base.PersistanceBase
)


class Query(ABC, Generic[QueryResult_T]): ...


Query_T = TypeVar("Query_T", bound=Query)


class QueryHandler(ABC, Generic[Query_T, QueryResult_T]):
    @abstractmethod
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    @abstractmethod
    async def handle(self, query: Query_T) -> QueryResult_T: ...


QueryProcessorHandlers: TypeAlias = dict[type[Query], type[QueryHandler]]


class QueryProcessor:
    def __init__(self, handlers: QueryProcessorHandlers):
        self.__handlers = handlers

    async def process(
        self, executor: AsyncSession, query: Query[QueryResult_T]
    ) -> QueryResult_T:
        query_type = type(query)
        handler_type = self.__handlers.get(query_type)
        if not handler_type:
            raise ValueError(f"No handler found for query type {query_type}")

        handler = handler_type(executor)
        return await handler.handle(query)
