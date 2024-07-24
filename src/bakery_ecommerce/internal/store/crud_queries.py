from typing import (
    Any,
    Callable,
    Coroutine,
    Generic,
    TypeVar,
    override,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import query


class SnippetException(Exception):
    pass


class IntegrityConflictException(Exception):
    pass


class NotFoundException(Exception):
    pass


AsyncCrud_T = TypeVar("AsyncCrud_T")


class AsyncCrud(Generic[AsyncCrud_T]):
    def __init__(self, session: AsyncSession, model: type[AsyncCrud_T]) -> None:
        self.__model = model
        self.__session = session

    async def get_one_by_field(
        self,
        field: str = "id",
        value: Any = Any,
    ) -> AsyncCrud_T | None:
        try:
            stmt = select(self.__model).where(getattr(self.__model, field) == value)
        except AttributeError:
            raise SnippetException(
                f"Column {field} not found on {self.__model}.",
            )
        result = await self.__session.execute(stmt)
        return result.scalar_one_or_none()

    # async def get_many_by_field(self) -> list[AsyncCrud_T]: ...
    #
    # async def create(self) -> AsyncCrud_T: ...
    #
    # async def create_many(self) -> list[AsyncCrud_T]: ...
    #
    # async def remote_by_field(self) -> bool: ...


CrudQueryResult_T = TypeVar("CrudQueryResult_T")


class CrudOperation(query.Query[AsyncCrud_T], Generic[AsyncCrud_T]):
    def __init__(
        self,
        model: type[AsyncCrud_T],
        operation: Callable[[AsyncCrud[AsyncCrud_T]], Coroutine[Any, Any, AsyncCrud_T]],
    ) -> None:
        self.model = model
        self.operation = operation


class CrudOperationHandler(query.QueryHandler[CrudOperation[AsyncCrud_T], AsyncCrud_T]):
    @override
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    @override
    async def handle(self, query: CrudOperation[AsyncCrud_T]) -> AsyncCrud_T:
        return await query.operation(AsyncCrud(self.__executor, query.model))


# def CrudFactory(model: type[PersistanceBase]):
#     class AsyncCrud:
#         @classmethod
#         async def create(
#             cls,
#             session: AsyncSession,
#             data: BaseSchema,
#         ) -> PersistanceBase:
#             try:
#                 db_model = model(**data.model_dump())
#                 session.add(db_model)
#                 await session.commit()
#                 await session.refresh(db_model)
#                 return db_model
#             except IntegrityError:
#                 raise IntegrityConflictException(
#                     f"{model.__tablename__} conflicts with existing data.",
#                 )
#             except Exception as e:
#                 raise SnippetException(f"Unknown error occurred: {e}") from e
#
#         @classmethod
#         async def create_many(
#             cls,
#             session: AsyncSession,
#             data: list[BaseSchema],
#             return_models: bool = False,
#         ) -> list[PersistanceBase] | bool:
#             db_models = [model(**d.model_dump()) for d in data]
#             try:
#                 session.add_all(db_models)
#                 await session.commit()
#             except IntegrityError:
#                 raise IntegrityConflictException(
#                     f"{model.__tablename__} conflict with existing data.",
#                 )
#             except Exception as e:
#                 raise SnippetException(f"Unknown error occurred: {e}") from e
#
#             if not return_models:
#                 return True
#
#             for m in db_models:
#                 await session.refresh(m)
#
#             return db_models
#
#         @classmethod
#         async def get_one_by_id(
#             cls,
#             session: AsyncSession,
#             id_: str | UUID,
#             column: str = "id",
#             with_for_update: bool = False,
#         ) -> PersistanceBase | None:
#             try:
#                 q = select(model).where(getattr(model, column) == id_)
#             except AttributeError:
#                 raise SnippetException(
#                     f"Column {column} not found on {model.__tablename__}.",
#                 )
#
#             if with_for_update:
#                 q = q.with_for_update()
#
#             results = await session.execute(q)
#             return results.unique().scalar_one_or_none()
#
#         @classmethod
#         async def get_many_by_ids(
#             cls,
#             session: AsyncSession,
#             ids: list[str | UUID] | None = None,
#             column: str = "id",
#             with_for_update: bool = False,
#         ) -> Sequence[PersistanceBase]:
#             q = select(model)
#             if ids:
#                 try:
#                     q = q.where(getattr(model, column).in_(ids))
#                 except AttributeError:
#                     raise SnippetException(
#                         f"Column {column} not found on {model.__tablename__}.",
#                     )
#
#             if with_for_update:
#                 q = q.with_for_update()
#
#             rows = await session.execute(q)
#             return rows.unique().scalars().all()
#
#         @classmethod
#         async def update_by_id(
#             cls,
#             session: AsyncSession,
#             data: BaseSchema,
#             id_: str | UUID,
#             column: str = "id",
#         ) -> PersistanceBase:
#             db_model = await cls.get_one_by_id(
#                 session, id_, column=column, with_for_update=True
#             )
#             if not db_model:
#                 raise NotFoundException(
#                     f"{model.__tablename__} {column}={id_} not found.",
#                 )
#
#             values = data.model_dump(exclude_unset=True)
#             for k, v in values.items():
#                 setattr(db_model, k, v)
#
#             try:
#                 await session.commit()
#                 await session.refresh(db_model)
#                 return db_model
#             except IntegrityError:
#                 raise IntegrityConflictException(
#                     f"{model.__tablename__} {column}={id_} conflict with existing data.",
#                 )
#
#         @classmethod
#         async def update_many_by_ids(
#             cls,
#             session: AsyncSession,
#             updates: dict[str | UUID, BaseSchema],
#             column: str = "id",
#             return_models: bool = False,
#         ) -> Sequence[PersistanceBase] | bool:
#             updates = {str(id): update for id, update in updates.items() if update}
#             ids = list(updates.keys())
#             db_models = await cls.get_many_by_ids(
#                 session, ids=ids, column=column, with_for_update=True
#             )
#
#             for db_model in db_models:
#                 values = updates[str(getattr(db_model, column))].model_dump(
#                     exclude_unset=True
#                 )
#                 for k, v in values.items():
#                     setattr(db_model, k, v)
#                 session.add(db_model)
#
#             try:
#                 await session.commit()
#             except IntegrityError:
#                 raise IntegrityConflictException(
#                     f"{model.__tablename__} conflict with existing data.",
#                 )
#
#             if not return_models:
#                 return True
#
#             for db_model in db_models:
#                 await session.refresh(db_model)
#
#             return db_models
#
#         @classmethod
#         async def remove_by_id(
#             cls,
#             session: AsyncSession,
#             id_: str | UUID,
#             column: str = "id",
#         ) -> int:
#             try:
#                 query = delete(model).where(getattr(model, column) == id_)
#             except AttributeError:
#                 raise SnippetException(
#                     f"Column {column} not found on {model.__tablename__}.",
#                 )
#
#             rows = await session.execute(query)
#             await session.commit()
#             return rows.rowcount
#
#         @classmethod
#         async def remove_many_by_ids(
#             cls,
#             session: AsyncSession,
#             ids: list[str | UUID],
#             column: str = "id",
#         ) -> int:
#             if not ids:
#                 raise SnippetException("No ids provided.")
#
#             try:
#                 query = delete(model).where(getattr(model, column).in_(ids))
#             except AttributeError:
#                 raise SnippetException(
#                     f"Column {column} not found on {model.__tablename__}.",
#                 )
#
#             rows = await session.execute(query)
#             await session.commit()
#             return rows.rowcount
#
#     return AsyncCrud
