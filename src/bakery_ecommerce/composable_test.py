from bakery_ecommerce.composable import Composable


class Container:
    counter = 0


class Stub: ...


class Box:
    def __init__(self, value) -> None:
        self._value = value

    def value(self):
        return self._value


def test_reduce_list_of_types():
    context = Container()

    cmp = Composable(context)

    def check_int(ctx, item):
        assert isinstance(item, int)
        assert item == 10
        ctx.counter += 1

    cmp.reducer(int, check_int)

    def check_stub(ctx, stub):
        assert isinstance(stub, Stub)
        ctx.counter += 1

    cmp.reducer(Stub, check_stub)

    context = cmp.reduce([Box(Stub()), Box(Stub()), Box(10)])

    assert context.counter == 3
