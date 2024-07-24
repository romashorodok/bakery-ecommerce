from dataclasses import dataclass, field
from enum import IntEnum
from .scalar import ScalarID


@dataclass
class Ingredient(ScalarID):
    name: str


@dataclass
class Inventory(ScalarID):
    quantity_in_fridge: int
    quantity_in_bakery: int
    quantity_baked: int


@dataclass
class Product(ScalarID):
    name: str
    base_price: int
    description: str


class OrderStatus(IntEnum):
    DRAFT = 0
    PROGRESS = 1
    APPROVED = 2
    CANCELLED = 3


@dataclass
class OrderItem(ScalarID):
    quantity: int


@dataclass
class Order(ScalarID):
    order_status: OrderStatus = field(default=OrderStatus.DRAFT)
    order_items: list[OrderItem] = field(default_factory=list[OrderItem])

    def calculate_tax(self) -> int: ...
