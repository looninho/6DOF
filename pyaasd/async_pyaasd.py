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
import os, sys

import asyncio
from pymodbus.client import AsyncModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.pdu import ExceptionResponse

import numpy as np

# User parameter mode (Pn) operation
# address 0000H..00ECH or 0..236 (dec): Pn000..Pn236 (read-write)

# Auxiliaire mode (Fn) operation
# address 0164H..016DH or 356..365 (dec): Fn000..Pn236 (read only)

# Monitoring mode (Dn) operation
# address 0000H..00ECH or 368..396 (dec): Dn000..Dn028 (write only)

NUMBER_MOTORS = 6

def read_16bits(val, fill:int) -> str:
    """Convert val to binary representation.

    Args:
        val (int): unsigned integer

    Returns:
        str: bin representation of val
    """    
    return bin(val).replace('0b', '').zfill(15)

def to_signed_int(nums:list)->list:
    signed_int=[]
    for num in nums:
        # convert to 32-bit signed integer
        if num & (1 << 15):
            num = -((num ^ 0xffff) + 1)
        signed_int.append(num)
    return signed_int

def read_signed_values(client:ModbusSerialClient, slave:int,  mb_addr:int, count:int=1)->list:
    rr = client.read_holding_registers(mb_addr, count, slave=slave)
    return to_signed_int(rr.registers)

def parse_values(keys:list, values:list)-> dict:
    d={}    
    for k, v in zip(keys, values):
        d[k]=v
    return d

# ? Should use it
class ErrorStatus(Exception):
    """ Example:
    ```python
    raise ErrorStatus('blabla...')
    ```
    """
    pass

class Sync_AASD_Alarm:
    """modbus addresses from 356 to 365 for Fn000 to view Sn0~Sn9, read only.
    The larger the Sn (serial number) of the alarm, the ealier the alarm occurs.
    Sn0 is the most recent alarm.
    There are 46 alarms: AL-01~AL-46
    """    
    def __init__(self, client:ModbusSerialClient):
        self.client=client
    
    def refresh(self, servo_number:int) -> list:
        alarm_vals=read_signed_values(self.client, servo_number, 356, 8)
        alarm_vals.append(read_signed_values(self.client, servo_number, 364, 2))
        self.keys=['Sn-'+str(i+1) for i in range(10)]
        self.parameters = parse_values(self.keys, alarm_vals)
        return 0
    
    def speed_command(self, servo_number:int):
        if hasattr(self, "parameters"):
            addr = 357
            self.parameters[self.keys[addr-356]] = read_signed_values(self.client, servo_number, addr, 1)[0]
            return self.parameters[self.keys[addr-356]]

    def torque_average(self, servo_number:int):
        if hasattr(self, "parameters"):
            addr = 358
            self.parameters[self.keys[addr-356]] = read_signed_values(self.client, servo_number, addr, 1)[0]
            return self.parameters[self.keys[addr-356]]

    def position_deviation(self, servo_number:int):
        if hasattr(self, "parameters"):
            addr = 359
            self.parameters[self.keys[addr-356]] = read_signed_values(self.client, servo_number, addr, 1)[0]
            return self.parameters[self.keys[addr-356]]

