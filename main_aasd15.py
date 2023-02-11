from typing import Dict, List, Any
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import (QPoint, QSize, QSettings)

import sys
sys.path.append('..')
from ui_brooks import Ui_FControl

from hardware.parametertree_utils import (ControllerParameterTree, \
    available_ports, flow_rate_unit_codes, dict_parities,dict_stopbits)
from hardware.brooks.brooks_s_protocol_serial_backend import Brooks, serial

MAX_INSTANCE_NUMBER = 10

class FControl(Ui_FControl, ControllerParameterTree):
    def __init__(self, fcontrol_params: List[Dict[str, Any]]) -> None:
        """[summary]

        Args:
            fcontrol_params (List[Dict[str, Any]]): [description]
        """     
        super(FControl, self).__init__(controller_params=fcontrol_params)   
        self.setupUi(self)
        self.isConnected = False
        
        self.add_parametertree(self.gridLayout_3)
        #remove line_color:
        self.settings.param('main_settings', 'line_color').remove()
        
        self.default_params()
                
        self.readSettings()
        
        self.connectSignals()
        
        #create widgets list:
        self.widgets_lcdPvs = [self.lcdPv_1, self.lcdPv_2, self.lcdPv_3,
                            self.lcdPv_4, self.lcdPv_5, self.lcdPv_6, 
                            self.lcdPv_7, self.lcdPv_8, self.lcdPv_9,
                            self.lcdPv_10]
        self.widgets_spSets = [self.sp_1, self.sp_2, self.sp_3, self.sp_4,
                            self.sp_5, self.sp_6, self.sp_7, self.sp_8,
                            self.sp_9, self.sp_10]
        
        #create member lists:
        self.mfcs = [None] * MAX_INSTANCE_NUMBER
        self.list_tags = [None] * MAX_INSTANCE_NUMBER
        self.list_fs = [None] * MAX_INSTANCE_NUMBER
        self.list_units = [None] * MAX_INSTANCE_NUMBER
        self.list_sps = [None] * MAX_INSTANCE_NUMBER
        self.list_pvs = [None] * MAX_INSTANCE_NUMBER
        
    def default_params(self):
        self.settings.param('main_settings', 'Device Interface', 
                            'link_interface').setValue('Serial')
        self.settings.param('main_settings', 'Device Interface', 
                            'link_interface', 'serial', 
                            'serial_type').setValue(1)
        self.settings.param('main_settings', 'Device Interface', 
                            'link_interface', 'serial', 
                            'baudrate').setValue(4)
        self.settings.param('main_settings', 'Device Interface', 
                            'link_interface', 'serial', 
                            'bytesize').setValue(8)
        self.settings.param('main_settings', 'Device Interface', 
                            'link_interface', 'serial', 'parity').setValue(2)
        self.settings.param('main_settings', 'Device Interface', 
                            'link_interface', 'serial', 'stopbits').setValue(0)
    
    def init_controller(self):
        """Initialize the controller and get all data from it.
        """        
        print("init_controller from subclass TControl.")
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
            val = self.settings.param('main_settings', 
                                    'Device Interface', 
                                    'link_interface', 
                                    'serial', 
                                    'parity').value()
            txt = {v:k for k, v in dict_parities.items() if
                      v == val}[val]
            parity = serial.__getattribute__(txt)
            val = self.settings.param('main_settings', 
                                    'Device Interface', 
                                    'link_interface', 
                                    'serial', 
                                    'stopbits').value()
            txt = {v:k for k, v in dict_stopbits.items() if
                      v == val}[val]
            stopbits = serial.__getattribute__(txt)
            read_timeout = self.settings.param('main_settings', 
                                               'Device Interface', 
                                               'link_interface', 
                                               'serial', 
                                               'read_timeout').value()
            
            #instance 10*Brooks...
            #! Warning: need check port: close() if is_open()
            try:
                self.uartdriver = serial.Serial(port=portname, baudrate=baud, 
                                       bytesize=databits, parity=parity, 
                                       stopbits=stopbits, timeout=read_timeout, 
                                       )            
            except IOError:
                self.uartdriver.close()
                self.uartdriver = serial.Serial(port=portname, baudrate=baud, 
                                       bytesize=databits, parity=parity, 
                                       stopbits=stopbits, timeout=read_timeout, 
                                       )
            
            #read data and update device settings parameters:
            for i in range(MAX_INSTANCE_NUMBER):
                self.list_tags = self.settings.child(
                    'device_settings', 'mfc_' + str(i), 'tag').value()
                self.list_fs = self.settings.child(
                    'device_settings', 'mfc_' + str(i), 'fs').value()
                self.list_fs = self.settings.child(
                    'device_settings', 'mfc_' + str(i), 'fs').value()
                self.list_units = self.settings.child(
                    'device_settings', 'mfc_' + str(i), 'unit').value()
                self.list_sps = self.settings.child(
                    'device_settings', 'mfc_' + str(i), 'sp').value()
                
                #prefix name:
                self.widgets_spSets[i].setPrefix(
                    self.settings.child('device_settings',
                                        'mfc_' + str(i),
                                        'gase_name').value() + ' = '
                                        )
                
                #init Brooks MFC
                if self.list_tags[i].split():
                    self.mfcs[i] = Brooks(self.uartdriver, self.list_tags[i])
                    if self.mfcs[i].long_address != 'Error':
                        #fullscale:
                        self.list_fs[i], self.list_units[i] = \
                            self.mfcs[i].get_flow_range()
                        self.settings.child('device_settings', 
                                            'mfc_' + str(i), 
                                            'fs').setValue(
                                                self.list_fs[i])
                        self.widgets_spSets[i].setMaximum(self.list_fs[i])
                
                        # setpoint and unit:
                        self.list_sps[i], self.list_units[i] = \
                            self.mfcs[i].get_setpoint()
                        self.settings.child('device_settings', 
                                            'mfc_' + str(i), 
                                            'sp').setValue(
                                                self.list_sps[i])
                        self.widgets_spSets[i].setValue(self.list_sps[i])
                        self.settings.child('device_settings', 
                                            'mfc_' + str(i), 
                                            'unit').setValue(
                                                self.list_units[i])
                        self.widgets_spSets[i].setSuffix(
                            ' ' + self.list_units[i])
                
                        #process variable:
                        self.list_pvs[i] = self.mfcs[i].get_flow()
                        self.widgets_lcdPvs[i].setValue(self.list_pvs[i])
                
                        #totalizers
                    else:
                        raise Exception('ERROR: tag or unknown!')
                
    def grab_data(self):
        print('read all pvs...')
        if self.isConnected:
            for i in range(MAX_INSTANCE_NUMBER):
                self.list_pvs[i] = self.mfcs[i].get_flow()
                self.widgets_lcdPvs[i].setValue(self.list_pvs[i])
                    
    def connectSignals(self) -> None:
        if self.isConnected:
            for i in range(MAX_INSTANCE_NUMBER):
                self.settings.param('device_settings', 'mfc_' + str(i), \
                    'totalizer', 'reset').sigActivated.connect(
                        self.mfcs[i].set_totalizer(2))
    
    # implementing slots
    
    # end actions
    def closeEvent(self, event):
        self.writeSettings()
        
    def readSettings(self):
        settings = QSettings("MKS 651C", "Pressure Controller")
        pos = settings.value("pos", QPoint(200, 200))
        size = settings.value("size", QSize(400, 400))
        self.resize(size)
        self.move(pos)

    def writeSettings(self):
        settings = QSettings("MKS 651C", "Pressure Controller")
        settings.setValue("pos", self.pos())
        settings.setValue("size", self.size())
        
    ## If anything changes in the tree, print a message
    #? Better way to share global state? I Reimplement these methods
    def change(self, param, changes):
        print("tree changes:")
        for param, change, data in changes:
            path = self.settings.childPath(param)
            if path is not None:
                childName = '.'.join(path)
            else:
                childName = param.name()
            print('  parameter: %s'% childName)
            print('  change:    %s'% change)
            print('  data:      %s'% str(data))
            print('  ----------')
            if childName == 'main_settings.show_data':
                self.start_DAQ() if data else self.stop_DAQ()
            if childName.startswith('device_settings.mfc_'):
                idx = int(childName.split(
                    'device_settings.mfc_')[1].split('.')[0])
                var = childName.split('.')[-1]
                if var == 'tag':
                    self.list_tags[idx] = data
                elif var == 'gase_name':
                    self.widgets_spSets[idx].setPrefix(data + ' = ')
                elif var == 'fs':
                    self.widgets_spSets[idx].setMaximum(data)
                elif var == 'unit':
                    self.mfcs[idx].set_flow_unit(data)
                    self.list_units[idx] = data
                    self.widgets_spSets[idx].setSuffix(' ' + data)
                elif var == 'sp':
                    self.mfcs[idx].set_flow(data)
                    self.list_sps[idx] = data
                    self.widgets_spSets[idx].setValue(data)
                elif var == 'reset':
                    val = self.mfcs[idx].get_totalizer()[0]
                    self.settings.child('device_settings', 
                                        'mfc_' + str(idx),
                                        'totalizer').setValue(val)
                else:
                    pass

    def valueChanging(param, value):
        print("Value changing (not finalized): %s %s" % (param, value))
    
    def save(self):
        global state
        state = self.settings.saveState()

    def restore(self):
        #?duplicate from parent class! I don't know how to share global state!
        global state
        add = self.settings['Save/Restore functionality', 'Restore State', 'Add missing items']
        rem = self.settings['Save/Restore functionality', 'Restore State', 'Remove extra items']
        self.settings.restoreState(state, addChildren=add, removeChildren=rem)
        
