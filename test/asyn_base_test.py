import asyncio
from functools import wraps
from time import monotonic, sleep


def some_wrapper(f):
    @wraps(f)
    async def inner(*args, **kwargs):
        start = monotonic()
        if asyncio.iscoroutinefunction(f):
            res = await f(*args, **kwargs)
        else:
            res = f(*args, **kwargs)
        duration = monotonic() - start
        return res, duration
    return inner


@some_wrapper
async def plus_async(x, y):
    await asyncio.sleep(1.0)
    return x + y


@some_wrapper
def minus_sync(x, y):
    sleep(1)  # attention ! it blocks the whole thread !
    return x - y


async def async_main():
    print(*await plus_async(5, 5))
    print(await asyncio.gather(plus_async(4, 4), plus_async(2, 2)))
    print(await asyncio.create_task(plus_async(1, 1)))
    print(await minus_sync(9, 9))


if __name__ == '__main__':
    asyncio.run(async_main())