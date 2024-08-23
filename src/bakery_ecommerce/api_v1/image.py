from typing import Annotated, Any
from uuid import UUID
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from nats.aio.client import Client as NATS

from bakery_ecommerce.composable import Composable, set_key
from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextExecutor,
)
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.upload.image_events import (
    GetPresignedUrlEvent,
    SetFeaturedProductImageEvent,
    SubmitImageUploadEvent,
)
from bakery_ecommerce.internal.upload.image_use_case import (
    GetPresignedUrl,
    GetPresignedUrlResult,
    SetFeaturedProductImage,
    SetFeaturedProductImageResult,
    SubmitImageUpload,
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


def submit_image_upload_request__context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
    nats: NATS = Depends(dependencies.request_nats_session),
) -> ContextBus:
    _submit_image_upload = SubmitImageUpload(queries, nats)
    return context | ContextExecutor(
        SubmitImageUploadEvent, _submit_image_upload.execute
    )


class SubmitImageUploadRequestBody(BaseModel):
    image_hash: str
    product_id: str


@api.post("/{image_id}/submit", dependencies=[Depends(verify_access_token)])
async def submit_image_upload(
    image_id: str,
    body: SubmitImageUploadRequestBody,
    context: Annotated[ContextBus, Depends(submit_image_upload_request__context_bus)],
):
    await context.publish(
        SubmitImageUploadEvent(
            image_id=UUID(image_id),
            image_hash=body.image_hash,
            product_id=UUID(body.product_id),
        )
    )
    await context.gather()
    return {"success": True}


def make_featured_image_request_context_bus(
    context: ContextBus = Depends(dependencies.request_context_bus),
    queries: QueryProcessor = Depends(dependencies.request_query_processor),
) -> ContextBus:
    _set_featured_product_image = SetFeaturedProductImage(queries)

    return context | ContextExecutor(
        SetFeaturedProductImageEvent, _set_featured_product_image.execute
    )


class MakeFeaturedImageRequestBody(BaseModel):
    product_id: str


@api.put("/{image_id}/featured", dependencies=[Depends(verify_access_token)])
async def make_featured_image(
    image_id: str,
    body: MakeFeaturedImageRequestBody,
    context: Annotated[ContextBus, Depends(make_featured_image_request_context_bus)],
):
    await context.publish(
        SetFeaturedProductImageEvent(
            image_id=UUID(image_id),
            product_id=UUID(body.product_id),
        )
    )

    result = await context.gather()
    cmp = Composable(dict[str, Any]())
    cmp.reducer(
        SetFeaturedProductImageResult,
        lambda resp, result: set_key(resp, "success", result.success),
    )
    return cmp.reduce(result.flatten())


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/images")
