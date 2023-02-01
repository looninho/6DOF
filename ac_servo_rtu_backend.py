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
        
    def Pn001(self):
        pass

if __name__ == "__main__":
    client = ModbusClient(method='rtu', 
                                port='COM2', 
                                timeout=1, 
                                baudrate=9600, 
                                strict=False)
    
    servo = AASD_15A(client, 1) # address = 1
    