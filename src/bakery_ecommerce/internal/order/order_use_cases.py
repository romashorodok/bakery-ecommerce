from dataclasses import dataclass
from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus
from bakery_ecommerce.internal.order.order_events import (
    ChangePaymentMethodEvent,
    GetUserDraftOrderEvent,
    GetUserDraftOrderRetrievedEvent,
)
from bakery_ecommerce.internal.order.store.order_model import (
    Order,
    Order_Status_Enum,
    PaymentDetail,
)
from bakery_ecommerce.internal.store.crud_queries import CrudOperation, CustomBuilder
from bakery_ecommerce.internal.store.query import QueryProcessor


@dataclass
class GetUserDraftOrderResult:
    order: Order


class GetUserDraftOrder:
    def __init__(self, context: ContextBus, queries: QueryProcessor) -> None:
        self.__context = context
        self.__queries = queries

    async def execute(self, params: GetUserDraftOrderEvent) -> GetUserDraftOrderResult:
        async def query(session: AsyncSession) -> Order:
            stmt = select(Order).where(
                and_(
                    Order.user_id == params.user_id,
                    Order.order_status == Order_Status_Enum.DRAFT,
                ),
            )
            try:
                result = await session.execute(stmt)
                return result.scalar_one()
            except NoResultFound:
                order = Order()
                order.user_id = params.user_id
                order.order_status = Order_Status_Enum.DRAFT

                payment_detail = PaymentDetail()
                order.payment_detail = payment_detail

                session.add(order)
                await session.flush()
                return order
            except Exception as e:
                raise ValueError(f"Unable get or create order. Err: {e}")

        result = await self.__queries.process(params.session, CustomBuilder(query))
        await self.__context.publish(GetUserDraftOrderRetrievedEvent(order=result))
        return GetUserDraftOrderResult(result)


class NotModifiedPaymentProvider(HTTPException):
    def __init__(self, provider: str) -> None:
        super().__init__(
            304, f"Not modified payment provider. Current provider {provider}", None
        )


@dataclass
class ChangePaymentMethodResult:
    payment_detail: PaymentDetail | None


class ChangePaymentMethod:
    def __init__(self, queries: QueryProcessor) -> None:
        self.__queries = queries

    async def execute(self, params: ChangePaymentMethodEvent):
        if params.order.payment_detail.payment_provider == params.provider:
            raise NotModifiedPaymentProvider(params.provider)

        operation = CrudOperation(
            PaymentDetail,
            lambda q: q.update_partial(
                "id",
                params.order.payment_detail_id,
                {"payment_provider": params.provider},
            ),
        )
        result = await self.__queries.process(params.session, operation)
        return ChangePaymentMethodResult(result)
