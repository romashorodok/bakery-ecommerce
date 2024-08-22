from typing import Self
from dataclasses import dataclass

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
