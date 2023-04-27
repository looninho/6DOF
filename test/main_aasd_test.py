import sys, os
from typing import Dict, List, Any

from PySide6.QtWidgets import QApplication, QGridLayout
from PySide6.QtUiTools import loadUiType
from PySide6.QtCore import Slot

this_dir = os.path.dirname(os.path.abspath(__file__))
root_dir=os.path.dirname(this_dir)
sys.path.insert(1, os.path.join(root_dir, 'pyaasd'))
sys.path.insert(1, os.path.join(root_dir, 'pyaasd/resources'))

from lib.parametertree_utils import ControllerParameterTree
import resources_rc
from sync_pyaasd import Sync_AASD_15A
from lib.utils import to_group_prms

MAX_SLAVE_NUMBER = 1

Form, Base = loadUiType( os.path.join(root_dir, 'pyaasd/ui/aasd_test.ui'))
class AASDControl(ControllerParameterTree, Form, Base):
    def __init__(self, aasdcontrol_params:List[Dict[str, Any]]=[]) -> None:
        if not aasdcontrol_params:
            aasdcontrol_params = [{
                'title': '6DOF Settings', 
                'name': 'device_settings', 
                'expanded': False, 
                'type': 'group', 
                'children': []}, 
            ]
        super(AASDControl, self).__init__(controller_params=aasdcontrol_params)
        self.setupUi(self)
        layout= QGridLayout()
        self.settings_tab.setLayout(layout)
        # self.parametertree = ControllerParameterTree(controller_params)
        self.add_parametertree(layout)
        #remove line_color:
        self.settings.param('main_settings', 'line_color').remove()
        # self.settings.param('main_settings', 'line_color').setOpts(visible=False)
        self.firstcall=True
        self.connectSignals()

    def init_controller(self):
        """Initialize the controller and get all data from it.
        """        
        print("init_controller from subclass AASDControl.")
        # for serial connection:
        if self.settings.param('main_settings', 'Device Interface', 
                               'link_interface').value() == 'Serial':
            portname = self.settings.param('main_settings', 
                                           'Device Interface', 
                                           'link_interface', 
                                           'serial', 
                                           'comport').value()
            baud = self.settings.param(
                'main_settings', 
                'Device Interface', 
                'link_interface', 
                'serial', 
                'baudrate').value()
            databits = self.settings.param(
                'main_settings', 
                'Device Interface', 
                'link_interface', 
                'serial', 
                'bytesize').value()
            parity = self.settings.param(
                'main_settings', 
                'Device Interface', 
                'link_interface', 
                'serial', 
                'parity').value()            
            stopbits = self.settings.param(
                'main_settings', 
                'Device Interface', 
                'link_interface', 
                'serial', 
                'stopbits').value()              
            read_timeout = self.settings.param(
                'main_settings', 
                'Device Interface', 
                'link_interface', 
                'serial', 
                'read_timeout').value()
            
            # instantiate Servo drivers...
            self.device = Sync_AASD_15A(
                port=portname, 
                # framer=ModbusRtuFramer, 
                baudrate=baud, 
                bytesize=databits, 
                parity=parity, 
                stopbits=stopbits, 
                strict=False,
                n_motors=MAX_SLAVE_NUMBER
            )
            
            # start read parms
            self.read_prms()                
            
            self.settings.child(
                'main_settings', 
                'Device Interface', 
                'connect_device'
            ).setValue(self.device.client.connected)
            
    def read_prms(self):
        if hasattr(self, "device"):
            self.device.refresh()
            if self.firstcall:
                self.create_parametertree()
    
    def create_parametertree(self):
        if self.firstcall:
            list_6dof_settings = []
            for servo_number in range(1,MAX_SLAVE_NUMBER+1):
                # create groups of 5 categories
                groups = []
                for cat, d in zip(
                    self.device.settings.descriptions.keys(),
                    [
                        self.device.settings.system_prms[servo_number],
                        self.device.settings.position_prms[servo_number],
                        self.device.settings.speed_prms[servo_number],
                        self.device.settings.torque_prms[servo_number],
                        self.device.settings.extended_prms[servo_number]
                    ]
                ):
                    groups += [{
                        'title': cat,
                        'name': cat.lower().replace(' ', '_'), 
                        'expanded': False,
                        'type': 'group',
                        'children': to_group_prms(d) # PnXXX functions and desxcriptions
                    }]
                aasd_settings = [
                    {
                        'title': 'Servo '+str(servo_number), 
                        'name': 'servo_'+str(servo_number), 
                        'expanded': False, 
                        'type': 'group', 
                        # 'children': all_params
                        'children': []
                    }
                ]
                self.settings.param('device_settings').addChildren(aasd_settings)
                self.settings.param('device_settings',
                                     'servo_'+str(servo_number)
                                    ).addChildren(groups)
        self.firstcall = False
        
    def connectSignals(self):
        #TODO: create signals nd connect: valueChanged, etc.
        pass
        # self.settings.param('main_settings', 'Device Interface', \
        #             'connect_device').sigActivated.connect(
        #                 self.printmsg("hello Connect to device"))
    
    def printmsg(self, msg:str):
        print(msg)

if __name__ == "__main__":    
    app = QApplication([])
    
    Form = AASDControl()
    Form.show()

    ## test save/restore
    state = Form.settings.saveState()
    Form.settings.restoreState(state)
    
    sys.exit(app.exec())
    