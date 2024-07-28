import inspect
from typing import Coroutine, Generic, Protocol, Any, TypeVar, Type, Callable

import asyncio

EventPayload_T = TypeVar("EventPayload_T", covariant=True)


class ContextEventProtocol(Protocol[EventPayload_T]):
    @property
    def payload(self) -> EventPayload_T: ...


_HandlerReturn_T = TypeVar("_HandlerReturn_T", bound=Any)


class ContextExecutor(Generic[_HandlerReturn_T]):
    def __init__(
        self,
        event_type: type[ContextEventProtocol[EventPayload_T]],
        handler: Callable[[EventPayload_T], Coroutine[Any, Any, _HandlerReturn_T]],
    ) -> None:
        self.event_type = event_type
        self.handler = handler

    def start(self, event: ContextEventProtocol, loop: asyncio.AbstractEventLoop):
        self.task = loop.create_task(self.handler(event.payload))
        return self.task


class ResultBox(Generic[_HandlerReturn_T]):
    def __init__(self, value: _HandlerReturn_T) -> None:
        self._value = value

    def value(self) -> _HandlerReturn_T:
        return self._value

    def __repr__(self) -> str:
        return f"ResultBox(value={self._value})"


class Result(Generic[_HandlerReturn_T]):
    def __init__(self, items: dict[str, list[ResultBox[_HandlerReturn_T]]]) -> None:
        self.items = items

    def flatten(self) -> list[ResultBox[_HandlerReturn_T]]:
        flattened_list = [item for sublist in self.items.values() for item in sublist]
        return flattened_list


# Compensating Actions: Define undo actions for each step to handle failures gracefully.
# Error Handling: Implement error handling to trigger compensating actions and manage the overall state of the Saga.
# TODO: use NATS based
class ContextBus(Generic[_HandlerReturn_T]):
    def __init__(
        self, executors: dict[str, list[ContextExecutor[_HandlerReturn_T]]]
    ) -> None:
        self.__executors = executors
        self.__tasks = asyncio.Queue[tuple[str, list[asyncio.Task[_HandlerReturn_T]]]]()
        self.__lock = asyncio.Lock()

    async def publish(self, event: ContextEventProtocol):
        event_type_str = str(type(event))
        async with self.__lock:
            if executors := self.__executors.get(event_type_str):
                tasks = list[asyncio.Task[_HandlerReturn_T]]()
                for executor in executors:
                    tasks.append(executor.start(event, asyncio.get_running_loop()))
                await self.__tasks.put((event_type_str, tasks))

    async def gather(self) -> Result[_HandlerReturn_T]:
        results: dict[str, list[ResultBox[_HandlerReturn_T]]] = {}

        while True:
            event: tuple[str, list[asyncio.Task[_HandlerReturn_T]]] | None = None

            async with self.__lock:
                if not self.__tasks.empty():
                    event = await self.__tasks.get()

            if event:
                event_type_str, tasks = event
                try:
                    completed = await asyncio.gather(*tasks)
                except Exception as e:
                    print(f"Exception occurred at event context bus: {e}")
                    completed = []

                if event_type_str not in results:
                    results[event_type_str] = []

                for result in completed:
                    if result is not None:
                        results[event_type_str].append(ResultBox(result))

            if self.__tasks.empty():
                break

        return Result(results)


__ignore_protocol_member = ["copy_with"]


def impl_event(protocol: Type):
    def decorator(cls):
        protocol_members = {
            member
            for member in dir(protocol)
            if not (member.startswith("__") and member.endswith("__"))
            and not member.startswith("_")
            and member not in __ignore_protocol_member
        }

        cls_members = {member for member in dir(cls)}
        if not protocol_members.issubset(cls_members):
            missing_members = protocol_members - cls_members
            raise TypeError(
                f"Class {cls.__name__} is missing members required by the protocol: {missing_members}"
            )

        for member in protocol_members:
            protocol_member = getattr(protocol, member, None)
            cls_member = getattr(cls, member, None)
            if protocol_member is None or cls_member is None:
                continue

            if callable(protocol_member):
                if not callable(cls_member):
                    raise TypeError(
                        f"Member '{member}' in class '{cls.__name__}' should be callable as required by the protocol."
                    )
                protocol_member_sig = inspect.signature(protocol_member)
                cls_member_sig = inspect.signature(cls_member)
                if protocol_member_sig != cls_member_sig:
                    raise TypeError(
                        f"Signature of member '{member}' in class '{cls.__name__}' does not match the protocol."
                    )
            elif isinstance(protocol_member, property):
                if not isinstance(cls_member, property):
                    raise TypeError(
                        f"Member '{member}' in class '{cls.__name__}' should be a property as required by the protocol."
                    )

        return cls

    return decorator