class Sync_AASD_Monitor:
    """modbus addresses from 368 to 396 for Dn000 to Dn028, read only
    """    
    def __init__(self, client:ModbusSerialClient):
        self.client=client
    
    def refresh(self, servo_number:int) -> list:
        """read all
        """ 
        keys = ['display', 'speed command', 'torque average', 'position deviation', 
                'AC power supply voltage', 'max instantaneous torque', 'pulse input frequency',
                'radiator temperature', 'current motor speed', 
                'input instruction pulse accumulated low value', 'input instruction pulse accumulated high value', 
                'encoder position feedback pulse accumulated low value', 'encoder position feedback pulse accumulated high value',
                'regenerative braking load rate', 'input port signal status',
                'output port signal status', 'torque analog voltage', 'speed analog voltage',
                'output register', 'feedback pulse low value', 'feedback pulse high value',
                'version', 'UVW encoder signals', 'rotor absolute position',
                'driver type', 'absolute encoder single loop data low',
                'absolute encoder single loop data high',
                'absolute encoder multi loop data low',
                'absolute encoder mulyi loop data high'
                ]
        # units = ['', 'r/min', '%', 'Volt', '%', 'kHz", "°C', 'r/min', '']
        monitor_vals = []
        for i in range(3):
            monitor_vals += read_signed_values(self.client, servo_number, 368+i*8, 8)
        monitor_vals += read_signed_values(self.client, servo_number, 368+24, 5)
        self.parameters = parse_values(keys, monitor_vals)
        return 0     
        
    def read_SigOut(self, servo_number:int)->dict:
        """See Dn18, modbus addr (386) :368~396 #TODO: put this function into Monitoring class

        Args:
            servo_number (int): _description_
        """        
        keys = ['TCMDreach', 'SPL', 'TRQL', 'Pnear', 'HOME', 'BRK', 'Run',
            'ZeroSpeed', 'Treach', 'Sreach', 'Preach', 'EMG', 'Ready', 'Alarm'
        ]
        rr = self.client.read_holding_registers(386, 1, slave=servo_number)
        str_vals = read_16bits(rr.registers[0], len(keys)) # len=14
        self.SigOut=parse_values(keys, list(map(int, list(str_vals))))
        return self.SigOut

    
