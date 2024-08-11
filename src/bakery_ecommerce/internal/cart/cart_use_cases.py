from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.context_bus import ContextBus
from bakery_ecommerce.internal.cart.cart_events import (
    GetUserCartEvent,
    UserCartAddCartItemEvent,
    UserCartRetrievedEvent,
)
from bakery_ecommerce.internal.cart.store.cart_item_model import CartItem
from bakery_ecommerce.internal.cart.store.cart_model import Cart
from bakery_ecommerce.internal.store.crud_queries import CrudOperation, CustomBuilder
from bakery_ecommerce.internal.store.query import QueryProcessor


@dataclass
class GetUserCartResult:
    cart: Cart


class GetUserCart:
    def __init__(
        self, context: ContextBus, session: AsyncSession, queries: QueryProcessor
    ) -> None:
        self.__context = context
        self.__session = session
        self.__queries = queries

    async def execute(self, params: GetUserCartEvent) -> GetUserCartResult:
        async def query(session: AsyncSession) -> Cart:
            stmt = select(Cart).where(Cart.user_id == params.user_id)
            try:
                result = await session.execute(stmt)
                return result.unique().scalar_one()
            except NoResultFound:
                cart = Cart()
                cart.user_id = params.user_id
                session.add(cart)
                await session.flush()
                return cart
            except Exception as e:
                raise ValueError(f"Unable get or create cart. Err: {e}")

        result = await self.__queries.process(self.__session, CustomBuilder(query))
        await self.__context.publish(UserCartRetrievedEvent(result))
        return GetUserCartResult(result)


@dataclass
class UserCartAddCartItemResult:
    cart_item: CartItem


class ProductAlreadyInCart(Exception): ...


class UserCartAddCartItem:
    def __init__(self, session: AsyncSession, queries: QueryProcessor) -> None:
        self.__session = session
        self.__queries = queries

    async def execute(
        self, params: UserCartAddCartItemEvent
    ) -> UserCartAddCartItemResult:
        for cart_item in await params.cart.awaitable_attrs.cart_items:
            if cart_item.product_id == params.product.id:
                raise ProductAlreadyInCart("Product already in cart")

        cart_item = CartItem()
        cart_item.cart_id = params.cart.id
        cart_item.product_id = params.product.id
        cart_item.quantity = params.quantity

        result = await self.__queries.process(
            self.__session,
            CrudOperation(CartItem, lambda q: q.create_one(cart_item)),
        )
        return UserCartAddCartItemResult(result)
