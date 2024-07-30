import contextlib
from typing import TypeVar
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus
from bakery_ecommerce.internal.store.query import (
    QueryProcessor,
    QueryProcessorHandlers,
)
from bakery_ecommerce.internal.store.session import (
    DatabaseSessionManager,
    PostgresDatabaseConfig,
)
from bakery_ecommerce.internal.store import crud_queries
from bakery_ecommerce.internal.store import product_queries


REQUEST_ATTR_T = TypeVar("REQUEST_ATTR_T")


def cache_request_attr(
    request: fastapi.Request, attr: REQUEST_ATTR_T
) -> REQUEST_ATTR_T:
    attr_type = str(type(attr))
    if not hasattr(request.state, attr_type):
        request.state._state[attr_type] = attr
    return request.state._state[attr_type]


session_manager = DatabaseSessionManager(PostgresDatabaseConfig().get_uri())


async def transaction():
    async with session_manager.tx() as tx:
        print("run transaction")
        yield tx
    print("out of transaction")


def request_transaction(
    request: fastapi.Request, tx: AsyncSession = fastapi.Depends(transaction)
) -> AsyncSession:
    return cache_request_attr(request, tx)


async def session():
    async with session_manager.session() as session:
        yield session


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI):
    yield
    if not session_manager.is_closed():
        await session_manager.close()


query_handlers = QueryProcessorHandlers(
    {
        crud_queries.CrudOperation: crud_queries.CrudOperationHandler,
        crud_queries.CustomBuilder: crud_queries.CustomBuilderHandler,
        product_queries.FindProductByName: product_queries.FindProductByNameHandler,
    }
)


def query_processor():
    yield QueryProcessor(query_handlers)


def request_query_processor(
    request: fastapi.Request,
    queries: QueryProcessor = fastapi.Depends(query_processor),
) -> QueryProcessor:
    return cache_request_attr(request, queries)


def request_context_bus(request: fastapi.Request) -> ContextBus:
    return cache_request_attr(request, ContextBus())
