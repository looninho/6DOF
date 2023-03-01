'''
'''
import sys, os
this_dir = os.path.dirname(os.path.abspath(__file__))

# from PyQt5 import uic
# from PyQt5.QtWidgets import QApplication
from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import loadUiType

# from PyQt5.QtCore import pyqtSlot
from PySide6.QtCore import Slot

from serial.tools.list_ports import comports
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.client import ModbusSerialClient as ModbusClient

# Form, Base = uic.loadUiType('aasd15.ui')
Form, Base = loadUiType('aasd15.ui')
class MainWindow(Form, Base):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self._scan_serialports()
        self.connect_signals()
        
    def _scan_serialports(self):
        for comport in comports():
            self.comports_cb.addItem(comport.device)
            
    def connect_signals(self):
        self.comports_cb.addItem("custom")
        self.comports_cb.setCurrentIndex(1)
        self.comports_cb.currentTextChanged.connect(self.create_client)
    
    # @pyqtSlot(str)
    @Slot(str)
    def create_client(self, device: str):
        self.comport_name = device
        print(f'device: {self.comport_name}\n')
        if self.client:
            self.client.close()
        self.client = ModbusClient(
            port=self.comport_name, 
            framer=ModbusRtuFramer, 
            baudrate=115200, 
            bytesize=8, 
            parity='O', 
            stopbits=1, 
            strict=False
        )

        

if __name__ == '__main__':
    app = QApplication([])
    FEN = MainWindow()
    FEN.show()
    sys.exit(app.exec())
