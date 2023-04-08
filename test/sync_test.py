from pymodbus.client import ModbusSerialClient
from pymodbus.framer.rtu_framer import ModbusRtuFramer

class Sync_AASD:
    def __init__(self, client:ModbusSerialClient):
        self.client=client
        
    def read_settings(self, slave:int=1, addr:int=0, count:int=8):
        rr = self.client.read_holding_registers(addr, count, slave=slave)
        return rr.registers
    
if __name__ == "__main__":
    client=ModbusSerialClient(
        port="COM7", # /dev/ttyUSB0
        framer=ModbusRtuFramer,
        baudrate=115200,
        bytesize=8,
        parity="O",
        stopbits=1,
        strict=False                      
    )
    
    mydriver=Sync_AASD(client)
    print(mydriver.read_settings())