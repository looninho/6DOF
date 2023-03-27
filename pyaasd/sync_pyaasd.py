# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:        sync_pyaasd.py
# Purpose:     Serial synchronous client driver for communicating with AASD-15A,
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

import os, sys
this_dir=os.path.dirname(os.path.abspath(__file__))
# parent_dir=os.path.dirname(this_dir)
sys.path.insert(1, os.path.join(this_dir, 'lib'))

# from serial.tools.list_ports import comports
from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer

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

# ? Should use it
class ErrorStatus(Exception):
    """ Example:
    ```python
    raise ErrorStatus('blabla...')
    ```
    """
    pass

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
        
    def read(self, servo_number:int, mb_addr:int) -> int:
        """read parameter at address mb_addr for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address to read value

        Returns:
            int: signed integer value
        """        
        rr = self.controller.read_holding_registers(mb_addr, 1, slave=servo_number)
        num = rr.getRegister(0)
        # convert to 32-bit signed integer
        if num & (1 << 15):
            num = -((num ^ 0xffff) + 1)
        return num

    def write_noconvert(self, servo_number:int, mb_addr:int, val:int) -> None:
        """Write without checking signed value val to parameter at mb_addr for servo_number.

        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address (Pn) to write value.
            val (int): signed integer
        """        
        # signed integer to unsigned
        self.controller.write_register(mb_addr, val, slave=servo_number)        
        
    def write2(self, servo_number:int, addr_start:int, val1:int, val2:int, signed=True) -> None:
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
        
    def write(self, servo_number:int, mb_addr:int, val:int, signed=True) -> None:
        """Write with checking signed value val to parameter at mb_addr for servo_number.
        
        Args:
            servo_number (int): servo motor number (see Pn065).
            mb_addr (int): modbus address (Pn) to write value.
            val (int): signed integer
            signer (bool): if value is a signed integer.
        """        
        # signed integer to unsigned
        usval = val & 0xffff if signed else val
        self.write_noconvert(servo_number, mb_addr, usval)

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
        val =  self.read(servo_number, Pn) # int number
        register = read_16bits(val) # bin format
        list_reg = list(register) # convert to list to change bit10
        list_reg[15-bit_pos-1]=str(value) # set bit10 to value 1 (default)
        reg=''
        for elm in list_reg:
            reg += elm
        val = int(reg, 2) # re-convert to int
        self.write_noconvert(servo_number, Pn, val)
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
        val =  self.read(servo_number, Pn)
        register = read_16bits(val)
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
        self.write_noconvert(servo_number, 1, value)
        print("Please reboot the servo motor for taking effect. For permanent write set Fn001")
        
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
        self.write_noconvert(servo_number, 2, value)
    
    def set_enable_motor(self, servo_number:int, enable:bool=True):
        """Enable motor (Pn003)

        Args:
            servo_number (int): servo motor number (see Pn065).
            enable (bool, optional): _description_. Defaults to True.
        """  
        self.write_noconvert(servo_number, 1) if enable else self.write_noconvert(servo_number, 0)  
    
    def set_servo_enable_mode(self, servo_number:int, value:int=0):    
        """Servo enable mode (Pn003)

        Args:
            servo_number (int): servo motor number (see Pn065).
            value (int, optional): servo enable mode 0..1. Defaults to 0.
                0: the SON (servo ON) enable drive from the input port SigIn
                1: Automatically enable drive after power on.
        """  
        self.write_noconvert(servo_number, value)
        
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
        self.write_noconvert(servo_number, 97, 1) if clockwise else self.write_noconvert(servo_number, 97, 0)
        
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
        self.write_noconvert(servo_number, Pn, gear_ratio)
        
    def set_PM_accel_decel_mode(self, servo_number:int, function_nb:int=2):
        """Position mode Pn109.Set function filter for acceleration and deceleration mode.

        Args:
            servo_number (int): servo motor number (see Pn065).
            function_nb (int, optional): 0~2. Defaults to 2. 0: no filtering, 1: smooth one time, 2: S-curve.
        """        
        self.write_noconvert(servo_number, 109, function_nb)
        
    def set_PM_command_source_selection(self, servo_number:int, source:int=2):
        """Position mode Pn117. Select source for position command.
        Internal is RS485, external is pulse input.

        Args:
            servo_number (int): servo motor number (see Pn065).
            source (int, optional): 0~3. Defaults to 2 (internal if SigIn Psourec=1).
        """        
        self.write_noconvert(servo_number, 117, source)
        
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
        self.write2(servo_number, Pn, n_high, n_low)
        if trigger:
            self.trigger(servo_number)


        
    

        
          
