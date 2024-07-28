import asyncio
import pytest

from dataclasses import dataclass

from bakery_ecommerce.context_bus import (
    ContextBus,
    ContextEventProtocol,
    ContextExecutor,
    ResultBox,
    impl_event,
)


@dataclass
class CustomPayload:
    value: int


@dataclass
@impl_event(ContextEventProtocol[CustomPayload])
class CustomPayloadCreated:
    _payload: CustomPayload

    @property
    def payload(self) -> CustomPayload:
        return self._payload


@dataclass
@impl_event(ContextEventProtocol[CustomPayload])
class CustomPayloadRead:
    _payload: CustomPayload

    @property
    def payload(self) -> CustomPayload:
        return self._payload


def num_gen():
    num = 0
    while True:
        yield num
        num += 1


class SafeGenerator:
    def __init__(self):
        self.gen = num_gen()
        self.lock = asyncio.Lock()

    async def get_next(self) -> int:
        async with self.lock:
            return next(self.gen)


@pytest.mark.asyncio
async def test_context_executors_with_dynamic_spawn():
    num_gen = SafeGenerator()

    async def spawn_task(num: int):
        n = await num_gen.get_next()
        if n > 5:
            return num

        await bus.publish(CustomPayloadCreated(CustomPayload(n)))
        return num

    async def read_task(num: int):
        await bus.publish(CustomPayloadRead(CustomPayload(num)))
        await asyncio.sleep(0.1)
        return None

    async def return_task(num: int):
        return num

    bus = ContextBus(
        {
            str(CustomPayloadCreated): [
                ContextExecutor(
                    CustomPayloadCreated, lambda payload: spawn_task(payload.value)
                ),
                ContextExecutor(
                    CustomPayloadCreated, lambda payload: read_task(payload.value)
                ),
            ],
            str(CustomPayloadRead): [
                ContextExecutor(
                    CustomPayloadRead, lambda payload: return_task(payload.value)
                ),
            ],
        }
    )

    num = await num_gen.get_next()

    await bus.publish(CustomPayloadCreated(CustomPayload(num)))

    result = await bus.gather()

    def check_valid_seq(input: list[ResultBox]):
        expect_seq = range(0, 5)

        for i in expect_seq:
            assert input[i].value() == i

    payload_created = result.items.get(str(CustomPayloadCreated))
    assert payload_created
    assert len(payload_created) == 6

    check_valid_seq(payload_created)

    payload_return = result.items.get(str(CustomPayloadRead))
    assert payload_return
    assert len(payload_return) == 6

    check_valid_seq(payload_return)

    print(result.items)
