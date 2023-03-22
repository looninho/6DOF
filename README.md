# Setup python environment
1) install python with Microsoft Store
2) create your workspace folder e.g:
    `mkdir -p d:\workspace\6dof`
3) then cd to this folder and create your python environment:
    `d: && cd  workspace\6dof`
    `python -m venv --system-site-packages 6dof-env`
    `6dof-env\Scripts\activate`
    `pip install -U pymodbus pyserial`

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
  - Pn065=1 # slave number
```
slave = 1
```
Assuming that your COM port is `COM3` and other communication parameters are defaults to `baud=115200`, `bytesize=8`, `parity=Odd`, `stopbits=1`. see Pn066 and Pn067. We define the client to communicate:
```
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.client import ModbusSerialClient

client=ModbusSerialClient(port='COM3',
                          framer=ModbusRtuFramer,
                          baudrate=115200,
                          bytesize=8,
                          parity="O",
                          stopbits=1,
                          strict=False
                          )
```
## System settings for internal control
### Simplifying
We define some function to simplify:
```
def read_holding_register(mb_addr, slave=slave):
    rr = client.read_holding_registers(mb_addr, 1, slave=slave)
    return rr.getRegister(0)

def write_register(mb_addr, val, slave=slave):
    client.write_register(mb_addr, val, slave=slave)

def read_16bits(val):
    return bin(val).replace('0b', '').zfill(15)

def set_bitN_to(Pn, bit_pos, value=1):
    val =  read_holding_register(Pn) # int number
    register = read_16bits(val) # bin format
    list_reg = list(register) # convert to list to change bit10
    list_reg[15-bit_pos-1]=str(value) # set bit10 to 1
    reg=''
    for elm in list_reg:
        reg += elm
    val = int(reg, 2) # re-convert to int
    write_register(Pn, val)
    return val

def trigger(Pn, bit_pos, raising=True):
    val =  read_holding_register(Pn)
    register = read_16bits(val)
    list_reg = list(register)
    if raising:
        if list_reg[15-bit_pos-1]=='1':
            change_bitN(Pn, bit_pos, 0)
        else:
            change_bitN(Pn, bit_pos, 1)
    else:
        if list_reg[15-bit_pos-1]=='0':
            change_bitN(Pn, bit_pos, 1)
        else:
            change_bitN(Pn, bit_pos, 0)
    return 0

```

### System settings
Internal control is RS485 unlike external or analog control.
Define your motor type number, see your motor's documentation, e.g for 80ST-M02430 the motor number is `4`:
```
# set motor number
Pn, val = 1, 4 # 4 is 80ST-M02430 motor
write_register(Pn, val)

# change the SigIn Ptrigger BIT10=1 for internal control
Pn, bit_pos = 69, 10
set_bitN_to(Pn, bit_pos, 1)

# select internal position control mode
Pn, val = 2, 2
write_register(Pn, val)
```
### position settings
```
# set electronic gear ratio to 3 for cell number 4 (Pn101)
Pn, val = 101, 3
write_register(Pn, val)

# select S-curve filter for accel & decel mode
Pn, val = 109, 2
write_register(Pn, val)

# select cpntrol source is internal
Pn, val = 117, 1 
write_register(Pn, val)
```

## Move motor
```
# preset the motor shaft to the position 1.5 CW
Pn, val = 120, 1 & 0xffff # x 10 000 pulse. [-9999~9999]
write_register(Pn, val)

# enable the motor
write_register(3, 1)

# each time we trigger, the motor wil turn 1.5 CW
Pn, bit_pos = 71, 10
trigger(Pn, bit_pos, raising=True)

# disable the motor
write_register(3, 0)
```
