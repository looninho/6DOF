# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:        async_pyaasd.py
# Purpose:     Serial asynchronous client driver for communicating with AASD-15A,
#              
#
# Notes:       
# Authors of original Code:   Luan Nguyen (2023)
# Copyright:   (c) Luan Nguyen
# Licence:     GPL-3.0
# Website:     
#-----------------------------------------------------------------------------

#https://pymodbus.readthedocs.io/en/latest/source/example/asynchronous_asyncio_serial_client.html?highlight=read%20coils#asynchronous-asyncio-serial-client-example
#await, write to a Coil and read back
#await, write to multiple Coils and read back

# from serial.tools.list_ports import comports
import asyncio
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.pdu import ExceptionResponse

# User parameter mode (Pn) operation
# address 0000H..00ECH or 0..236 (dec): Pn000..Pn236 (read-write)

# Auxiliaire mode (Fn) operation
# address 0164H..016DH or 356..365 (dec): Fn000..Pn236 (read only)

# Monitoring mode (Dn) operation
# address 0000H..00ECH or 368..396 (dec): Dn000..Dn028 (write only)

NUMBER_MOTORS = 6

def read_16bits(val) -> str:
    """Convert val to binary representation.

    Args:
        val (int): unsigned integer

    Returns:
        str: bin representation of val
    """    
    return bin(val).replace('0b', '').zfill(15)

def to_32bit_signed(num:int) -> int:
    """_summary_

    Args:
        num (int): _description_

    Returns:
        int: _description_
    """    
    if num & (1 << 15):
        num = -((num ^ 0xffff) + 1)
    return num
 
async def run_async_client(client, modbus_calls=None):
    """Run sync client."""
    # _logger.info("### Client starting")
    await client.connect()
    assert client.connected
    if modbus_calls:
        await modbus_calls(client)
    await client.close()
    # _logger.info("### End of Program")

def _check_call(rr):
    """Check modbus call worked generically."""
    assert not rr.isError()  # test that call was OK
    assert not isinstance(rr, ExceptionResponse)  # Device rejected request
    return rr

# ? Should use it
class ErrorStatus(Exception):
    """ Example:
    ```python
    raise ErrorStatus('blabla...')
    ```
    """
    pass

client = AsyncModbusSerialClient(
    port="COM7",
    framer=ModbusRtuFramer,
    baudrate=115200,
    bytesize=8,
    parity="O",
    stopbits=1,
    strict=False
)

async def run_async_calls(client):
    await read_system_config(client)
    await read_PC_config(client)
    await read_SC_config(client)
    await read_TC_config(client)
    await read_extended_config(client)

async def read_system_config(client):
    rr = _check_call(await client.read_holding_registers(0, 8, slave=1))
    assert len(rr.bits) == 8
    # return rr.registers

async def read_PC_config(client):
    rr = _check_call(await client.read_holding_registers(96, 8, slave=1))
    assert len(rr.bits) == 8
    # return rr.registers

async def read_SC_config(client):
    rr = _check_call(await client.read_holding_registers(146, 8, slave=1))
    assert len(rr.bits) == 8
    # return rr.registers

async def read_TC_config(client):
    rr = _check_call(await client.read_holding_registers(186, 8, slave=1))
    assert len(rr.bits) == 8
    # return rr.registers

async def read_extended_config(client):
    rr = _check_call(await client.read_holding_registers(216, 8, slave=1))
    assert len(rr.bits) == 8
    # return rr.registers

async def foo(client):
    rr = await client.read_holding_registers(0, 8, slave=1)
    return rr.registers


asyncio.run(run_async_client(client, modbus_calls=run_async_calls))

