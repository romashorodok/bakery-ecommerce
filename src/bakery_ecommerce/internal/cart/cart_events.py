from dataclasses import dataclass
from typing import Self
from uuid import UUID

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.cart.store.cart_model import Cart
from bakery_ecommerce.internal.store.persistence.product import Product


@dataclass
@impl_event(ContextEventProtocol)
class GetUserCartEvent:
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
class UserCartAddCartItemEvent:
    quantity: int
    user_id: UUID
    cart: Cart
    product: Product

    @property
    def payload(self) -> Self:
        return self