class Sync_AASD_15A:
    """Serial synchronous AC Servo Driver for AC Servo Motor model 80ST-M02430LB
    """    
    def __init__(self, port:str, framer=ModbusRtuFramer, baudrate=115200, bytesize=8, parity="O", stopbits=1, strict=False):
        self.controller = ModbusSerialClient(
            port=port,
            framer=framer,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            strict=strict       
        )
        
        self.parameters={
            'settings': {
                'system': None,
                'position': None,
                'speed': None,
                'torque': None,
                'extended': None
            }, 
            'alarm':None, 
            'monitoring':None
        }
        
        
    def _read(self, servo_number:int, mb_addr:int, count:int=1) -> int:
        """read parameter at address mb_addr for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address to read value

        Returns:
            int: signed integer value
        """        
        rr = self.controller.read_holding_registers(mb_addr, count, slave=servo_number)
        nums=[]
        for num in rr.registers:
            # convert to 32-bit signed integer
            if num & (1 << 15):
                num = -((num ^ 0xffff) + 1)
            nums.append(num)
        return nums

    def _write_noconvert(self, servo_number:int, mb_addr:int, val:int) -> None:
        """Write without checking signed value val to parameter at mb_addr for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address (Pn) to write value.
            val (int): signed integer
        """        
        # signed integer to unsigned
        self.controller.write_register(mb_addr, val, slave=servo_number)        
        
    def _write2(self, servo_number:int, addr_start:int, val1:int, val2:int, signed=True) -> None:
        """Write 2 consecutive addresses with checking signed values val to parameter at addr_start and addr_start +1 
        for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            addr_start (int): start modbus address (Pn) to write to.
            val1 (int): signed integer. Value to write to addr_start
            val2 (int): signed integer. Value to write to addr_start + 1
            signer (bool): if value is a signed integer.
        """        
        # signed integer to unsigned
        usval1 = val1 & 0xffff if signed else val1
        usval2 = val2 & 0xffff if signed else val2
        self.controller.write_registers(addr_start, [usval1, usval2], slave=servo_number)
        
    def _write1(self, servo_number:int, mb_addr:int, val:int, signed=True) -> None:
        """Write with checking signed value val to parameter at mb_addr for servo_number.
        
        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address (Pn) to write value.
            val (int): signed integer
            signer (bool): if value is a signed integer.
        """        
        # signed integer to unsigned
        usval = val & 0xffff if signed else val
        self._write_noconvert(servo_number, mb_addr, usval)

    def read_SigIn_port(self, servo_number:int) -> dict:
        keyList = ['Sen', 'Punlock', 'Pdistance', 'Psource', 
           'Pstop', 'Ptrigger', 'Pos2', 'Pos1', 
           'REF', 'GOH', 'PC', 'INH', 
           'Pclear', 'Cinv', 'Gn2', 'Gn1', # start register2
           'Cgain', 'Cmode', 'TR2', 
           'TR1', 'Sp3', 'Sp2', 'Sp1', 
           'ZeroLock', 'EMG', 'TCW', 'TCCW', 
           'CWL', 'CCWL', 'AlarmRst', 'SON', # start register1
          ]
        self.SigIn = {key: None for key in keyList}
        # nums = self._read(servo_number, 68, 2)
        rr = self.controller.read_holding_registers(68, 4, slave=servo_number)
        nums = rr.registers
        regs_mode_and_enable = [read_16bits(num, 15) for num in nums]
        for i in range(15): # Pn068~Pn171
            self.SigIn[keyList[i+16]]={'internal': int(regs_mode_and_enable[0][i])}        
            self.SigIn[keyList[i+1]]={'internal': int(regs_mode_and_enable[1][i])} # don't use [0] = "Sen"
            self.SigIn[keyList[i+16]]={'enable': int(regs_mode_and_enable[2][i])}
            self.SigIn[keyList[i+1]]={'enable': int(regs_mode_and_enable[3][i])} # don't use [0] = "Sen"
        return self.SigIn
        
    def read_system_prms(self, servo_number:int, mb_addr:int) -> list:
        """Return list of 92 values from Pn000 to Pn092 except Pn086. #TODO: extended prms

        Args:
            servo_number (int): _description_
            mb_addr (int): _description_

        Returns:
            list: _description_
        """               
        system_op_ids = np.append(
            np.arange(86),
            np.arange(87,93)
        )
        # TODO: convert signed int
        for i in range(10):
            rr = self.controller.read_holding_registers(system_op_ids[i*8], 8, slave=servo_number)
        system_op_vals=rr.registers
        rr = self.controller.read_holding_registers(system_op_ids[80], 6, slave=servo_number)
        system_op_vals.append(rr.registers)
        rr = self.controller.read_holding_registers(system_op_ids[86], 6, slave=servo_number)
        system_op_vals.append(rr.registers)
        return system_op_vals
    
    def read_position_prms(self, servo_number:int, mb_addr:int) -> list:
        """Return list of 46 values from Pn096 to Pn141.

        Returns:
            _type_: _description_
        """                
        position_op_ids = np.arange(96,142)
        
        for i in range(5):
            rr = self.controller.read_holding_registers(position_op_ids[i*8], 8, slave=servo_number)
        position_op_vals=rr.registers
        rr = self.controller.read_holding_registers(position_op_ids[40], 6, slave=servo_number)
        position_op_vals.append(rr.registers)
        return position_op_vals
    
    def read_speed_prms(self, servo_number:int, mb_addr:int) -> list:
        """Return list of 36 values from Pn146 to Pn183 except Pn180 and Pn181.

        Args:
            servo_number (int): _description_
            mb_addr (int): _description_

        Returns:
            list: _description_
        """        
        speed_op_ids = np.append(
            np.arange(146,180),
            np.arange(182,184)
        )
        
        for i in range(3):
            rr = self.controller.read_holding_registers(speed_op_ids[i*8], 8, slave=servo_number)
        speed_op_vals=rr.registers
        rr = self.controller.read_holding_registers(speed_op_ids[32], 2, slave=servo_number)
        speed_op_vals.append(rr.registers)
        rr = self.controller.read_holding_registers(speed_op_ids[34], 2, slave=servo_number)
        speed_op_vals.append(rr.registers)
        return speed_op_vals
    
    def read_torque_prms(self, servo_number:int, mb_addr:int) -> list:
        """Pn186..Pn210
        """        
        torque_op_ids = np.arange(186,211)
        
        for i in range(3):
            rr = self.controller.read_holding_registers(torque_op_ids[i*8], 8, slave=servo_number)
        torque_op_vals=rr.registers
        rr = self.controller.read_holding_registers(torque_op_ids[24], 1, slave=servo_number)
        torque_op_vals.append(rr.registers)
        return torque_op_vals
    
    def read_extended_prms(self, servo_number:int, mb_addr:int) -> list:
        """Return list of 36 values from Pn216 to Pn270 except Pn240 to Pn256 and Pn261 to Pn262. #TODO: extended prms

        Args:
            servo_number (int): _description_
            mb_addr (int): _description_

        Returns:
            list: _description_
        """        
        """Pn216..Pn219 #TODO: append from syst op.
        Pn220..Pn233
        Pn234..Pn239
        Pn257..Pn260
        Pn263..Pn270
        """        
        extended_op_ids = np.append(
            np.arange(216, 240),
            np.arange(257,261)
        )
        extended_op_ids=np.append(extended_op_ids, np.arange(263,271))
        # TODO: convert signed int
        for i in range(3):
            rr = self.controller.read_holding_registers(extended_op_ids[i*8], 8, slave=servo_number)
        extended_op_vals=rr.registers
        rr = self.controller.read_holding_registers(extended_op_ids[24], 4, slave=servo_number)
        extended_op_vals.append(rr.registers)
        rr = self.controller.read_holding_registers(extended_op_ids[28], 8, slave=servo_number)
        extended_op_vals.append(rr.registers)
        return extended_op_vals
    
    def change_bitN(self, servo_number:int, Pn:int, bit_pos:int, value=1) -> int:
        """Change bitN value of register 1 or 2 (see Pn070 and Pn071)

        Args:
            servo_number (int): servo motor number (see Pn065).
            Pn (int): modbus address of register
            bit_pos (int): bit position N
            value (int, optional): 0 or 1. Defaults to 1.

        Returns:
            int: Pn value (decimal)
        """        
        val =  self._read(servo_number, Pn)[0] # int number
        register = read_16bits(val, 15) # bin format
        list_reg = list(register) # convert to list to change bit10
        list_reg[15-bit_pos-1]=str(value) # set bit10 to value 1 (default)
        reg=''
        for elm in list_reg:
            reg += elm
        val = int(reg, 2) # re-convert to int
        self._write_noconvert(servo_number, Pn, val)
        return val

    def trigger(self, servo_number:int, raising=True) -> int:
        """Trigger servo_number movement. If raising=True, trigger is raising edge.
        Trigger BIT10 of register 2 (Pn071)

        Args:
            servo_number (int): servo motor number (see Pn065).
            raising (bool, optional): trigger is raising (True) or falling (False). Defaults to True.

        Returns:
            int: 0
        """        
        Pn, bit_pos=71, 10
        val =  self._read(servo_number, Pn)[0]
        register = read_16bits(val, 15)
        list_reg = list(register)
        if raising:
            if list_reg[15-bit_pos-1]=='1':
                self.change_bitN(Pn, bit_pos, 0)
            else:
                self.change_bitN(servo_number, Pn, bit_pos, 1)
        else:
            if list_reg[15-bit_pos-1]=='0':
                self.change_bitN(servo_number, Pn, bit_pos, 1)
            else:
                self.change_bitN(servo_number, Pn, bit_pos, 0)
        return 0
    
    def set_motor_code(self, servo_number:int, value:int=4):
        """This is Pn001 function for writing. Effect after driver reboot.

        Args:
            servo_number (int): servo motor number (see Pn065).
            value (int, optional): 0..70. Defaults to 4 (80ST-M02430 motor).
        """        
        self._write_noconvert(servo_number, 1, value)
        print("Please reboot the servo motor for taking effect.\n \
              For permanent write set Pn081 or manually set Fn001")
        
    def set_control_mode(self, servo_number:int, value:int=2):
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
        """     
        self._write_noconvert(servo_number, 2, value)
    
    def set_enable_motor(self, servo_number:int, enable:bool=True):
        """Enable motor (Pn003)

        Args:
            servo_number (int): servo motor number (see Pn065).
            enable (bool, optional): _description_. Defaults to True.
        """  
        self._write_noconvert(servo_number, 1) if enable else self._write_noconvert(servo_number, 0)  
    
    def set_servo_enable_mode(self, servo_number:int, value:int=0):    
        """Servo enable mode (Pn003)

        Args:
            servo_number (int): servo motor number (see Pn065).
            value (int, optional): servo enable mode 0..1. Defaults to 0.
                0: the SON (servo ON) enable drive from the input port SigIn
                1: Automatically enable drive after power on.
        """  
        self._write_noconvert(servo_number, value)
        
    def allow_internal_control(self, servo_number:int, allow:bool=True):
        """system settings for internal instruction mode.
        write input fonction control register 2 (Pn069) to allow internal control of Ptrigger (Bit10)

        Args:
            servo_number (int): servo motor number (see Pn065).
            allow (bool, optional): _description_. Defaults to True.
        """
        Pn, bit_pos = 69, 10
        if allow:
            self.change_bitN(servo_number, Pn, bit_pos, 1)
        else:
            self.change_bitN(servo_number, Pn, bit_pos, 0)
        return 0
    
    def set_PM_logic_direction(self, servo_number:int, clockwise:bool=False):
        """Position mode Pn097. Set direction CCW (default) when enter a ppsitive command.

        Args:
            servo_number (int): servo motor number (see Pn065).
            clockwise (bool, optional): CCW or CW. Defaults to False (CCW).
        """
        self._write_noconvert(servo_number, 97, 1) if clockwise else self._write_noconvert(servo_number, 97, 0)
        
    def reverse(self, servo_number:int, reverse:bool=False):
        """Same as `set_PM_logic_direction`.
        By default the motor rotates in CCW when you are facing the motor shaft.
        To reverse this direction set reverse=True.

        Args:
            servo_number (int): servo motor number (see Pn065).
            reverse (bool): False: CCW, True: CW. Defaults to False (CCW).
        """    
        self.set_PM_logic_direction(servo_number, clockwise=reverse)
            
    def set_PM_electronic_gear_ratio(self, servo_number:int, gear_ratio:int, cell:int=4):
        """Position mode Pn098~Pn101. Set the electronic gear ratio for cell N.
        The cell number is determined by Gn1, Gn2.
        
        #TODO: check Gn1, Gn2 (Pn071) to see which cell is selected. Default is cell 4 (Pn101)

        Args:
            servo_number (int): servo motor number (see Pn065).
            gear_ratio (int): 1~32767. see appendix electronic gear ratio calculation.
            cell (int): 1~4. Default to 4. 1 is Pn098,.., 4 is Pn101.
        """
        assert cell in range(1,5)
        assert gear_ratio in range(1, 32768)
        Pn=97+cell # Pn098~Pn101
        self._write_noconvert(servo_number, Pn, gear_ratio)
        
    def set_PM_accel_decel_mode(self, servo_number:int, function_nb:int=2):
        """Position mode Pn109.Set function filter for acceleration and deceleration mode.

        Args:
            servo_number (int): servo motor number (see Pn065).
            function_nb (int, optional): 0~2. Defaults to 2. 0: no filtering, 1: smooth one time, 2: S-curve.
        """        
        self._write_noconvert(servo_number, 109, function_nb)
        
    def set_PM_command_source_selection(self, servo_number:int, source:int=2):
        """Position mode Pn117. Select source for position command.
        Internal is RS485, external is pulse input.

        Args:
            servo_number (int): servo motor number (see Pn065).
            source (int, optional): 0~3. Defaults to 2 (internal if SigIn Psourec=1).
        """        
        self._write_noconvert(servo_number, 117, source)
        
    def set_PM_move(self, servo_number:int, n_high:int, n_low:int, internal_cmd:int=0, trigger=True):
        """Position mode Pn120~Pn127. Set motor position and trigger the movement.
        Args:
            servo_number (int): _description_
            n_high (int): -9999~9999: number of circles.
            n_low (int): -9999~9999: e.g. 5000 is half the circle.
            internal_cmd (int, optional): 0~3 Determined by Pos1, Pos2 values see Pn071. Defaults to 0.
        """        
        assert internal_cmd in range(4)
        Pn=120+2*internal_cmd
        self._write2(servo_number, Pn, n_high, n_low)
        if trigger:
            self.trigger(servo_number)


python -m asyncio
        
async_client=AsyncModbusSerialClient(
    port="COM7", # /dev/ttyUSB0
    framer=ModbusRtuFramer,
    baudrate=115200,
    bytesize=8,
    parity="O",
    stopbits=1,
    strict=False                      
)
    
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
        
          
