from typing import Annotated, TypedDict
from fastapi import APIRouter, Depends, HTTPException, Request

from bakery_ecommerce import dependencies
from bakery_ecommerce.internal.identity.token import Token
from bakery_ecommerce.token_middleware import verify_access_token

from pydantic import BaseModel

from nats.aio.client import Client as NATS

import stripe

api = APIRouter()


class StripeObject(TypedDict):
    id: str


class StripeData(TypedDict):
    object: StripeObject


class StripeRequest(BaseModel):
    type: str
    api_version: str
    data: StripeData


@api.post("/stripe/webhook")
async def stripe_webhook_handler(
    request: Request,
    body: StripeRequest,
    nats: Annotated[NATS, Depends(dependencies.request_nats_session)],
):
    payload = await request.body()
    stripe_signature = request.headers.get("stripe-signature")

    js = nats.jetstream()

    # t = body.type
    # print("body type", t)

    result = await js.publish(
        subject=f"stripe.{body.type}.{body.data['object']['id']}",
        stream="PAYMENTS",
        payload=payload,
    )

    # "payments.stripe."
    # print(body)
    # print(stripe_signature)


@api.post("/stripe/payment-intent", dependencies=[Depends(verify_access_token)])
async def stripe_create_payment_intent(
    token: Annotated[Token, Depends(verify_access_token)],
):
    # TODO: On this stage i should create order and store payment intent ??
    # TODO: validate if stored payment intent use correct price and items
    print("user token", token)
    print("user_id", token.user_id())
    user_id = token.user_id()
    if not user_id:
        raise HTTPException(status_code=401, detail="Not found access_tokne user_id")

    # "stripe.payment_intent.created.pi_3PoA5DAgTou10Ln80l8s5ql3

    intent = await stripe.PaymentIntent.create_async(
        amount=100,
        currency="usd",
        metadata={
            "user_id": str(user_id),
        },
    )

    return intent


def register_handler(router: APIRouter):
    router.include_router(api, prefix="/payments")
