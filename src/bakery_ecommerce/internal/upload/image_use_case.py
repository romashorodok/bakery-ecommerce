from dataclasses import dataclass
from uuid import uuid4
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal.store.crud_queries import CustomBuilder
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.upload.image_events import GetPresignedUrlEvent
from bakery_ecommerce.internal.upload.store.iamge_model import Image
from bakery_ecommerce.object_store import ObjectStore


class ImageAlreadyUploadedError(HTTPException):
    def __init__(self, image: Image) -> None:
        super().__init__(
            409, "Image already uploaded. Delete it first or use existed", None
        )
        self.image = image


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
            row = await params.session.execute(stmt)
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
        if image.submited:
            raise ImageAlreadyUploadedError(image)

        self.__object_store.connect()
        url = self.__object_store.get_presigned_put_url(
            bucket=image.bucket,
            file=image.original_file,
        )
        return GetPresignedUrlResult(url, image.id)
