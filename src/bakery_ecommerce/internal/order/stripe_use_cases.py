from dataclasses import dataclass
import stripe
from bakery_ecommerce.internal.order.stripe_events import (
    StripeCreateOrderPaymentIntentEvent,
)


@dataclass
class StripeCreateOrderPaymentIntentResult:
    client_secret: str | None


class StripeCreateOrderPaymentIntent:
    async def execute(self, params: StripeCreateOrderPaymentIntentEvent):
        amount = params.order.items_price_multiplied()
        if amount < 100:
            raise ValueError("Payment intent require at least 100 amount")

        if params.order.payment_detail.payment_intent:
            result = await stripe.PaymentIntent.modify_async(
                params.order.payment_detail.payment_intent,
                amount=params.order.items_price_multiplied(),
            )
            return StripeCreateOrderPaymentIntentResult(result.client_secret)

        result = await stripe.PaymentIntent.create_async(
            amount=amount,
            # TODO: Different currency
            currency="usd",
            metadata={
                "payment_detail_id": str(params.order.payment_detail_id),
                "order_id": str(params.order.id),
                "user_id": str(params.user_id),
            },
        )

        return StripeCreateOrderPaymentIntentResult(result.client_secret)
