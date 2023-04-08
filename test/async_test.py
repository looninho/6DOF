python -m asyncio

import time 
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.pdu import ExceptionResponse

async_client=AsyncModbusSerialClient(
    port="COM7", # /dev/ttyUSB0
    framer=ModbusRtuFramer,
    baudrate=115200,
    bytesize=8,
    parity="O",
    stopbits=1,
    strict=False                      
)

def to_signed_int(nums:list)->list:
    signed_int=[]
    for num in nums:
        # convert to 32-bit signed integer
        if num & (1 << 15):
            num = -((num ^ 0xffff) + 1)
        signed_int.append(num)
    return signed_int


await async_client.connect()

rr = await async_client.read_holding_registers(356, 8, slave=1)

async def read_signed_values(client:AsyncModbusSerialClient, slave:int,  mb_addr:int, count:int=1)->list:
    rr = await client.read_holding_registers(mb_addr, count, slave=slave)
    return to_signed_int(rr.registers)

async def refresh_alarm(client):
    alarm_vals = await read_signed_values(client, 1, 356, 8)
    alarm_vals += await read_signed_values(client, 1, 364, 2)
    return alarm_vals

async def refresh_mon(client):
    monitor_vals = []
    for i in range(3):
        monitor_vals += await read_signed_values(client, 1, 368+i*8, 8)
    monitor_vals += await read_signed_values(client, 1, 368+3*8, 5)
    return monitor_vals

async def display_refresh(client, rate:int, timeout_secondes:float=5.0):
    loop = asyncio.get_running_loop()
    end_time = loop.time() + timeout_secondes
    while True:
        # print("Alarm:", await refresh_alarm(client))
        # print("Monitor:", await refresh_mon(client))
        await refresh_alarm(client)
        await refresh_mon(client)
        if (loop.time() + 1.0) >= end_time:
            break
        await asyncio.sleep(1/rate)

await display_refresh(client, 400, 5) # 400 Hz

############################################
background_tasks = set()
task1 = asyncio.create_task(refresh_alarm(client))
background_tasks.add(task1)
task1.add_done_callback(background_tasks.discard)

task2 = asyncio.create_task(refresh_mon(client))
background_tasks.add(task2)
task2.add_done_callback(background_tasks.discard)

async def main(client):
    task1 = asyncio.create_task(
        refresh_alarm(client))
    task2 = asyncio.create_task(
        refresh_mon(client))
    print(f"started at {time.strftime('%X')}")
    # Wait until both tasks are completed (should take
    await task1
    await task2
    print(f"finished at {time.strftime('%X')}")

# asyncio.run(main(client))
await main(client)

##############################################""

import asyncio
import logging

from pymodbus.client import AsyncModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.pdu import ExceptionResponse

_logger = logging.getLogger()

async def run_async_client(client, modbus_calls=None):
    """Run sync client."""
    _logger.info("### Client starting")
    await client.connect()
    assert client.connected
    if modbus_calls:
        rr = await modbus_calls(client)
    # await client.close()
    _logger.info("### End of Program")
    return rr.registers
    
async def _handle_holding_registers(client):
    """Read/write holding registers."""
    _logger.info("### write holding register and read holding registers")
    rr = await client.read_holding_registers(0, 8, slave=1)
    return rr

async def run_async_calls(client):
    rr = await _handle_holding_registers(client)
    return rr

def _check_call(rr):
    """Check modbus call worked generically."""
    assert not rr.isError()  # test that call was OK
    assert not isinstance(rr, ExceptionResponse)  # Device rejected request
    return rr

class Async_AASD:
    def __init__(self, client:AsyncModbusSerialClient):
        self.client=client
        
    def read_settings(self, slave:int=1, addr:int=0, count:int=8):
        rr = self.client.read_holding_registers(addr, count, slave=slave)
        return rr.registers

async def test(client):
    await client.connect()
    rr = await client.read_holding_registers(0,8,slave=1)
    return rr.registers

asyncio.run(test(client), debug=True)


async def connect(client):
    await client.connect()
    return client.connected

async def connected(client):
    return client.connected


async def a_read(client:AsyncModbusSerialClient, slave:int, addr:int, count:int=1):
    # await client.connect()
    # assert client.connected
    # rr = await client.read_holding_registers(addr, count, slave=slave)
    # return to_signed_int(rr.registers)
    return await client.read_holding_registers(addr, count, slave=slave)

background_tasks = set()

for i in range(3):
    task = asyncio.create_task(a_read(client, 1, 356+i*8, 8))
    # Add task to the set. This creates a strong reference.
    background_tasks.add(task)
    # To prevent keeping references to finished tasks forever,
    # make each task remove its own reference from the set after
    # completion:
    task.add_done_callback(background_tasks.discard)

async def main():
    # Nothing happens if we just call "nested()".
    # A coroutine object is created but not awaited,
    # so it *won't run at all*.
    a_read(client, 1, 356, 8)
    # Let's do it differently now and await it:
    print(await a_read(client, 1, 356, 8))

asyncio.run(a_read(client, 1, 356, 8))

asyncio.run(a_read(client, 1, 368, 8))

asyncio.run(main(client))


asyncio.run(connected(client))

asyncio.run(connect(client))

if __name__ == "__main__":
    client=AsyncModbusSerialClient(
        port="COM7", # /dev/ttyUSB0
        framer=ModbusRtuFramer,
        baudrate=115200,
        bytesize=8,
        parity="O",
        stopbits=1,
        strict=False                      
    )
    
    asyncio.run(run_async_client(client, modbus_calls=run_async_calls), debug=True)
    
    # background_tasks = set()
    
    # for i in range(10):
    #     task = asyncio.create_task(some_coro(param=i))
        
    #     # Add task to the set. This creates a strong reference.
    # background_tasks.add(task)

    # # To prevent keeping references to finished tasks forever,
    # # make each task remove its own reference from the set after
    # # completion:
    # task.add_done_callback(background_tasks.discard)
    
