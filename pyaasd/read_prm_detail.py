import os, sys

from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import loadUiType
from PySide6.QtCore import Slot

this_dir=os.path.dirname(os.path.abspath(__file__))
root_dir=os.path.dirname(this_dir)
# sys.path.insert(1, os.path.join(root_dir, 'pyaasd/ui'))
docs_dir=os.path.join(root_dir, 'docs')

txtfilepath=os.path.join(docs_dir, 'prms_detail')

class PrmsDetail:
    def __init__(self, filepath=txtfilepath) -> None:
        file1 = open(filepath, 'r')
        self.Lines = file1.readlines()

    def read_detail(self)-> list:
        prms_detail={}
        for line in self.Lines[1:]:
            if line.startswith('## '):
                prms_detail[line.strip("##").strip()] = []
            elif line.startswith('& Pn'):
                temp = line.split('& ')[-1].split(";")
                # try:
                range_txt=temp[3].split("-")
                if len(range_txt) > 2:
                    i=temp[3][1:].index('-')
                    v_min_t = temp[3][:i+1]
                    v_max_t = temp[3][i+2:]
                else:
                    v_min_t = range_txt[0]
                    v_max_t = range_txt[-1]
                if '.' in temp[3]:
                    range_v = [float(v_min_t), float(v_max_t)]
                else:
                    # try:
                    range_v = [int(v_min_t), int(v_max_t)]
                    # except ValueError:
                    #     print(temp)
                    #     return
                value = {'function': temp[0],
                        'reboot':temp[1],
                        'description': temp[2]+'\n',
                        'range': range_v,
                        'default': temp[4],
                        'unit': temp[5],
                        'apply': temp[6]}
                # except IndexError:
                #     print(temp)
                #     return
                prms_detail[list(prms_detail.keys())[-1]].append(value)
            else:
                # try:
                prms_detail[list(prms_detail.keys())[-1]][-1]['description']+=line
                # except IndexError:
                #     print('ERROR at: \n', line)
                #     return
        return prms_detail

Form, Base = loadUiType( os.path.join(root_dir, 'pyaasd/ui/prm_description.ui'))
class DescWindow(Form, Base):
    def __init__(self, parent=None):
        super(DescWindow, self).__init__(parent)
        self.setupUi(self)
        prms_d=PrmsDetail(txtfilepath)
        self.all_desc=prms_d.read_detail()
        self.initUi()
        self.connect_signals()
        
    def connect_signals(self):
        self.category_cb.currentTextChanged.connect(self.update_prm_list)
        self.parameter_cb.currentTextChanged.connect(self.update_description)
        
    def initUi(self):
        for key in self.all_desc.keys():
            self.category_cb.addItem(key)
        self.update_prm_list(self.category_cb.currentText())
            
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
        
if __name__ == "__main__":
    # prms_d=PrmsDetail(txtfilepath)
    # d=prms_d.read_detail()
    # list_keys = list(d.keys())
    # # print(list_keys)
    # for item in d.items():
    #     print( len(item[1]), [ item[1][0]['function'], item[1][-1]['function'] ] )
    app = QApplication([])
    window = DescWindow()
    window.show()
    sys.exit(app.exec())