class Async_AASD_15A:
    """Serial asynchronous AC Servo Driver for AC Servo Motor model 80ST-M02430LB
    """    
    def __init__(self, port:str, framer=ModbusRtuFramer, baudrate=115200, bytesize=8, parity="O", stopbits=1, strict=False):
        self.controller = AsyncModbusSerialClient(
            port=port,
            framer=framer,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            strict=strict       
        )
                
    async def read_config(self):
        
    async def read(self, servo_number:int, mb_addr:int, count:int=1) -> int:
        """read parameter at address mb_addr for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address to read value
            count (int, optional): number of registers to read. Default to 1.

        Returns:
            int: signed integer value
        """        
        rr = await self.controller.read_holding_registers(mb_addr, count, slave=servo_number)
        # num = rr.getRegister(0)
        nums = rr.registers
        # convert to 32-bit signed integer
        for idx, item in enumerate(nums):
            nums[idx] = to_32bit_signed(item)
        return nums

    async def write_noconvert(self, servo_number:int, mb_addr:int, val:int) -> None:
        """Write without checking signed value val to parameter at mb_addr for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address (Pn) to write value.
            val (int): signed integer
        """        
        # signed integer to unsigned
        await self.controller.write_register(mb_addr, val, slave=servo_number)        
        
    async def write(self, servo_number:int, mb_addr:int, val:int, signed=True) -> None:
        """Write with checking signed value val to parameter at mb_addr for servo_number.
        
        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address (Pn) to write value.
            val (int): signed integer
            signed (bool, optional): if value is a signed integer. Defaults to True.
        """        
        # signed integer to unsigned
        usval = val & 0xffff if signed else val
        await self.write_register(mb_addr, usval, slave=servo_number)

    async def write2(self, servo_number:int, addr_start:int, val1:int, val2:int, signed=True) -> None:
        """Write 2 consecutive addresses with checking signed values val to parameter at addr_start and addr_start +1 
        for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            addr_start (int): start modbus address (Pn) to write to.
            val1 (int): signed integer. Value to write to addr_start
            val2 (int): signed integer. Value to write to addr_start + 1
            signed (bool, optional): if value is a signed integer. Defaults to True.
        """        
        # signed integer to unsigned
        usval1 = val1 & 0xffff if signed else val1
        usval2 = val2 & 0xffff if signed else val2
        await self.controller.write_registers(addr_start, [usval1, usval2], slave=servo_number)
        
    async def change_bitN(self, servo_number:int, Pn:int, bit_pos:int, value=1) -> bool:
        """Change bitN value of register 1 or 2 (see Pn070 and Pn071)

        Args:
            servo_number (int): servo motor number (see Pn065).
            Pn (int): modbus address of register
            bit_pos (int): bit position N
            value (int, optional): 0 or 1. Defaults to 1.

        Returns:
            bool: True if successful else False
        """        
        # val =  await self.read(servo_number, Pn)[0] # int number
        rr = _check_call(await self.controller.read_holding_registers(Pn, 1, slave=servo_number))
        val = rr.registers[0]
        register = read_16bits(val) # bin format
        list_reg = list(register) # convert to list to change bit10
        list_reg[15-bit_pos-1]=str(value) # set bit10 to value 1 (default)
        reg=''
        for elm in list_reg:
            reg += elm
        val = int(reg, 2) # re-convert to int
        # _check_call(await self.write_noconvert(servo_number, Pn, val))
        _check_call(await self.controller.write_register(Pn, val, slave=servo_number)) # val=0~32767 & 0xffff
        rr = _check_call(await self.controller.read_holding_registers(Pn, 1, slave=servo_number))
        valr = rr.registers[0]
        return val == valr

    async def trigger(self, servo_number:int, raising=True) -> int:
        """Trigger servo_number movement. If raising=True, trigger is raising edge.
        Trigger BIT10 of register 2 (Pn071)

        Args:
            servo_number (int): servo motor number (see Pn065).
            raising (bool, optional): trigger is raising (True) or falling (False). Defaults to True.

        Returns:
            int: 0
        """        
        Pn, bit_pos=71, 10
        # val =  self.read(servo_number, Pn)
        rr = await self.controller.read_holding_registers(Pn, 1, slave=servo_number)
        val = rr.registers[0]
        register = read_16bits(val)
        list_reg = list(register)
        if raising:
            if list_reg[15-bit_pos-1]=='1':
                await self.change_bitN(Pn, bit_pos, 0)
            else:
                await self.change_bitN(servo_number, Pn, bit_pos, 1)
        else:
            if list_reg[15-bit_pos-1]=='0':
                await self.change_bitN(servo_number, Pn, bit_pos, 1)
            else:
                await self.change_bitN(servo_number, Pn, bit_pos, 0)
        return 0
    
    async def set_motor_code(self, servo_number:int, value:int=4) -> bool:
        """This is Pn001 function for writing. Effect after driver reboot.

        Args:
            servo_number (int): servo motor number (see Pn065).
            value (int, optional): 0..70. Defaults to 4 (80ST-M02430 motor).
            
        Returns:
            bool: True if successful else False
        """        
        # self.write_noconvert(servo_number, 1, value)
        _check_call(await self.controller.write_register(1, value, slave=servo_number)) # value=0~70
        rr = _check_call(await self.controller.read_holding_registers(1, 1, slave=servo_number))
        print("Please reboot the servo motor for taking effect. For permanent write set manually Fn001")
        return rr.registers[0] == value
        
    async def set_control_mode(self, servo_number:int, value:int=2) -> bool:
        """Set control mode. Effect after driver reboot.

        Args:
            servo_number (int): servo motor number (see Pn065).
            value (int, optional): setting mode value 0..5. Defaults to 2.
                0: Torque mode,
                1: Speed mode,
                2: Position mode,
                3: Position / speed mode,
                4: Position / torque mode,
                5: Speed / torque mode
                
        Returns:
            bool: True if successful else False
        """     
        # self.write_noconvert(servo_number, 2, value)
        _check_call(await self.controller.write_register(2, value, slave=servo_number)) # value=0~70
        rr = _check_call(await self.controller.read_holding_registers(2, 1, slave=servo_number))
        print("Please reboot the servo motor for taking effect. For permanent write set manually Fn001")
        return rr.registers[0] == value
    
    async def set_enable_motor(self, servo_number:int, enable:bool=True) -> bool:
        """Enable motor (Pn003)

        Args:
            servo_number (int): servo motor number (see Pn065).
            enable (bool, optional): Defaults to True.
                True: Automatically enable drive after power on.
                False: the SON (servo ON) enable drive from the input port SigIn
            
        Returns:
            bool: True if successful else False
        """  
        # self.write_noconvert(servo_number, 1) if enable else self.write_noconvert(servo_number, 0)  
        value = 1 if enable else 0
        _check_call(await self.controller.write_register(3, value, slave=servo_number)) # value=0~1
        rr = _check_call(await self.controller.read_holding_registers(3, 1, slave=servo_number))
        return rr.registers[0] == value
            
    async def allow_internal_control(self, servo_number:int, allow:bool=True) -> bool:
        """Pn069. System settings for internal instruction mode.
        write input fonction control register 2 (Pn069) to allow internal control of SigIn Ptrigger (Bit10)

        Args:
            servo_number (int): servo motor number (see Pn065).
            allow (bool, optional): _description_. Defaults to True.
            
        Returns:
            bool: True if successful else False
        """
        Pn, bit_pos = 69, 10
        if allow:
            return await self.change_bitN(servo_number, Pn, bit_pos, 1)
        else:
            return await self.change_bitN(servo_number, Pn, bit_pos, 0)
    
    async def set_PM_logic_direction(self, servo_number:int, clockwise:bool=False) -> bool:
        """Position mode Pn097. Set direction CCW (default) when enter a ppsitive command.

        Args:
            servo_number (int): servo motor number (see Pn065).
            clockwise (bool, optional): CCW or CW. Defaults to False (CCW).
            
        Returns:
            bool: True if successful else False
        """
        # self.write_noconvert(servo_number, 97, 1) if clockwise else self.write_noconvert(servo_number, 97, 0)
        value = 1 if clockwise else 0
        _check_call(await self.controller.write_register(97, value, slave=servo_number)) # value=0~1
        rr = _check_call(await self.controller.read_holding_registers(97, 1, slave=servo_number))
        return rr.registers[0] == value
        
    async def reverse(self, servo_number:int, reverse:bool=False) -> bool:
        """Same as `set_PM_logic_direction`.
        By default the motor rotates in CCW when you are facing the motor shaft.
        To reverse this direction set reverse=True.

        Args:
            servo_number (int): servo motor number (see Pn065).
            reverse (bool): False: CCW, True: CW. Defaults to False (CCW).
            
        Returns:
            bool: True if successful else False
        """    
        return await self.set_PM_logic_direction(servo_number, clockwise=reverse)
            
    async def set_PM_electronic_gear_ratio(self, servo_number:int, gear_ratio:int, cell:int=4) -> bool:
        """Position mode Pn098~Pn101. Set the electronic gear ratio for cell N.
        The cell number is determined by Gn1, Gn2.
        
        #TODO: check Gn1, Gn2 (Pn071) to see which cell is selected. Default is cell 4 (Pn101)

        Args:
            servo_number (int): servo motor number (see Pn065).
            gear_ratio (int): 1~32767. see appendix electronic gear ratio calculation.
            cell (int): 1~4. Default to 4. 1 is Pn098,.., 4 is Pn101.
            
        Returns:
            bool: True if successful else False
        """
        assert cell in range(1,5)
        assert gear_ratio in range(1, 32768)
        Pn=97+cell # Pn098~Pn101
        # self.write_noconvert(servo_number, Pn, gear_ratio)
        _check_call(await self.controller.write_register(Pn, gear_ratio, slave=servo_number)) # value=0~1
        rr = _check_call(await self.controller.read_holding_registers(Pn, 1, slave=servo_number))
        return rr.registers[0] == gear_ratio
        
    async def set_PM_accel_decel_mode(self, servo_number:int, function_nb:int=2) -> bool:
        """Position mode Pn109.Set function filter for acceleration and deceleration mode.

        Args:
            servo_number (int): servo motor number (see Pn065).
            function_nb (int, optional): 0~2. Defaults to 2. 0: no filtering, 1: smooth one time, 2: S-curve.
        """        
        # self.write_noconvert(servo_number, 109, function_nb)
        _check_call(await self.controller.write_register(109, function_nb, slave=servo_number)) # value=0~1
        rr = _check_call(await self.controller.read_holding_registers(109, 1, slave=servo_number))
        return rr.registers[0] == function_nb
        
    async def set_PM_command_source_selection(self, servo_number:int, source:int=2) -> bool:
        """Position mode Pn117. Select source for position command.
        Internal is RS485, external is pulse input.

        Args:
            servo_number (int): servo motor number (see Pn065).
            source (int, optional): 0~3. Defaults to 2 (internal if SigIn Psourec=1).
        """        
        # self.write_noconvert(servo_number, 117, source)
        _check_call(await self.controller.write_register(117, source, slave=servo_number)) # value=0~1
        rr = _check_call(await self.controller.read_holding_registers(117, 1, slave=servo_number))
        print("Please reboot the servo motor for taking effect. For permanent write set manually Fn001")
        return rr.registers[0] == source
        
    async def set_PM_move(self, servo_number:int, n_high:int, n_low:int, internal_cmd:int=0, trigger=True) -> bool:
        """Position mode Pn120~Pn127. Set motor position and trigger the movement.
        Args:
            servo_number (int): _description_
            n_high (int): -9999~9999: number of circles.
            n_low (int): -9999~9999: e.g. 5000 is half the circle.
            internal_cmd (int, optional): 0~3 Determined by Pos1, Pos2 values see Pn071. Defaults to 0.
        """        
        assert internal_cmd in range(4)
        Pn=120+2*internal_cmd
        # self.write2(servo_number, Pn, n_high, n_low)
        await self.controller.write_registers(Pn, [n_high & 0xffff, n_low & 0xffff], slave=servo_number)
        if trigger:
            return await self.trigger(servo_number)
        return False # motor did'nt move


        
    

        
          
