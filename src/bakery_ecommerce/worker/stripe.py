from asyncio import sleep, Lock
import nats
from nats.aio.msg import Msg

from bakery_ecommerce.internal.store.session import DatabaseSessionManager
from bakery_ecommerce import dependencies


async def worker(
    consumer_name: str, nats_server: str, session_manager: DatabaseSessionManager
):
    lock = Lock()

    async def handler(msg: Msg):
        async with lock:
            print(
                "nats handler acquire",
            )
            subject = msg.subject
            reply = msg.reply
            data = msg.data.decode()
            print(
                "Received {consumer_name} a message on '{subject} {reply}' data: {data}".format(
                    subject=subject,
                    reply=reply,
                    consumer_name=consumer_name,
                    data=data,
                )
            )
            await msg.ack()

    async with await nats.connect(nats_server) as nc:
        print("start nats connection", nc, "nats_args", nats_server)
        js = nc.jetstream()

        config = dependencies.payments_stripe_consumer_config(consumer_name)

        sub = await js.subscribe_bind(
            stream="PAYMENTS",
            consumer=consumer_name,
            config=config,
            cb=handler,
            manual_ack=True,
        )

        await sleep(10)
        await sub.unsubscribe()

        async with lock:
            await nc.drain()
