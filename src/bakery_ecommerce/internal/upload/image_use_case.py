from dataclasses import dataclass
from uuid import uuid4
import uuid
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import case

from nats.aio.client import Client as NATS

from bakery_ecommerce.internal.store.crud_queries import (
    CustomBuilder,
)
from bakery_ecommerce.internal.store.persistence.product import ProductImage
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.upload.image_events import (
    GetPresignedUrlEvent,
    SetFeaturedProductImageEvent,
    SubmitImageUploadEvent,
)
from bakery_ecommerce.internal.upload.store.image_model import Image
from bakery_ecommerce.object_store import ObjectStore
from bakery_ecommerce import dependencies
from bakery_ecommerce import nats_subjects


@dataclass
class GetPresignedUrlResult:
    upload_url: str
    id: uuid.UUID


class GetPresignedUrl:
    def __init__(self, queries: QueryProcessor, object_store: ObjectStore) -> None:
        self.__queries = queries
        self.__object_store = object_store

    async def execute(self, params: GetPresignedUrlEvent):
        async def get_or_create_query(session: AsyncSession):
            stmt = select(Image).where(Image.original_file_hash == params.image_hash)
            row = await session.execute(stmt)
            result = row.unique().scalar()
            if result:
                return result

            image = Image()
            image.original_file_hash = params.image_hash
            image.original_file = str(uuid4())
            image.bucket = str(uuid4())
            session.add(image)
            await session.flush()
            return image

        image = await self.__queries.process(
            params.session, CustomBuilder(get_or_create_query)
        )
        if not image:
            raise ValueError(f"Not found image of the hash {params.image_hash}")

        self.__object_store.connect()
        url = self.__object_store.get_presigned_put_url(
            bucket=image.bucket,
            file=image.original_file,
        )
        return GetPresignedUrlResult(url, image.id)


@dataclass
class SubmitImageUploadResult:
    product_image: ProductImage


class SubmitImageUpload:
    def __init__(self, queries: QueryProcessor, nats: NATS) -> None:
        self.__queries = queries
        self.__nats = nats

    async def execute(self, params: SubmitImageUploadEvent):
        async def get_or_create_query(session: AsyncSession):
            stmt = select(ProductImage).where(
                and_(
                    ProductImage.product_id == params.product_id,
                    ProductImage.image_id == params.image_id,
                )
            )
            row = await session.execute(stmt)
            result = row.unique().scalar()
            if result:
                return result

            product_image = ProductImage()
            product_image.product_id = params.product_id
            product_image.image_id = params.image_id
            session.add(product_image)
            await session.flush()
            return product_image

        product_image = await self.__queries.process(
            params.session, CustomBuilder(get_or_create_query)
        )

        js = self.__nats.jetstream()
        await js.publish(
            dependencies.product_image_transcoding_required_subject(
                str(product_image.id),
            ),
            nats_subjects.ProductImageTranscodingRequired(
                image_id=str(product_image.image_id),
            ).to_bytes(),
            stream=dependencies.product_images_transcoding_stream_config.name,
        )

        return SubmitImageUploadResult(product_image)


@dataclass
class SetFeaturedProductImageResult:
    success: bool


class SetFeaturedProductImage:
    def __init__(self, queries: QueryProcessor) -> None:
        self.__queries = queries

    async def execute(self, params: SetFeaturedProductImageEvent):
        async def query(session: AsyncSession):
            stmt = (
                update(ProductImage)
                .where(ProductImage.product_id == params.product_id)
                .values(
                    featured=case(
                        (ProductImage.image_id == params.image_id, True), else_=False
                    )
                )
            )
            result = await session.execute(stmt)
            return result.rowcount > 0

        result = await self.__queries.process(params.session, CustomBuilder(query))
        return SetFeaturedProductImageResult(result)
