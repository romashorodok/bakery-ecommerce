from typing import Callable, Generic, Protocol, Any, Sequence, TypeVar


_COMPOSABLE_CONTEXT_T = TypeVar("_COMPOSABLE_CONTEXT_T")
_COMPOSABLE_ITEM_T = TypeVar("_COMPOSABLE_ITEM_T")

_REDUCEABLE_UNION_T = TypeVar("_REDUCEABLE_UNION_T", covariant=True)


def set_key(source: dict[str, Any], key: str, value: Any):
    source[key] = value


class ReduceableProtocol(Protocol[_REDUCEABLE_UNION_T]):
    def value(self) -> _REDUCEABLE_UNION_T: ...


class Composable(Generic[_COMPOSABLE_CONTEXT_T]):
    def __init__(self, root: _COMPOSABLE_CONTEXT_T) -> None:
        self.__root = root
        self.__reducers = dict[type, Callable[[_COMPOSABLE_CONTEXT_T, Any], None]]()

    def reducer(
        self,
        item_type: type[_COMPOSABLE_ITEM_T],
        reducer_fn: Callable[[_COMPOSABLE_CONTEXT_T, _COMPOSABLE_ITEM_T], None],
    ):
        self.__reducers[item_type] = reducer_fn

    def reduce(
        self, items: Sequence[ReduceableProtocol[_REDUCEABLE_UNION_T]]
    ) -> _COMPOSABLE_CONTEXT_T:
        for item in items:
            item_value = item.value()
            item_type = type(item_value)
            fn = self.__reducers[item_type]
            if fn:
                fn(self.__root, item_value)
        return self.__root
