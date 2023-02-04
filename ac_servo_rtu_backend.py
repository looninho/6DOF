# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# Name:        ac_servo_rtu_backend.py
# Purpose:     driver for communicating with AASD-15A,
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

from pymodbus.client.sync import ModbusSerialClient as ModbusClient

# User parameter mode (Pn) operation
# address 0000H..00ECH or 0..236 (dec): Pn000..Pn236 (read-write)

# Auxiliaire mode (Fn) operation
# address 0164H..016DH or 356..365 (dec): Fn000..Pn236 (read only)

# Monitoring mode (Dn) operation
# address 0000H..00ECH or 368..396 (dec): Dn000..Dn028 (write only)

# ? Should use it
class ErrorStatus(Exception):
    """ Example:
    ```python
    raise ErrorStatus('blabla...')
    ```
    """
    pass

class AASD_15A(object):
    """AC Servo Driver for AC Servo Motor model 80ST-M02430LB
    """
    def __int__(self, client: ModbusClient, slave_address: int):
        """Initialize the AC Servo Driver.
        
        This function must be called only once before any other functions 
        of this library are called.

        Args:
            client (ModbusClient): the modbus client on the comport. 
            example of client:
            ```python
            from pymodbus.client.sync import ModbusSerialClient as ModbusClient
            client = ModbusClient(method='rtu', 
                                port='COM2', 
                                timeout=1, 
                                baudrate=9600, #TODO
                                strict=False)
            servo = AASD_15A(client, 1)
            ```
            slave_address (int): modbus unit
        """        
        self.UNIT = slave_address
        self.controller = client
        
    # System parameters
    def get_parameter_editing_mode(self) -> int:
        """This is the Pn000 reading function. It returns the current 
        parameter editing mode.

        Returns:
            int: current parameter editing mode:
                0: Parameter initialization prohibited.
                1: allow parameter initialization but does not initialize
                  Pn001, 80, 159, 190 and other application independent 
                  functional parameters.
                2: restore settings before shipment.
                3: press button to view mode and cannot modify parameters.
        """        
        rr = self.controller.read_holding_registers(0, 1, unit=self.UNIT) # 0 for Pn000, 1 for number of word(s) to read
        return rr.getRegister(0) # O is the LSB, 1 is MSB
    
    def set_parameter_editing_mode(self, value:int) -> int:
        """This is the Pn000 writing function.

        Args:
            value (int): 0, 1, 2 or 3 see descriptions above.

        Returns:
            int: see above
        """        
        rq = self.controller.write_register(0, int(value), unit=self.UNIT) # 0 is Pn000
        return self.get_parameter_editing_mode() == value
    
    def get_motor_code(self) -> int:
        """This is Pn001 function for reading.

        Returns:
            int: 0..35: the current motor code. For 80ST-M02430 the code is 4.
        """        
        rr = self.controller.read_holding_registers(1, 1, unit=self.UNIT) #  for Pn001, 1 or 2? for number of word(s) to read
        return rr.getRegister(0)
    
    def set_motor_code(self, value:int) -> int:
        """This is the Pn000 writing function.

        Args:
            value (int): 0..35 see descriptions above.

        Returns:
            int: TODO
        """        
        rq = self.controller.write_register(1, int(value), unit=self.UNIT)
        return self.get_motor_code() == value
    
    #TODO: for other functions that we don't need return value, we can ignore the return function to spped up the communication.


if __name__ == "__main__":
    # initialize de COM port and hook it to the driver
    client = ModbusClient(method='rtu', 
                                port='COM2', 
                                timeout=1, 
                                baudrate=9600, 
                                strict=False)
    
    servo = AASD_15A(client, 1) # address = 1 for motor 1, 2 for motor 2, etc.
    
    # let's see what is the current initialization mode:
    print(f"the current parameter initilization mode is: {servo.get_parameter_editing_mode()}")
    
    # now we want to allow parameter initialization, we enter the value 1 for that:
    servo.set_parameter_editing_mode(1)
    
    # set the motor code for your servo motor. For 80ST_M02430, the code is 4:
    servo.set_motor_code(4)
    
    # When you finish edition, don't forget to put it back to value 3
    servo.set_parameter_editing_mode(3)
    
    
    
    
    