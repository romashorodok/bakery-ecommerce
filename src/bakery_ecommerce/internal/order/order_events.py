from dataclasses import dataclass
from typing import Self
from uuid import UUID
from bakery_ecommerce.context_bus import (
    ContextEventProtocol,
    ContextPersistenceEvent,
    impl_event,
)
from bakery_ecommerce.internal.cart.store.cart_model import Cart
from bakery_ecommerce.internal.order.store.order_model import (
    Order,
    Payment_Provider_Enum,
)


@dataclass
@impl_event(ContextEventProtocol)
class GetUserDraftOrderEvent(ContextPersistenceEvent):
    user_id: UUID

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class UserDraftOrderRetrievedEvent:
    order: Order

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class ChangePaymentMethodEvent(ContextPersistenceEvent):
    order: Order
    provider: Payment_Provider_Enum

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class CartItemsToOrderItemsEvent(ContextPersistenceEvent):
    cart: Cart
    order: Order

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class CartItemsToOrderItemsConvertedEvent:
    order: Order | None

    @property
    def payload(self) -> Self:
        return self
