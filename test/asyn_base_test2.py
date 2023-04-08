import asyncio
from functools import wraps
from time import monotonic, sleep


class DecorateAsyncio(type):

    def __new__(cls, name, bases, local):
        for attr in local:
            value = local[attr]
            if callable(value):
                local[attr] = DecorateAsyncio._some_wrapper(value)

        return type.__new__(cls, name, bases, local)

    @staticmethod
    def _some_wrapper(f):
        @wraps(f)
        # we need self here to exclude errors related to number of arguments
        # since we gonna decorate instance level methods
        async def inner(self, *args, **kwargs):
            start = monotonic()
            if asyncio.iscoroutinefunction(f):
                res = await f(*args, **kwargs)
            else:
                res = f(*args, **kwargs)
            duration = monotonic() - start
            return res, duration

        return inner


class SomeClass(metaclass=DecorateAsyncio):
    async def plus_async(x, y):
        await asyncio.sleep(1.0)
        return x + y

    def minus_sync(x, y):
        sleep(1)  # attention ! it blocks the whole thread !
        return x - y


async def async_main():
    s = SomeClass()
    print(await s.plus_async(5, 5))
    print(await asyncio.gather(s.plus_async(4, 4), s.plus_async(2, 2)))
    print(await asyncio.create_task(s.plus_async(1, 1)))
    print(await s.minus_sync(9, 9))


if __name__ == '__main__':
    asyncio.run(async_main())