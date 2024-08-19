from dataclasses import dataclass
from uuid import UUID

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.order.store.order_model import Order


@dataclass
@impl_event(ContextEventProtocol)
class StripeCreateOrderPaymentIntentEvent:
    order: Order
    user_id: UUID

    @property
    def payload(self):
        return self
