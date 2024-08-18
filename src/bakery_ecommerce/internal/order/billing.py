from abc import ABC, abstractmethod
from typing import override

CENTS_MULTIPLIER = 100


class Billing(ABC):
    @abstractmethod
    def convert_price_to_price_with_cents(self, price: int) -> tuple[int, int]: ...


class StripeBilling(Billing):
    @override
    def convert_price_to_price_with_cents(self, price: int) -> tuple[int, int]:
        return price * CENTS_MULTIPLIER, CENTS_MULTIPLIER
