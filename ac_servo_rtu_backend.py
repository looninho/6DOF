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
                                stopbits=1, 
                                bytesize=8,
                                parity='O',
                                baudrate=9600, #TODO
                                strict=False)
            servo = AASD_15A(client, 1)
            ```
            slave_address (int): modbus unit
        """        
        self.UNIT = slave_address
        self.controller = client
        
    # System parameters Pn (Write, read possible)
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
    
    def set_parameter_editing_mode(self, value:int=1):
        """This is the Pn000 writing function.

        Args:
            value (int, optional): see get_parameter_editing_mode(). Defaults to 1.
        """        
        self.controller.write_register(0, int(value), unit=self.UNIT) # 0 is Pn000
        # return self.get_parameter_editing_mode() == value
    
    def get_motor_code(self) -> int:
        """This is Pn001 function for reading.

        Returns:
            int: 0..35: the current motor code. For 80ST-M02430 the code is 4.
        """        
        rr = self.controller.read_holding_registers(1, 1, unit=self.UNIT) 
        return rr.getRegister(0)
    
    def set_motor_code(self, value:int=4):
        """This is Pn001 function for writing. Effect after driver reboot.

        Args:
            value (int, optional): 0..70. Defaults to 4 (80ST-M02430 motor).
        """        
        self.controller.write_register(1, int(value), unit=self.UNIT)
     
    def get_control_mode(self) -> int:
        """Control mode. Pn002 function.

        Returns:
            int: setting mode value 0..5.
                0: Torque mode,
                1: Speed mode,
                2: Position mode,
                3: Position / speed mode,
                4: Position / torque mode,
                5: Speed / torque mode
        """    
        rr = self.controller.read_holding_registers(2, 1, unit=self.UNIT) 
        return rr.getRegister(0)   
    
    def set_control_mode(self, value:int=2):
        """Set control mode. Effect after driver reboot.

        Args:
            value (int, optional): setting mode value 0..5. Defaults to 2.
                0: Torque mode,
                1: Speed mode,
                2: Position mode,
                3: Position / speed mode,
                4: Position / torque mode,
                5: Speed / torque mode
        """     
        self.controller.write_register(2, int(value), unit=self.UNIT)
        
    def get_servo_enable_mode(self) -> int:
        """Servo enable mode (Pn003)

        Returns:
            int: servo enable mode 0..1
                0: the SON (servo ON) enable drive from the input port SigIn
                1: Automatically enable drive after power on.
        """    
        rr = self.controller.read_holding_registers(3, 1, unit=self.UNIT) 
        return rr.getRegister(0)    
    
    def set_servo_enable_mode(self, value:int=0):    
        """Servo enable mode (Pn003)

        Args:
            value (int, optional): servo enable mode 0..1. Defaults to 0.
                0: the SON (servo ON) enable drive from the input port SigIn
                1: Automatically enable drive after power on.
        """        
        self.controller.write_register(3, int(value), unit=self.UNIT)

    def get_servo_disconnect_enable_shutdown_mode(self) -> int:
        """Servo disconnect enable shutdown mode (Pn004)
        When the enable signal changes from valid to invalid, the motor can
        be stopped operating: 0: inertia stop, 1: slow down and stop. The 
        deceleration time is determined by Pn005, 2: electromagnetic
        braking mode parking (suitable for motors with electromagnetic
        brakes).

        Returns:
            int: servo disconnect enable shutdown mode 0..2
                0: deceleration stop not used. Inertia stop
                1: deceleration stop = slow down and stop
                2: not used. For motors with electrmagnetic brakes
        """    
        rr = self.controller.read_holding_registers(4, 1, unit=self.UNIT) 
        return rr.getRegister(0)    
    
    def set_servo_disconnect_enable_shutdown_mode(self, value:int=1):    
        """Servo disconnect enable shutdown mode (Pn004)
        When the enable signal changes from valid to invalid, the motor can
        be stopped operating: 0: inertia stop, 1: slow down and stop. The 
        deceleration time is determined by Pn005, 2: electromagnetic
        braking mode parking (suitable for motors with electromagnetic
        brakes).

        Args:
            value (int, optional): servo disconnect enable shutdown mode 
            0..2. Defaults to 1.
                0: deceleration stop not used. Inertia stop
                1: deceleration stop = slow down and stop
                2: not used. For motors with electrmagnetic brakes
        """        
        self.controller.write_register(4, int(value), unit=self.UNIT)
        
    def get_break_down_to_slow_down(self) -> int:
        """Break down to slow down (Pn005)
        When the enable signal changes from valid to invalid, the motor is
        slow down to zero. In the deceleration process, if the enable signal 
        is effective again, the motor will slow down to zero.

        Returns:
            int: 5..10000 ms
        """    
        rr = self.controller.read_holding_registers(5, 1, unit=self.UNIT) 
        return rr.getRegister(0)    
    
    def set_break_down_to_slow_down(self, value:int=100):    
        """Break down to slow down (Pn005)
        When the enable signal changes from valid to invalid, the motor is
        slow down to zero. In the deceleration process, if the enable signal 
        is effective again, the motor will slow down to zero.

        Args:
            value (int, optional): 5..10000. 
            Defaults to 1.
        """        
        self.controller.write_register(5, int(value), unit=self.UNIT)
        

if __name__ == "__main__":
    # initialize de COM port and hook it to the driver
    client = ModbusClient(method='rtu', 
                          port='COM8', 
                          stopbits=1,
                          bytesize=8,
                          parity='O',
                          baudrate=115200, 
                          strict=False)
    
    # TODO: Before communicating with the servo set by hand the Pn065 to 1 for motor1, 2 for motor2, etc.
    
    servo = AASD_15A(client, 1) # address = 1 for motor 1, 2 for motor 2, etc.
    
    # let's see what is the current initialization mode:
    print(f"the current parameter initilization mode is: {servo.get_parameter_editing_mode()}")
    
    # now we want to allow parameter initialization, we enter the value 1 for that:
    servo.set_parameter_editing_mode(1)
    
    # set the motor code for your servo motor. For 80ST_M02430, the code is 4:
    servo.set_motor_code(4)
    
    # When you finish edition, don't forget to put it back to value 3
    servo.set_parameter_editing_mode(3)
    
    
    
    
    