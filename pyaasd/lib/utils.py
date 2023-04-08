import os

this_dir=os.path.dirname(os.path.abspath(__file__)) # lib
root_dir=os.path.dirname(os.path.dirname(this_dir))
# sys.path.insert(1, os.path.join(root_dir, 'pyaasd/ui'))
docs_dir=os.path.join(root_dir, 'docs')

parmtxt=os.path.join(docs_dir, 'prms_detail')

def to_children(item_list):
    children=[]
    for item in item_list:
        default= 0 if item['default'] == 'Rated speed' else item['default']
        child={
            'title': item['function'].lower() + " "*4,
            'name': item['function'].lower().replace(' ', '_'),
            'type': 'float' if '.' in item['range'] else 'int', #TODO for key 'type': list or group if not continous values
            'default': float(default) if '.' in item['range'] else int(float(default)),
            'suffix': item['unit'], 
            'tip': item['description'],
        }
        children.append(child)
    return children

def SigIn_gen():
    keyList = [ # 31 keys
        'Sen', 'Punlock', 'Pdistance', 'Psource', 
        'Pstop', 'Ptrigger', 'Pos2', 'Pos1', 
        'REF', 'GOH', 'PC', 'INH', 
        'Pclear', 'Cinv', 'GN2', 'GN1', 
        'Cgain', 'Cmode', 'TR2', 
        'TR1', 'Sp3', 'Sp2', 'Sp1', 
        'ZeroLock', 'EMG', 'TCW', 'TCCW', 
        'CWL', 'CCWL', 'AlarmRst', 'SON',          
    ]
    SigIn = {key: None for key in keyList}
    return SigIn

def SigOut_gen():
    keyList = [ # 13 keys
        'TCMDreach', 'SPL', 'TQL', 'Pnear', 'HOME', 'BRK', 'Run',
        'ZerpSpeed', 'Treach', 'Sreach', 'Preach', 'Ready', 'Alarm'
    ]
    SigOut = {key: None for key in keyList}
    return SigOut



class PrmsDetail:
    def __init__(self, filepath=parmtxt) -> None:
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


