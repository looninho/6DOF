import sys, os
from typing import Dict, List, Any

from PySide6.QtWidgets import QApplication, QGridLayout
from PySide6.QtUiTools import loadUiType
from PySide6.QtCore import Slot

this_dir = os.path.dirname(os.path.abspath(__file__))
root_dir=os.path.dirname(this_dir)
sys.path.insert(1, os.path.join(root_dir, 'pyaasd'))
sys.path.insert(1, os.path.join(root_dir, 'pyaasd/resources'))

from pyaasd.lib.parametertree_utils import ControllerParameterTree
import resources_rc
from pyaasd.sync_pyaasd import Sync_AASD_15A
from pyaasd.lib.utils import to_group_prms

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
        self.parametertree = ControllerParameterTree(controller_params)
        self.parametertree.add_parametertree(layout)
        #remove line_color:
        self.parametertree.settings.param('main_settings', 'line_color').remove()
        # self.settings.param('main_settings', 'line_color').setOpts(visible=False)
        self.firstcall=True
        # self.connectSignals()

    def init_controller(self):
        """Initialize the controller and get all data from it.
        """        
        print("init_controller from subclass AASDControl.")
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
                        'name': cat.replace(' ', '_'), 
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
                        'children': groups
                    }
                ]
                self.settings.params('device_settings').addChildren(aasd_settings)
                self.settings.params('device_settings',
                                     'servo_'+str(servo_number)
                                    ).addChildren(groups)
        self.firstcall = False

            #TODO: update parametertree
            #! Warning: need check port: close() if is_open()
            # try:
            #     self.uartdriver = serial.Serial(port=portname, baudrate=baud, 
            #                            bytesize=databits, parity=parity, 
            #                            stopbits=stopbits, timeout=read_timeout, 
            #                            )            
            # except IOError:
            #     self.uartdriver.close()
            #     self.uartdriver = serial.Serial(port=portname, baudrate=baud, 
            #                            bytesize=databits, parity=parity, 
            #                            stopbits=stopbits, timeout=read_timeout, 
            #                            )
            
            #read data and update device settings parameters:
            # for i in range(MAX_SLAVE_NUMBER):
            #     self.list_tags = self.settings.child(
            #         'device_settings', 'mfc_' + str(i), 'tag').value()
            #     self.list_fs = self.settings.child(
            #         'device_settings', 'mfc_' + str(i), 'fs').value()
            #     self.list_fs = self.settings.child(
            #         'device_settings', 'mfc_' + str(i), 'fs').value()
            #     self.list_units = self.settings.child(
            #         'device_settings', 'mfc_' + str(i), 'unit').value()
            #     self.list_sps = self.settings.child(
            #         'device_settings', 'mfc_' + str(i), 'sp').value()
                
            #     #prefix name:
            #     self.widgets_spSets[i].setPrefix(
            #         self.settings.child('device_settings',
            #                             'mfc_' + str(i),
            #                             'gase_name').value() + ' = '
            #                             )
                
            #     #init Brooks MFC
            #     if self.list_tags[i].split():
            #         self.mfcs[i] = Brooks(self.uartdriver, self.list_tags[i])
            #         if self.mfcs[i].long_address != 'Error':
            #             #fullscale:
            #             self.list_fs[i], self.list_units[i] = \
            #                 self.mfcs[i].get_flow_range()
            #             self.settings.child('device_settings', 
            #                                 'mfc_' + str(i), 
            #                                 'fs').setValue(
            #                                     self.list_fs[i])
            #             self.widgets_spSets[i].setMaximum(self.list_fs[i])
                
            #             # setpoint and unit:
            #             self.list_sps[i], self.list_units[i] = \
            #                 self.mfcs[i].get_setpoint()
            #             self.settings.child('device_settings', 
            #                                 'mfc_' + str(i), 
            #                                 'sp').setValue(
            #                                     self.list_sps[i])
            #             self.widgets_spSets[i].setValue(self.list_sps[i])
            #             self.settings.child('device_settings', 
            #                                 'mfc_' + str(i), 
            #                                 'unit').setValue(
            #                                     self.list_units[i])
            #             self.widgets_spSets[i].setSuffix(
            #                 ' ' + self.list_units[i])
                
            #             #process variable:
            #             self.list_pvs[i] = self.mfcs[i].get_flow()
            #             self.widgets_lcdPvs[i].setValue(self.list_pvs[i])
                
            #             #totalizers
            #         else:
            #             raise Exception('ERROR: tag or unknown!')
        
    def connectSignals(self):
        self.settings.param('main_settings', 'Device Interface', \
                    'connect_device').sigActivated.connect(
                        self.printmsg("hello Connect to device"))
    
    def printmsg(self, msg:str):
        print(msg)

if __name__ == "__main__":
    from lib.utils import get_all_params, PrmsDetail
            
    prms_d=PrmsDetail()
    d=prms_d.read_detail()
    all_params = get_all_params(d)
    
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
    
    
    Form = AASDControl()
    Form.show()

    ## test save/restore
    state = Form.settings.saveState()
    Form.settings.restoreState(state)
    
    sys.exit(app.exec())
    