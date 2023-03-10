# AASD-15 driver for 6DOF motion simulator
## _Using RS485 rtu protocol_

[![N|Solid](https://cldup.com/dTxpPi9lDf.thumb.png)](https://nodesource.com/products/nsolid)

[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

WIP: implement functions for:

- Parameter settings mode: Pn000~Pn236:
  - system control parameters: Pn00~Pn095 (WIP)
  - position control parameter: Pn096~Pn145 (TODO)
  - speed control parameters: Pn146~Pn185 (TODO)
  - torque control parameters: Pn186~Pn215 (TODO)
  - extended control parameter: Pn216~Pn236 (TODO)
- Monitoring mode: Dn000~Dn028 (TODO)
- Alarm reading mode: Fn000~Fn??? (TODO)

## modbus communication address

- 0~236 for Pn000~Pn236
- 356~365 for Fn000~Fn???
- 368~396 for Dn000~Dn028

## Installation: using Docker

Configuration: Host is Windows 10 with Docker Desktop, Ubuntu WSL, XLaunch (Xming) and usbipd installed. 

### install usbipd-win

Follow instructions [here](https://github.com/dorssel/usbipd-win) to install `usbipd-win` software for sharing locally connected USB devices to other machines, including WSL 2

### install X server for Windows
Install Xming X Server for Windows [here](https://sourceforge.net/projects/xming/files/Xming/6.9.0.31/Xming-6-9-0-31-setup.exe/download)

### install usbip in Ubuntu WSL

Ubuntu WSL is the bridge between the host (Windows 10) and the docker container where we'll develop.

```sh
sudo apt update
sudo apt install linux-tools-virtual hwdata
sudo update-alternatives --install /usr/local/bin/usbip usbip `ls /usr/lib/linux-tools/*/usbip | tail -n1` 20
```
### attach the rs485 usb device to WSL

Check that Docker Desktop and WSL are running:
```
wsl -l -v
``` 
Should print:
```
  NAME                   STATE           VERSION
* docker-desktop-data    Running         2
  docker-desktop         Running         2
  Ubuntu                 Running         2
``` 

In Windows terminal, list all usb devices attached: `usbipd list`.

Attach the COM port where the RS485 usb device is plugged: `usbipd wsl attach -d Ubuntu -b <BUSID>`. You can check in Ubuntu WSL with `lsusb`.

### Create the development environment with Docker

#### Build docker image: 

cd to this root dir where is the `Dockerfile` and build:
```sh
docker build --tag=modbus6dof:dev .
```

#### Run the container

Check the vEthernet(WSL) IP address in Windows with `ipconfig` and check the Ubuntu WSL IP with `cat /proc/net/fib_trie`. By using this [website](https://tehnoblog.org/ip-tools/ip-address-in-cidr-range/) select an IP address which matches CIDR (e.g. 172.24.245.10 for this tuto) then run the container:
```sh
docker run --ip 172.24.245.10 -it --rm --privileged -e DISPLAY=host.docker.internal:0.0 -v "e:\dev\instrumentation\hardware\6DOF":/6dof:rw --name=6dof_dev modbus6dof:dev bash
```

### Test installation

run `XLaunch` from Windows host with default params

run the test app in the container:
```sh
cd /6dof
python main_assd15.py
```

### finish

detach usb device physically or use this command: `usbipd wsl detach -b <BUSID>` in Windows terminal.
## Quick start (TODO)

## Basic test with `pymodbus`

The default serial port settings for RS485 modbus rtu is `8-bits` data, `Odd` parity, `1-bit` stop, `115200` baudrate.

Before using this module, you have to change the Pn065 parameter to `1` for `motor1`, `2` for `motor2`, etc. This is the site address for communication.

**Note:** With RS485 you can connect all your 6 AASD comports to one USB-RS485 adaptator using 2 `120 Ohm` terminal resistors.
1) list your COM ports to find which COM port is connected your usb-rs485 adaptator:
```sh
from serial.tools.list_ports import comports
list_comm = comports()
for port in list_comm:
    for m in port.__dict_keys():
        print(m, ": ", port.__getattribute__(m))
    print('-'*79)
```
2) define the motor identity and the COM port:
```sh
motor_id = 1
port = 'COM7' # change here for your actual COM port
```
3) setup the modbus rtu client for your usb-rs485 adaptator
```sh
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
client = ModbusClient(
                        method='rtu', 
                        port=port, 
                        stopbits=1, 
                        bytesize=8, 
                        parity='O', 
                        baudrate=115200, 
                        strict=False
                    )
```
4) goto editing mode if not yet:
```sh
Pn, nbyte = 0, 1
rr = client.read_holding_registers(Pn, nbyte, unit=motor_id)
if rr.getRegister(0) != 1: # change to editing mode
    client.write_register(Pn, 1, unit=motor_id)
```
5) set the driver for 80st-m02430 motor:
```sh
Pn, value = 1, 4
client.write_register(Pn, value, unit=motor_id) # motor code for 80st-m02430 is 4
```
6) **WARNING** for test only: enable the driver when power on:
```sh
Pn, value = 3, 1
client.write_register(Pn, value, unit=motor_id)
```
7)
