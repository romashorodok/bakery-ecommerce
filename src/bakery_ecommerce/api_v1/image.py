from typing import Annotated, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import ContextBus, ContextExecutor
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.upload.image_events import GetPresignedUrlEvent
from bakery_ecommerce.internal.upload.image_use_case import (
    GetPresignedUrl,
    GetPresignedUrlResult,
)
from bakery_ecommerce.object_store import ObjectStore
from bakery_ecommerce.token_middleware import verify_access_token
from bakery_ecommerce import dependencies

api = APIRouter()


def upload_image_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
    object_store: ObjectStore = Depends(dependencies.request_object_store),
) -> ContextBus:
    _get_presigned_url = GetPresignedUrl(queries, object_store)
    return context | ContextExecutor(GetPresignedUrlEvent, _get_presigned_url.execute)


class UploadImageRequestBody(BaseModel):
    image_hash: str


@api.post("/", dependencies=[Depends(verify_access_token)])
async def upload_image(
    body: UploadImageRequestBody,
    context: Annotated[ContextBus, Depends(upload_image_request__context_bus)],
):
    await context.publish(
        GetPresignedUrlEvent(
            body.image_hash,
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        GetPresignedUrlResult,
        lambda resp, result: set_key(resp, "image", result),
    )
    return cmp.reduce(result.flatten())


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/images")
