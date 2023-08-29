# Setup python environment

1) install python with Microsoft Store

2) create your workspace folder:

`mkdir -p d:\workspace\6dof`

3) then cd to this folder and create your python environment:

`d: && cd workspace\6dof`

`python -m venv --system-site-packages 6dof-env`

`6dof-env\Scripts\activate`

`pip install -U APScheduler pymodbus pyserial PySide6 pyqtgraph`

  

# System settings

In your python console, identify the COM port for your RS485 adaptator:

```
from serial.tools.list_ports import comports

for port in comports():
	for m in port.__dict__.keys():
		print(m, ": ", port.__getattribute__(m))
	print('-'*79)
```
  
Prior to communicate with the driver, we have to check "by hand" the slave parameter.

Default factor settings is for `RS485` (Pn064) communication with `slave=1`. This is the modbus client number to identify your driver `1` for motor1, etc. You can check with:

- Pn065=1 # motor_idx


Assuming that your COM port is `COM3` and other communication parameters are defaults to `baud=115200`, `bytesize=8`, `parity=Odd`, `stopbits=1`. see Pn066 and Pn067. 
cd to this root folder, we define the controller for our 6 AASD drivers

```
from pyaasd.sync_pyaasd import Sync_AASD_15A

mycontroller = Sync_AASD_15A(port="COM3")
```

## System settings for internal control
### System settings

Internal control is RS485 unlike external or analog control.

Define your motor code number, see your motor's documentation, e.g for 80ST-M02430 the motor code number is `4`:

```
# set motor code (=4) for motor number 1
motor_idx = 1
mycontroller.set_motor_code(motor_idx, 4)

# change the SigIn Ptrigger BIT10=1 for internal control
mycontroller.allow_internal_control(motor_idx, True)
```

### position settings
```
# select internal position control mode
# You need to power cycle the driver to take effect or 
# set it permanently with Fn001.
mycontroller.set_control_mode(motor_idx, 2)

# set electronic gear ratio to 3 for cell number 4 (Pn101)
mycontroller.set_PM_electronic_gear_ratio(motor_idx, gear_ration=3, cell=4)  

# select S-curve filter for accel & decel mode
mycontroller.set_PM_accel_decel_mode(motor_idx, 2)

# select control source is internal
mycontroller.set_PM_command_source_selection(motor_idx, 2)
```

### Move motor with position mode
Now we can move the motor
```
# enable the motor
mycontroller.set_enable_motor(motor_idx, True)

# Move to the position 1.5 CW
mycontroller.set_PM_move(motor_idx, 1, 5000)

# disable the motor
mycontroller.set_enable_motor(motor_idx, False)

```

### speed settings
```
# select internal speed control mode  
# You need to power cycle the driver to take effect or  
# set it permanently with Fn001.  
mycontroller.set_control_mode(motor_idx, 1)

# set acceleration & deceleration mode to S-curve filter:
# note: values for Pn146 are
#        0: No acceleration and deceleration
#        1: S-curve accel & decel
#        2: Linear accel & decel
mycontroller.set_SM_accel_decel_mode(motor_idx, 1)

# set time constants Ts to 10 ms, Ta to 30 ms, Td to 100 ms:
mycontroller.set_SM_time_constants_ms(motor_idx, 10, 30, 100)

# select internal speed source control
mycontroller.set_SM_command_source_selection(motor_idx, 1)

# enable the motor  
mycontroller.set_enable_motor(motor_idx, True)

# set the motor speed to -50 rpm
# by default SP1, SP2 and SP3 are 0, 0, 0 this means
# the internal speed command is 1.
# if you set SP1, SP2, SP3 to 1, 1, 1 in the Pn070, 
# this means the internal speed command is 8.
mycontroller.set_SM_internal_speed_command_1(motor_idx, -50)

# disable the motor
mycontroller.set_enable_motor(motor_idx, False)
```