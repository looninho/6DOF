from colorsys import hsv_to_rgb
import os, sys

this_dir=os.path.dirname(os.path.abspath(__file__)) # test
root_dir=os.path.dirname(this_dir)
sys.path.insert(1, root_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from PySide6.QtUiTools import loadUiType
from PySide6.QtCore import Slot

from serial.tools.list_ports import comports
from pyaasd.lib.utils import to_children, PrmsDetail
from pyaasd.sync_pyaasd import Sync_AASD_15A

Form, Base = loadUiType( os.path.join(root_dir, 'pyaasd/ui/prm_description.ui') )
class DescWindow(Form, Base):
    def __init__(self, parent=None):
        super(DescWindow, self).__init__(parent)
        self.setupUi(self)
        self._scan_serialports()
        font = QFont()
        font.setPointSize(12)
        self.description_te.setFont(font)
        prms_d=PrmsDetail()
        self.all_desc=prms_d.read_detail()
        self.initUi()
        self.connect_signals()
        
    def _scan_serialports(self):
        for comport in comports():
            self.comports_cb.addItem(comport.device)
    
    def initUi(self):
        for key in self.all_desc.keys():
            self.category_cb.addItem(key)
        self.update_prm_list(self.category_cb.currentText())
            
    @Slot()
    def connect_signals(self):
        self.category_cb.currentTextChanged.connect(self.update_prm_list)
        self.parameter_cb.currentTextChanged.connect(self.update_description)
        self.read_btn.clicked.connect(self.read_value)
        self.connect_btn.clicked.connect(self.connect_device)
    
    @Slot()
    def connect_device(self):
        
        self.device = Sync_AASD_15A(port=self.comports_cb.currentText())
        
    @Slot()
    def read_value(self):
        if self.parameter_cb.currentText():
            Pn = int(self.parameter_cb.currentText().lower().replace('pn', ''))
            if hasattr(self, "device"):
                if self.device.controller.connected:
                    self.value_le.setText(str(self.device.read(1, Pn)))
    
    @Slot(str)
    def update_prm_list(self, category:str):
        self.parameter_cb.clear()
        for elm in self.all_desc[category]:
            self.parameter_cb.addItem(elm['function'])
        self.update_description(self.parameter_cb.currentText())
            
    @Slot(str)
    def update_description(self, prm_name:str):
        category = self.category_cb.currentText()
        current_prm_idx = self.parameter_cb.currentIndex()
        self.reboot_le.setText(self.all_desc[category][current_prm_idx]['reboot'])
        self.description_te.setText(self.all_desc[category][current_prm_idx]['description'])
        self.range_low_le.setText(str(self.all_desc[category][current_prm_idx]['range'][0]))
        self.range_high_le.setText(str(self.all_desc[category][current_prm_idx]['range'][1]))
        self.default_le.setText(self.all_desc[category][current_prm_idx]['default'])
        self.unit_le.setText(self.all_desc[category][current_prm_idx]['unit'])
        self.apply_le.setText(self.all_desc[category][current_prm_idx]['apply'])
        
        self.read_value()
        
if __name__ == "__main__":
    app = QApplication([])
    window = DescWindow()
    # window.connect_device('COM7')
    window.show()
    sys.exit(app.exec())
