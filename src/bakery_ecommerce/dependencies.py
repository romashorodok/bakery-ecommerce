import contextlib
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal import product, store

session_manager = store.session.DatabaseSessionManager(
    store.session.PostgresDatabaseConfig().get_uri()
)


async def transaction():
    async with session_manager.tx() as tx:
        yield tx


async def session():
    async with session_manager.session() as session:
        yield session


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI):
    yield
    if not session_manager.is_closed():
        await session_manager.close()


query_handlers = store.query.QueryProcessorHandlers(
    {
        store.crud_queries.CrudOperation: store.crud_queries.CrudOperationHandler,
        store.crud_queries.CustomBuilder: store.crud_queries.CustomBuilderHandler,
        store.product_queries.FindProductByName: store.product_queries.FindProductByNameHandler,
    }
)


def query_processor():
    yield store.query.QueryProcessor(query_handlers)


def get_product_by_name(
    session: AsyncSession = fastapi.Depends(transaction),
    queries: store.query.QueryProcessor = fastapi.Depends(query_processor),
):
    yield product.GetProductByName(session, queries)


def create_product(
    session: AsyncSession = fastapi.Depends(session),
    queries: store.query.QueryProcessor = fastapi.Depends(query_processor),
):
    yield product.CreateProduct(session, queries)


def get_product_list(
    session: AsyncSession = fastapi.Depends(session),
    queries: store.query.QueryProcessor = fastapi.Depends(query_processor),
):
    yield product.GetProductList(session, queries)