if __name__ == "__main__":
    
    list_mfc_settings =[]
    for i in range(MAX_INSTANCE_NUMBER):
        list_mfc_settings += [
            {'title': 'MFC ' + str(i), 'name': 'mfc_' + str(i), 'type': 'group', 'children':[
                {'title': 'Tag:', 'name': 'tag', 'type': 'str',},
                {'title': 'Gase:', 'name': 'gase_name', 'type': 'str', 'value': 'gase_' + str(i)},
                {'title': 'Line Color:', 'name': 'line_color', 'type': 'color', 'value': "FF0", 'tip': "lineplot color"},
                {'title': 'Full Scale:', 'name': 'fs', 'type': 'float', 'readonly': True,},
                {'title': 'Unit:', 'name': 'unit', 'type': 'list', 'values': flow_rate_unit_codes,},
                {'title': 'Setpoint:', 'name': 'sp', 'type': 'float',},
                {'title': 'Totalizer:', 'name': 'totalizer', 'type': 'float', 'readonly': True, 'children': [
                    {'title': 'Reset Totalizer', 'name': 'reset', 'type': 'action'},
                ]}
            ]}]
            
    fcontrol_params = [
        {'title': 'MFCs Settings', 'name': 'device_settings', 'type': 'group', 'children': list_mfc_settings},
    ]
    
    app = QtGui.QApplication([])
    Form = FControl(fcontrol_params)
    Form.show()
    
    ## test save/restore
    state = Form.settings.saveState()
    Form.settings.restoreState(state)   
    
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
        #sys.exit(app.exec_())