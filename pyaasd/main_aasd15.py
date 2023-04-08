'''
'''
import sys, os
this_dir = os.path.dirname(os.path.abspath(__file__))
root_dir=os.path.dirname(this_dir)

from PySide6.QtWidgets import QApplication, QRadioButton
from PySide6.QtUiTools import loadUiType

from PySide6.QtCore import Slot
from PySide6.QtGui import QIntValidator

from serial.tools.list_ports import comports
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.client import ModbusSerialClient as ModbusClient

Form, Base = loadUiType( os.path.join(root_dir, 'pyaasd/ui/aasd15.ui'))
class MainWindow(Form, Base):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self._scan_serialports()
        self.connect_signals()
        
    def _scan_serialports(self):
        for comport in comports():
            self.comports_cb.addItem(comport.device)
    
    def init_controller(self):
        """Initialize the controller and get all data from it.
        """   
        print("init_controller from subclass TControl.")
    
    def connect_signals(self):
        self.comports_cb.addItem("custom")
        self.comports_cb.setCurrentIndex(1)
        self.comports_cb.currentTextChanged.connect(self.create_client)
        self.dn_radio.clicked.connect(self.get_checked_function)
        self.fn_radio.clicked.connect(self.get_checked_function)
        self.pn_radio.clicked.connect(self.get_checked_function)
        self.read_radio.clicked.connect(self.get_checked_request)
        self.write_radio.clicked.connect(self.get_checked_request)
    
    @Slot()    
    def on_send_pb_clicked(self):
        text_r=self.read_le.text()
        text_w=self.write_le.text()
        if self.read_radio.isChecked():
            vals = text_r.split('-')
            print(f"Send read modbus address: {vals[0]}, count: {int(vals[1])}")
        elif self.write_radio.isChecked():
            vals = text_w.split('-')
            count = int(vals[1])
            msg = "Send write modbus address start:" + vals[0] + ", count: " + vals[1] + ", values: "
            for v in vals[2:]:
                msg += v + ", "
            print(msg)
        else:
            return
            
    @Slot(str)
    def create_client(self, device: str):
        self.comport_name = device
        print(f'device: {self.comport_name}\n')
        if hasattr(self, "client"):
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

    @Slot()
    def get_checked_function(self):
        for rb in self.function_select_group.findChildren(QRadioButton):
            if rb.isChecked():
                radio_name = rb.objectName()
                if "pn" in radio_name:
                    self.function_name = "Pn"
                    self._set_modbus_addr_range(0, 236)
                elif "fn" in radio_name:
                    self.function_name = "Fn"
                    self._set_modbus_addr_range(356, 365)
                elif "dn" in radio_name:
                    self.function_name = "Dn"
                    self._set_modbus_addr_range(368, 396)
                else:
                    return
        print(f"{self.function_name} selected.")
        
    @Slot()
    def get_checked_request(self):
        if self.read_radio.isChecked():
            self.request = "read"
        elif self.write_radio.isChecked():
            self.request = "write"
        else:
            return
        self._set_input_mask_ranges()
        
    def _set_modbus_addr_range(self, addr_min:int, addr_max:int):
        self.min_modbus_addr = addr_min
        self.max_modbus_addr = addr_max
        
    def _set_input_mask_ranges(self):
        # set input mask for read_le:
        # self.read_le.setInputMask('999-99')
        
        # set the validator for meach entry in the read input mask
        # mbaddr_validator = QIntValidator(self.min_modbus_addr, self.max_modbus_addr, self.read_le)
        # count_validator = QIntValidator(1, 10, self.read_le)
        
        # self.read_le.setValidator(mbaddr_validator)
        # self.read_le.setValidator(count_validator) # start at index 4
        
        # set input mask for write_le:
        # self.write_le.setInputMask('999-9-99999')
        
        # set the validator for meach entry in the read input mask
        # mbaddr_validator = QIntValidator(self.min_modbus_addr, self.max_modbus_addr, self.write_le)
        # count_validator = QIntValidator(1, 1, self.write_le)
        # value_validator = QIntValidator(0, 100, self.write_le)
        
        # self.write_le.setValidator(mbaddr_validator)
        # self.write_le.setValidator(count_validator) # start at index 4
        # self.write_le.setValidator(value_validator) # start at index 6
        pass
        

if __name__ == '__main__':
    app = QApplication([])
    FEN = MainWindow()
    FEN.show()
    sys.exit(app.exec())
