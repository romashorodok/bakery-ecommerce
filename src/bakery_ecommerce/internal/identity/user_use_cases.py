from dataclasses import dataclass
from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal.store.query import QueryProcessor
from bakery_ecommerce.internal.store.crud_queries import CrudOperation
from bakery_ecommerce.context_bus import ContextBus, ContextEventProtocol, impl_event

from .store.user_model import User


@dataclass
@impl_event(ContextEventProtocol)
class UserValidPasswordEvent:
    is_valid: bool
    user: User

    @property
    def payload(self) -> Self:
        return self


@dataclass
@impl_event(ContextEventProtocol)
class ValidateUserPasswordEvent:
    email: str
    password: str

    @property
    def payload(self) -> Self:
        return self


class InvalidEmailError(Exception): ...


class InvalidPasswordHashError(Exception): ...


class ValidateUserPassword:
    def __init__(
        self, context: ContextBus, session: AsyncSession, queries: QueryProcessor
    ) -> None:
        self.__context = context
        self.__session = session
        self.__queries = queries

    async def execute(self, params: ValidateUserPasswordEvent):
        operation = CrudOperation(
            User, lambda q: q.get_one_by_field("email", params.email)
        )
        user = await self.__queries.process(self.__session, operation)

        if not user:
            raise InvalidEmailError("Not found user email")

        valid = user.validate_hash(params.password)
        if not valid:
            raise InvalidPasswordHashError("invalid user password")

        await self.__context.publish(UserValidPasswordEvent(valid, user))

        return valid


@dataclass
@impl_event(ContextEventProtocol[User])
class UserCreatedEvent:
    _payload: User

    @property
    def payload(self) -> User:
        return self._payload


@dataclass
@impl_event(ContextEventProtocol)
class CreateUserEvent:
    first_name: str
    last_name: str
    email: str
    password: str

    @property
    def payload(self) -> Self:
        return self


class CreateUser:
    def __init__(
        self, context: ContextBus, session: AsyncSession, queries: QueryProcessor
    ) -> None:
        self.__context = context
        self.__session = session
        self.__queries = queries

    async def execute(self, params: CreateUserEvent) -> User:
        model = User()
        model.first_name = params.first_name
        model.last_name = params.last_name
        model.email = params.email
        model.hash = params.password
        operation = CrudOperation(User, lambda q: q.create_one(model))

        try:
            model = await self.__queries.process(self.__session, operation)
            await self.__session.flush()
        except Exception as e:
            print("CreateUser use case. Err:", e)
            raise e

        await self.__context.publish(UserCreatedEvent(model))

        return model
