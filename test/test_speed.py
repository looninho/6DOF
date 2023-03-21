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

# write motor type, check it is 4 for 80ST-M02430
Pn, val = 1, 4
motor_type = read_holding_register(Pn)
print(f"motor type: {motor_type}. (4 for 80st_m02430)")
if motor_type != val:
    print(f"motor_type was {motor_type}. Now set to {val}...")
    write_register(Pn, val)
else:
    print(f"motor_type is already {motor_type}. Nothing changed.")

# system settings for internal instruction mode
## select internal (modbus) speed control mode
Pn, val = 2, 1
control_mode = read_holding_register(Pn)
print(f"control mode: {control_mode}. (1 for speed mode)")
if control_mode != val:
    print(f"control_mode was {control_mode}. Now set to {val}...")
    write_register(Pn, val)
    print("\nPlease, POWER CYCLE the driver to take effect.")
else:
    print("\nDriver is ready.")

############################################
# # INTERNAL SPEED CONTROL
############################################
## speed control mode settings
Pn, val = 146, 1 # accel&decel mode: S-curve filter
accel_decel_mode =  read_holding_register(Pn)
print(f"accel_decel_mode: {accel_decel_mode}. (1 for S-curve filter)")
if accel_decel_mode != val:
    print(f"accel_decel_mode was {accel_decel_mode}. Now set to {val}...")
    write_register(Pn, val)

Pn, val = 147, 10
Ts =  read_holding_register(Pn)
print(f"Ts: {Ts} ms")
if Ts != val:
    print(f"Ts was {Ts} ms. Now set to {val} ms...")
    write_register(Pn, val)

Pn, val = 148, 30
Ta =  read_holding_register(Pn)
print(f"Ta: {Ta} ms")
if Ta != val:
    print(f"Ta was {Ta} ms. Now set to {val} ms...")
    write_register(Pn, val)

Pn, val = 149, 100
Td =  read_holding_register(Pn)
print(f"Td: {Td} ms")
if Td != val:
    print(f"Td was {Td} ms. Now set to {val} ms...")
    write_register(Pn, val)

Pn, val = 168, 1 # src sel
speed_cmd_src =  read_holding_register(Pn)
print(f"speed_cmd_src: {speed_cmd_src}. 1 for internal speed 1~8.")
if speed_cmd_src != val:
    print(f"speed_cmd_src was {speed_cmd_src}. Now set to {val}...")
    write_register(Pn, val)

## enable the motor
client.write_register(3, 1, slave=slave)

## set the motor speed to -50 rpm
Pn, val = 169, -600 & 0xffff # unit=rpm, range=[-5000~5000]
speed_cmd_src =  read_holding_register(Pn)
print(f"speed_cmd_src: {speed_cmd_src}. 1 for internal speed 1~8.")
if speed_cmd_src != val:
    print(f"speed_cmd_src was {speed_cmd_src}. Now set to {val}...")
    write_register(Pn, val)

## disable the motor
client.write_register(3, 0, slave=slave)
