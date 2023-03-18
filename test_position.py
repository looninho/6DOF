# use pymodbus v3.x
# https://pymodbus.readthedocs.io/en/latest/source/examples.html#synchronous-client-example

from serial.tools.list_ports import comports
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.client import ModbusSerialClient

liste_comm = comports()
for port in liste_comm:
    for m in port.__dict__.keys():
        print(m, ": ", port.__getattribute__(m))
    print('-'*79)

slave = 1

client=ModbusSerialClient(port='/dev/ttyUSB0',
                          framer=ModbusRtuFramer,
                          baudrate=115200,
                          bytesize=8,
                          parity="O",
                          stopbits=1,
                          strict=False
                          )

def read_holding_register(mb_addr, slave=slave):
    rr = client.read_holding_registers(mb_addr, 1, slave=slave)
    return rr.getRegister(0)

def write_register(mb_addr, val, slave=slave):
    client.write_register(mb_addr, val, slave=slave)

# write motor type, check it is 4 for 8ST_M02430
Pn, val = 1, 4
motor_type = read_holding_register(Pn)
print(f"motor type: {motor_type}. (4 for 80st_m02430)")
if motor_type != val:
    print(f"motor_type was {motor_type}. Now set to {val}...")
    write_register(Pn, val)
else:
    print(f"motor_type is already {motor_type}. Nothing changed.")

# read and store registers to dictionary:
keyList = ['Punlock', 'Pdistance', 'Psource', 
           'Pstop', 'Ptrigger', 'Pos2', 'Pos1', 
           'REF', 'GOH', 'PC', 'INH', 
           'Pclear', 'Cinv', 'Gn2', 'Gn1', 
           'Cgain', 'Cmode', 'TR2', 
           'TR1', 'Sp3', 'Sp2', 'Sp1', 
           'ZeroLock', 'EMG', 'TCW', 'TCCW', 
           'CWL', 'CCWL', 'AlarmRst', 'SON', 
          ]
SigIn = {key: None for key in keyList}

## read input function control mode select register 1. (0:analog, 1:internal)
Pn = 68
val =  read_holding_register(Pn)
reg1_mode = bin(val).replace('0b', '').zfill(15)
for i in range(len(reg1_mode)):
    SigIn[keyList[i+15]]={'internal': int(reg1_mode[i])}

## read input function control mode select register 2. (0:analog, 1:internal)
Pn = 69
val =  read_holding_register(Pn)
reg2_mode = bin(val).replace('0b', '').zfill(15)
for i in range(len(reg2_mode)):
    SigIn[keyList[i]]={'internal': int(reg2_mode[i])}

## read input function logic state  registers 1 (0:Off, 1:On)
Pn = 70
val =  read_holding_register(Pn)
reg1_enable = bin(val).replace('0b', '').zfill(15)
for i in range(len(reg1_enable)):
    SigIn[keyList[i+15]]['enable'] = int(reg1_enable[i])

## read input function logic state  registers 2 (0:Off, 1:On)
Pn = 71
val =  read_holding_register(Pn)
reg2_enable = bin(val).replace('0b', '').zfill(15)
for i in range(len(reg2_enable)):
    SigIn[keyList[i]]['enable'] = int(reg2_enable[i])

for item in SigIn.items():
    print(item)

# system settings for internal instruction mode
## write Pn069 to allow internal control of Ptrigger (Bit10)
Pn, bit_pos = 69, 10
list_reg2 = list(reg2_mode)
list_reg2[15-bit_pos-1]='1'
reg2_mode=''
for elm in list_reg2:
    reg2_mode += elm

val = int(reg2_mode, 2)
val2 = read_holding_register(Pn)
if val2 != val:
    print(f"reg2_mode was {val2}. Now set to {val}...")
    write_register(Pn, val)

val2 = read_holding_register(Pn)
reg2_mode = bin(val2).replace('0b', '').zfill(15)
for i in range(len(reg2_mode)):
    SigIn[keyList[i]]['internal'] = int(reg2_mode[i])

print(f"Ptrigger is: {SigIn[keyList[15-bit_pos-1]]}")

## select internal (modbus) position control mode
Pn, val = 2, 2
control_mode = read_holding_register(Pn)
print(f"control mode: {control_mode}. (2 for position mode)")
if control_mode != val:
    print(f"control_mode was {control_mode}. Now set to {val}...")
    write_register(Pn, val)
    print("\nPlease, POWER CYCLE the driver to take effect.")
else:
    print("\nDriver is ready.")

############################################
# # INTERNAL POSITION CONTOL
############################################
## position control mode settings
Pn, val = 101, 3 # (Gn2, Gn1) = (1, 1)
pe_gear_ratio =  read_holding_register(Pn)
print(f"pe_gear_ratio: {pe_gear_ratio}.")
if pe_gear_ratio != val:
    print(f"pe_gear_ratio was {pe_gear_ratio}. Now set to {val}...")
    write_register(Pn, val)

Pn, val = 109, 2 # accel&decel mode: S-curve filter
accel_decel_mode =  read_holding_register(Pn)
print(f"accel_decel_mode: {accel_decel_mode}. (2 for S-curve filter)")
if accel_decel_mode != val:
    print(f"accel_decel_mode was {accel_decel_mode}. Now set to {val}...")
    write_register(Pn, val)

Pn, val = 117, 1 # src sel
pos_cmd_src =  read_holding_register(Pn)
print(f"pos_cmd_src: {pos_cmd_src}. (1 for internal position src)")
if pos_cmd_src != val:
    print(f"pos_cmd_src was {pos_cmd_src}. Now set to {val}...")
    write_register(Pn, val)

## preset the motor shaft to the position 1.5 circle
Pn, val = 120, 1 & 0xffff # x 10 000 pulse. [-9999~9999]
p_hight =  read_holding_register(Pn)
print(f"pulse number high: {p_hight}. (x 10 000 pulse)")
if p_hight != val:
    print(f"pulse number high was {p_hight}. Now set to {val}...")
    write_register(Pn, val)

Pn, val = 121, 5000 & 0xffff # x 10 000 pulse. [-9999~9999]
p_low =  read_holding_register(Pn)
print(f"pulse number low: {p_low}. (x 10 000 pulse)")
if p_low != val:
    print(f"pulse number low was {p_low}. Now set to {val}...")
    write_register(Pn, val)

## enable the motor
client.write_register(3, 1, slave=slave)

## trigger on the position
Pn, bit_pos = 71, 10
val =  read_holding_register(Pn)
reg2_enable = bin(val).replace('0b', '').zfill(15)
if reg2_enable[15-bit_pos-1]=='1': # set to low before rising edge
    list_reg2 = list(reg2_enable)
    list_reg2[15-bit_pos-1]='0'
    reg2_enable=''
    for elm in list_reg2:
        reg2_enable += elm
    val = int(reg2_enable, 2)
    write_register(Pn, val)

list_reg2 = list(reg2_enable)
list_reg2[15-bit_pos-1]='1'
reg2_enable=''
for elm in list_reg2:
    reg2_enable += elm

val = int(reg2_enable, 2)
write_register(Pn, val)

## disable the motor
client.write_register(3, 0, slave=slave)

