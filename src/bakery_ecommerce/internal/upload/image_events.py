from typing import Self
from dataclasses import dataclass
from uuid import UUID

from bakery_ecommerce.context_bus import (
    ContextEventProtocol,
    ContextPersistenceEvent,
    impl_event,
)


@dataclass
@impl_event(ContextEventProtocol)
class GetPresignedUrlEvent(ContextPersistenceEvent):
    image_hash: str

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class SubmitImageUploadEvent(ContextPersistenceEvent):
    image_hash: str
    image_id: UUID
    product_id: UUID

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class SetFeaturedProductImageEvent(ContextPersistenceEvent):
    product_id: UUID
    image_id: UUID

    @property
    def payload(self) -> Self:
        return self
