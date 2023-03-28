import sys, os
from typing import Dict, List, Any

from PySide6.QtWidgets import QApplication, QGridLayout
from PySide6.QtUiTools import loadUiType
from PySide6.QtCore import Slot

this_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(this_dir, 'lib')
root_dir=os.path.dirname(this_dir)
sys.path.insert(1, lib_dir)

Form, Base = loadUiType( os.path.join(root_dir, 'pyaasd/ui/aasd_test.ui'))

from lib.parametertree_utils import (ControllerParameterTree, \
    available_ports, dict_parities, dict_stopbits)
from sync_pyaasd import Sync_AASD_15A

MAX_SLAVE_NUMBER = 6

class AASDControl(ControllerParameterTree, Form, Base):
    def __init__(self, aasdcontrol_params: List[Dict[str, Any]]) -> None:
        super(AASDControl, self).__init__(controller_params=aasdcontrol_params)
        self.setupUi(self)
        layout= QGridLayout()
        self.comm_tab.setLayout(layout)
        self.add_parametertree(layout)
        #remove line_color:
        self.settings.param('main_settings', 'line_color').remove()

if __name__ == "__main__":
    from lib.read_prm_detail import PrmsDetail, to_children
    
    prms_d=PrmsDetail()
    d=prms_d.read_detail()
    all_params = []
    for key, item in d.items():
        params={'title': key,
                'name': key.replace(' ', '_'), 
                'expanded': False,
                'type': 'group',
                'children': to_children(item),}
        all_params.append(params)
    
    list_aasd_settings = []
    for i in range(MAX_SLAVE_NUMBER):
        list_aasd_settings += [
            {
                'title': 'Servo '+str(i+1), 
                'name': 'servo_'+str(i+1), 
                'expanded': False, 
                'type': 'group', 
                'children': all_params
            }
        ]
    controller_params = [
        {'title': '6DOF Settings', 'name': 'device_settings', 'expanded': False, 'type': 'group', 'children': list_aasd_settings},
    ]
    
    app = QApplication([])
    Form = AASDControl(controller_params)
    Form.show()
    
    ## test save/restore
    state = Form.settings.saveState()
    Form.settings.restoreState(state)   
    sys.exit(app.exec())
    
    # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #     QtWidgets.QApplication.instance().exec()