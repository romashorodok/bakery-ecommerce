from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bakery_ecommerce.internal.store.query import Query, QueryHandler

_JOIN_T = TypeVar("_JOIN_T", covariant=True)


class JoinRoot(Generic[_JOIN_T]):
    def __init__(self, model: type[_JOIN_T], field: str) -> None:
        self.model = model
        self.field = getattr(model, field)
        self.objects = set[_JOIN_T]()

    def add_model(self, model: Any):
        self.objects.add(model)

    def __repr__(self) -> str:
        return f"{self.objects}"


class JoinOn(Generic[_JOIN_T]):
    def __init__(self, model: type[_JOIN_T], field: str, root_field: Any) -> None:
        self.model = model
        self.field = getattr(model, field)
        self.root_field = root_field
        self.objects = set[_JOIN_T]()

    def add_model(self, model: Any):
        self.objects.add(model)

    def __repr__(self) -> str:
        return f"{self.objects}"


_JOIN_RESULT_T = TypeVar("_JOIN_RESULT_T")

_JOIN_CHECK_T = TypeVar("_JOIN_CHECK_T")


class JoinResult(Generic[_JOIN_RESULT_T]):
    def __init__(self, container: dict[str, list[_JOIN_RESULT_T]]) -> None:
        self.__container = container

    # TODO: the type of _JOIN_T is covariant which mean when I return it will be a union set of types not a conconcrete
    def get(self, t: type[_JOIN_RESULT_T]) -> list[_JOIN_RESULT_T] | None:
        return self.__container.get(str(t))

    def get_strict(self, t: type[_JOIN_CHECK_T]) -> list[_JOIN_CHECK_T]:
        data = self.get(t)  # pyright: ignore
        if not data or len(data) == 0:
            raise ValueError(f"JoinResult not found {str(t)}")

        return data  # pyright: ignore

    def __repr__(self) -> str:
        return f"{self.__container}"


@dataclass
class JoinOperation(Query[JoinResult[_JOIN_T]]):
    join_root: JoinRoot[_JOIN_T]
    join_on: dict[type[_JOIN_T], JoinOn[_JOIN_T]]
    where_value: Any | None


class JoinOperationHandler(QueryHandler[JoinOperation, JoinResult[_JOIN_T]]):
    def __init__(self, executor: AsyncSession) -> None:
        self.__executor = executor

    async def handle(self, query: JoinOperation) -> JoinResult[_JOIN_T]:
        join_on_models = map(lambda m: m.model, query.join_on.values())

        stmt = select(query.join_root.model, *join_on_models)

        for join_model in query.join_on.values():
            stmt = stmt.outerjoin(
                join_model.model,
                join_model.field
                == getattr(query.join_root.model, join_model.root_field),
            )

        if query.where_value:
            stmt = stmt.where(query.join_root.field == query.where_value)

        rows = await self.__executor.execute(stmt)
        rows = rows.unique()

        for row in rows:
            for i in row:
                model_type = type(i)

                if query.join_root.model == model_type:
                    query.join_root.add_model(i)

                if join_on := query.join_on.get(model_type):
                    if join_on.model == model_type:
                        join_on.add_model(i)

        result = dict[str, list[_JOIN_T]](
            {str(query.join_root.model): [*query.join_root.objects]}
        )

        for join_model in query.join_on.values():
            result[str(join_model.model)] = [*join_model.objects]

        return JoinResult(result)
