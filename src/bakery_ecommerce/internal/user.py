from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal import store
from bakery_ecommerce.internal.store import persistence


@dataclass
class CreateUserParams:
    pass


class CreateUser:
    def __init__(
        self, session: AsyncSession, queries: store.query.QueryProcessor
    ) -> None:
        self.__queries = queries
        self.__session = session

    async def execute(self, params: CreateUserParams):
        user = persistence.user.User
