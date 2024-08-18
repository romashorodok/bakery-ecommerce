from dataclasses import dataclass
from typing import Self
from uuid import UUID

from bakery_ecommerce.context_bus import (
    ContextEventProtocol,
    ContextPersistenceEvent,
    impl_event,
)
from bakery_ecommerce.internal.cart.store.cart_model import Cart
from bakery_ecommerce.internal.store.persistence.product import Product


@dataclass
@impl_event(ContextEventProtocol)
class GetUserCartEvent(ContextPersistenceEvent):
    user_id: UUID

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class UserCartRetrievedEvent:
    cart: Cart

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class UserCartAddCartItemEvent(ContextPersistenceEvent):
    quantity: int
    user_id: UUID
    cart: Cart
    product: Product

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class UserCartDeleteCartItemEvent(ContextPersistenceEvent):
    cart: Cart
    product_id: UUID

    @property
    def payload(self) -> Self:
        return self
