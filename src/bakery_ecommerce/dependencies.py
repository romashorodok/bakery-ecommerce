import asyncio
import contextlib
import os
import threading
from nats.js import JetStreamContext
from nats.js.api import (
    AckPolicy,
    ConsumerConfig,
    DeliverPolicy,
    DiscardPolicy,
    RetentionPolicy,
    StreamConfig,
)
from nats.js.errors import NotFoundError
import time
from typing import Any, Callable, Coroutine, TypeVar
import fastapi
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce import worker
from bakery_ecommerce.context_bus import ContextBus
from bakery_ecommerce.internal.catalog.store.catalog_queries import (
    NormalizeCatalogItemsPosition,
    NormalizeCatalogItemsPositionHandler,
)
from bakery_ecommerce.internal.identity.store.private_key_session_queries import (
    GetPrivateKeySignature,
    GetPrivateKeySignatureHandler,
)
from bakery_ecommerce.internal.store.join_queries import (
    JoinOperation,
    JoinOperationHandler,
)
from bakery_ecommerce.internal.store.query import (
    QueryCache,
    QueryProcessor,
    QueryProcessorHandlers,
)
from bakery_ecommerce.internal.store.session import (
    DatabaseSessionManager,
    PostgresDatabaseConfig,
)
from bakery_ecommerce.internal.store import crud_queries
from bakery_ecommerce.internal.store import product_queries

import nats
from nats.aio.client import Client as NATS

import stripe

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


nats_server = "nats://localhost:4222"


async def nats_session():
    async with await nats.connect(nats_server) as nc:
        yield nc


def request_nats_session(
    request: fastapi.Request, nc: NATS = fastapi.Depends(nats_session)
):
    return cache_request_attr(request, nc)


def start_loop(
    loop: asyncio.AbstractEventLoop,
    worker_f: Callable[[Any], Coroutine],
    delay: float = 2.0,
    *args,
):
    retries = 0
    while True:
        try:
            loop.run_until_complete(worker_f(*args))
        except Exception as e:
            if "Event loop stopped before Future completed" in str(e):
                print("Stop worker loop")
                break

            print(f"catch error in loop routine. Delay {delay}. {e}")
            time.sleep(delay)
        finally:
            retries += 1


def spawn_worker_thread(
    worker_f: Callable[..., Coroutine], *args
) -> tuple[asyncio.AbstractEventLoop, threading.Thread]:
    runner = asyncio.new_event_loop()
    thread = threading.Thread(target=start_loop, args=(runner, worker_f, 2.0, *args))
    return (runner, thread)


stripe_any_subject = "stripe.>"

payments_stream_config = StreamConfig(
    name="PAYMENTS",
    retention=RetentionPolicy.WORK_QUEUE,
    discard=DiscardPolicy.OLD,
    subjects=[
        stripe_any_subject,
    ],
)


def payments_stripe_consumer_config(consumer_name: str) -> ConsumerConfig:
    return ConsumerConfig(
        name=consumer_name,
        deliver_policy=DeliverPolicy.ALL,
        deliver_group="payments_stripe_group_0",
        deliver_subject="stripe",
        ack_policy=AckPolicy.EXPLICIT,
    )


async def get_or_create_stream(js: JetStreamContext, config: StreamConfig):
    if not config.name:
        raise ValueError("Stream config must have a name")

    try:
        stream = await js.stream_info(config.name)
        stream = await js.update_stream(payments_stream_config)
    except NotFoundError as e:
        print(f"not found stream {e}", type(e))
        stream = await js.add_stream(payments_stream_config)

    return stream


async def get_or_create_consumer(
    js: JetStreamContext, stream_config: StreamConfig, consumer_config: ConsumerConfig
):
    if not consumer_config.name or not stream_config.name:
        raise ValueError("Requere stream_config.name and consumer_config.name")

    try:
        consumer = await js.consumer_info(stream_config.name, consumer_config.name, 1)
    except Exception as e:
        print(f"not found consumer {e}", type(e))
        consumer = await js.add_consumer(stream_config.name, consumer_config, 1)

    return consumer


@contextlib.asynccontextmanager
async def lifespan(_: fastapi.FastAPI):
    async with await nats.connect(nats_server) as nc:
        js = nc.jetstream()
        await get_or_create_stream(js, payments_stream_config)
        await get_or_create_consumer(
            js,
            payments_stream_config,
            payments_stripe_consumer_config("payments_stripe_consumer_0"),
        )

    stripe_secret_key = os.environ.get("STRIPE_SECRET_KEY")
    print("Use stripe secret key:", stripe_secret_key)
    stripe.api_key = stripe_secret_key

    stripe_runner, stripe_thread = spawn_worker_thread(
        worker.stripe.worker, "payments_stripe_consumer_1", nats_server, session_manager
    )
    stripe_thread.start()

    stripe_runner_2, stripe_thread_2 = spawn_worker_thread(
        worker.stripe.worker, "payments_stripe_consumer_2", nats_server, session_manager
    )
    stripe_thread_2.start()

    yield

    stripe_runner_2.call_soon_threadsafe(stripe_runner_2.stop)
    stripe_thread_2.join()

    stripe_runner.call_soon_threadsafe(stripe_runner.stop)
    stripe_thread.join()

    if not session_manager.is_closed():
        await session_manager.close()


query_handlers = QueryProcessorHandlers(
    {
        crud_queries.CrudOperation: crud_queries.CrudOperationHandler,
        crud_queries.CustomBuilder: crud_queries.CustomBuilderHandler,
        product_queries.FindProductByName: product_queries.FindProductByNameHandler,
        GetPrivateKeySignature: GetPrivateKeySignatureHandler,
        JoinOperation: JoinOperationHandler,
        NormalizeCatalogItemsPosition: NormalizeCatalogItemsPositionHandler,
    }
)


def query_processor(nats: NATS = fastapi.Depends(request_nats_session)):
    yield QueryProcessor(query_handlers, QueryCache(nats))


def request_query_processor(
    request: fastapi.Request,
    queries: QueryProcessor = fastapi.Depends(query_processor),
) -> QueryProcessor:
    return cache_request_attr(request, queries)


def request_context_bus(request: fastapi.Request) -> ContextBus:
    return cache_request_attr(request, ContextBus(session_manager.session_maker()))
