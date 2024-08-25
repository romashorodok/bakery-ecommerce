import asyncio
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from nats.aio.msg import Msg

from bakery_ecommerce.internal.store.crud_queries import CrudOperation
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.store.session import DatabaseSessionManager
from bakery_ecommerce.internal.upload.store.image_model import Image as ModelImage
from bakery_ecommerce.nats_subjects import ProductImageTranscodingRequired
from bakery_ecommerce.object_store import ObjectStore

from PIL import Image

chunk_size = 1024

MIME_TYPE = "webp"
PILLOW_MIME_TYPE_FORMAT = "WebP"


def transcode_image_file(object_store: ObjectStore, bucket: str, file: str) -> str:
    resp = object_store.get_file(bucket, file)

    file_data = BytesIO()

    with resp:
        for chunk in resp.stream(chunk_size * 4):
            file_data.write(chunk)

    resp.close()
    resp.release_conn()

    file_data.seek(0)

    # transcoded_file = f"{uuid4()}.{MIME_TYPE}"
    transcoded_file = f"{file}.{MIME_TYPE}"

    with Image.open(file_data) as image:
        transcoded_data = BytesIO()
        image.save(transcoded_data, format=PILLOW_MIME_TYPE_FORMAT)
        transcoded_data.seek(0)
        object_store.put_bytes(
            bucket,
            transcoded_file,
            transcoded_data,
            transcoded_data.getbuffer().nbytes,
        )

    return transcoded_file


async def product_image_transcoding_handler(
    msg: Msg,
    queries: QueryProcessor,
    session_manager: DatabaseSessionManager,
    object_store: ObjectStore,
):
    subject = ProductImageTranscodingRequired.from_bytes(msg.data)

    async with session_manager.tx() as session:
        image = await queries.process(
            session,
            CrudOperation(
                ModelImage,
                lambda q: q.get_one_by_field("id", subject.image_id),
            ),
        )
        if not image:
            raise ValueError(f"not found image: {subject.image_id}")

        if image.transcoded_file:
            print(f"Already transcoded image: {subject.image_id}")
            await msg.ack()

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, object_store.connect)
            transcoded_file = await loop.run_in_executor(
                pool,
                transcode_image_file,
                object_store,
                image.bucket,
                image.original_file,
            )
        await queries.process(
            session,
            CrudOperation(
                ModelImage,
                lambda q: q.update_partial(
                    "id",
                    image.id,
                    {
                        "transcoded_file": transcoded_file,
                        "transcoded_file_mime": MIME_TYPE,
                    },
                ),
            ),
        )

    print("recv product_image", queries, session_manager, object_store)
    await msg.ack()
