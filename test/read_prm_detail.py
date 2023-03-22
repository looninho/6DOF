import os
test_dir=os.path.dirname(os.path.abspath(__file__))
root_dir=os.path.dirname(test_dir)
docs_dir=os.path.join(root_dir, 'docs')

txtfilepath=os.path.join(docs_dir, 'prms_detail')

# f=open('prms_detail.txt', 'r')
# fw=open('prms_detail2', 'w')

# while 1:
#     line = f.readline()
#     if line == '&\n':
#         line2 = '& ' + f.readline()
#         fw.write(line2)
#     else:
#         fw.write(line)

# f.close()
# fw.close()

class PrmsDetail:
    def __init__(self, filepath) -> None:
        file1 = open(filepath, 'r')
        self.Lines = file1.readlines()

    def read_detail(self)-> list:
        prms_detail={}
        for line in self.Lines:
            if line.startswith('## '):
                prms_detail[line.strip("##").strip()] = []
            if line.startswith('& Pn'):
                temp = line.split('& ')[-1].split(";")
                try:
                    range_txt=temp[3].split("-")
                    if len(range_txt) > 2:
                        i=temp[3][1:].index('-')
                        v_min_t = temp[3][:i+1]
                        v_max_t = temp[3][i+2:]
                    else:
                        v_min_t = range_txt[0]
                        v_max_t = range_txt[0]
                    if '.' in temp[3]:
                        range_v = [float(v_min_t), float(v_max_t)]
                    else:
                        try:
                            range_v = [int(v_min_t), int(v_max_t)]
                        except ValueError:
                            print(temp)
                            return
                    value = {'function': temp[0],
                            'reboot':temp[1],
                            'description': temp[2],
                            'range': range_v,
                            'default': temp[4],
                            'unit': temp[5],
                            'apply': temp[6]}
                except IndexError:
                    print(temp)
                    return
                prms_detail[list(prms_detail.keys())[-1]].append(value)
        return prms_detail

if __name__ == "__main__":
    prms_d=PrmsDetail(txtfilepath)
    d=prms_d.read_detail()
    [print(key) for key in d.keys()]