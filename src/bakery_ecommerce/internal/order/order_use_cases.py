from dataclasses import dataclass
from typing import Any, Sequence, TypedDict
from uuid import UUID
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus
from bakery_ecommerce.internal.cart.store.cart_item_model import CartItem
from bakery_ecommerce.internal.identity.store.user_model import User
from bakery_ecommerce.internal.order.billing import Billing
from bakery_ecommerce.internal.order.order_events import (
    CartItemsToOrderItemsConvertedEvent,
    CartItemsToOrderItemsEvent,
    ChangePaymentMethodEvent,
    GetOrdersEvent,
    GetUserDraftOrderEvent,
    GetUserOrdersEvent,
    UserDraftOrderRetrievedEvent,
)
from bakery_ecommerce.internal.order.store.order_model import (
    Order,
    Order_Status_Enum,
    OrderItem,
    PaymentDetail,
)
from bakery_ecommerce.internal.store.crud_queries import (
    CrudOperation,
    CustomBuilder,
)
from bakery_ecommerce.internal.store.join_queries import (
    JoinOn,
    JoinOperation,
    JoinRoot,
)
from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.utils import get_model_dict


@dataclass
class Customer:
    first_name: str
    last_name: str
    email: str


class OrderWithCustomer(TypedDict):
    order: dict[str, Any]
    customer: Customer | None


@dataclass
class GetOrdersResult:
    orders_with_customers: list[OrderWithCustomer]


class GetOrders:
    def __init__(self, queries: QueryProcessor) -> None:
        self.__queries = queries

    async def execute(self, params: GetOrdersEvent) -> GetOrdersResult:
        operation = JoinOperation(
            where_value=None,
            join_root=JoinRoot(model=Order, field="id"),
            join_on={User: JoinOn(model=User, field="id", root_field="user_id")},
        )
        result = await self.__queries.process(params.session, operation)

        orders = result.get_strict(Order)
        users = {user.id: user for user in result.get_strict(User)}

        orders_with_customers = list[OrderWithCustomer]()

        for order in orders:
            user = users.get(order.user_id)
            customer: Customer | None = None
            if user:
                customer = Customer(user.first_name, user.last_name, user.email)

            orders_with_customers.append(
                OrderWithCustomer(
                    order=order.to_dict(),
                    customer=customer,
                )
            )

        return GetOrdersResult(orders_with_customers)


@dataclass
class GetUserOrdersResult:
    orders: Sequence[Order]


class GetUserOrders:
    def __init__(self, queries: QueryProcessor) -> None:
        self.__queries = queries

    async def execute(self, params: GetUserOrdersEvent) -> GetUserOrdersResult:
        async def query(session: AsyncSession) -> Sequence[Order]:
            stmt = (
                select(Order)
                .where(
                    and_(
                        Order.user_id == params.user_id,
                        Order.order_status != Order_Status_Enum.DRAFT,
                    )
                )
                .limit(params.page_size)
                .offset(params.page)
            )
            result = await session.execute(stmt)
            return result.unique().scalars().all()

        result = await self.__queries.process(params.session, CustomBuilder(query))
        return GetUserOrdersResult(result)


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
                return result.unique().scalar_one()
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
        await self.__context.publish(UserDraftOrderRetrievedEvent(order=result))
        return GetUserDraftOrderResult(result)


@dataclass
class ChangePaymentMethodResult:
    payment_detail: PaymentDetail | None


class ChangePaymentMethod:
    def __init__(self, queries: QueryProcessor) -> None:
        self.__queries = queries

    async def execute(self, params: ChangePaymentMethodEvent):
        print("Change Provider", params.provider)

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


class EmptyCartItemsError(HTTPException):
    def __init__(self) -> None:
        super().__init__(400, "Cart is empty. Cannot proceed with checkout.", None)


@dataclass
class CartItemsToOrderItemsResult:
    order: Order | None


class CartItemsToOrderItems:
    def __init__(
        self, context: ContextBus, queries: QueryProcessor, billing: Billing
    ) -> None:
        self.__context = context
        self.__queries = queries
        self.__billing = billing

    async def execute(self, params: CartItemsToOrderItemsEvent):
        cart_items = params.cart.cart_items
        if len(cart_items) == 0:
            raise EmptyCartItemsError()

        await self.__sanitize_order_items(
            params.session, params.order.order_items, cart_items
        )
        await params.session.flush()

        await self.__create_or_update_order_items(
            params.session, params.order, cart_items
        )

        await params.session.flush()
        result = await self.__queries.process(
            params.session,
            CrudOperation(Order, lambda q: q.get_one_by_field("id", params.order.id)),
        )
        await self.__context.publish(CartItemsToOrderItemsConvertedEvent(result))
        return CartItemsToOrderItemsResult(result)

    async def __create_or_update_order_items(
        self,
        session: AsyncSession,
        order: Order,
        cart_items: list[CartItem],
    ):
        existing_order_items = {i.product_id: i for i in order.order_items}

        for cart_item in cart_items:
            if cart_item.product_id in existing_order_items:
                order_item = existing_order_items[cart_item.product_id]
                order_item.quantity = cart_item.quantity
                order_item.price = cart_item.product.price

                price_multiplied, price_multiplier = (
                    self.__billing.convert_price_to_price_with_cents(order_item.price)
                )
                order_item.price_multiplied = price_multiplied
                order_item.price_multiplier = price_multiplier

                order_item_dict = get_model_dict(order_item)
                operation = CrudOperation(
                    OrderItem,
                    lambda q: q.update_partial("id", order_item.id, order_item_dict),
                )
                await self.__queries.process(session, operation)
            else:
                order_item = OrderItem()
                order_item.order_id = order.id
                order_item.product_id = cart_item.product_id

                order_item.price = cart_item.product.price
                order_item.quantity = cart_item.quantity

                price_multiplied, price_multiplier = (
                    self.__billing.convert_price_to_price_with_cents(order_item.price)
                )
                order_item.price_multiplied = price_multiplied
                order_item.price_multiplier = price_multiplier
                session.add(order_item)

    async def __sanitize_order_items(
        self,
        session: AsyncSession,
        order_items: list[OrderItem],
        cart_items: list[CartItem],
    ):
        cart_product_ids = set(map(lambda i: i.product_id, cart_items))
        items_ids_to_delete: list[UUID] = []

        for order_item in order_items:
            if order_item.product_id not in cart_product_ids:
                items_ids_to_delete.append(order_item.id)

        if items_ids_to_delete:
            await self.__queries.process(
                session,
                CrudOperation(
                    OrderItem,
                    lambda q: q.remove_many_by_field("id", items_ids_to_delete),
                ),
            )
