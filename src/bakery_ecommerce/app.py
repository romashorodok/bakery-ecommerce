import contextlib
from typing import Annotated, TypeAlias
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal import store
from bakery_ecommerce.internal.store import persistence


session_manager = store.session.DatabaseSessionManager(
    # TODO: Get from config/env
    store.session.PostgresDatabaseConfig().get_uri()
)


async def get_session():
    async with session_manager.session() as session:
        yield session


async def get_transaction():
    async with session_manager.tx() as tx:
        yield tx


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI):
    yield
    if not session_manager.is_closed():
        await session_manager.close()


QueryProcessorSesssion: TypeAlias = store.query.QueryProcessor


async def get_query_processor():
    handlers = store.query.QueryProcessorHandlers(
        {
            store.product_queries.FindProductByName: store.product_queries.FindProductByNameHandler,
            store.crud_queries.CrudOperation: store.crud_queries.CrudOperationHandler,
        }
    )
    yield store.query.QueryProcessor(handlers)


app = fastapi.FastAPI(
    lifespan=lifespan,
)


@app.get("/test")
async def test(
    db: Annotated[AsyncSession, fastapi.Depends(get_session)],
    # tx: Annotated[AsyncSession, fastapi.Depends(get_transaction)],
    queries: Annotated[QueryProcessorSesssion, fastapi.Depends(get_query_processor)],
):
    query = store.crud_queries.CrudOperation(
        persistence.product.Product,
        lambda q: q.get_one_by_field("name", "test"),
    )

    result = await queries.process(
        db,
        query,
    )
    print("query result", result, type(result))

    # crud_handler = store.crud_queries.CrudOperationHandler(session)
    #
    # result = await crud_handler.handle(query)

    # result_tx = await queries.process(
    #     tx, store.product_queries.FindProductByName("test")
    # )
    # result_sess = await queries.process(
    #     session, store.product_queries.FindProductByName("test")
    # )
    # print(result_tx)
    # print(result_sess)
    pass


# __api_v1 = fastapi.APIRouter(prefix="/api/v1")
# api_v1.product.register_handler(__api_v1)
# app.include_router(__api_v1)
