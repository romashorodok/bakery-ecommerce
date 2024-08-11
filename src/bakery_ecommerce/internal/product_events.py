from dataclasses import dataclass
from typing import Self

from bakery_ecommerce.context_bus import ContextEventProtocol, impl_event
from bakery_ecommerce.internal.store.persistence.product import Product


@dataclass
@impl_event(ContextEventProtocol)
class ProductByIdRetrievedEvent:
    product: Product

    @property
    def payload(self) -> Self:
        return self
