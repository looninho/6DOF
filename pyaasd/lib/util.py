# using synchronous client

def read_holding_register(mb_addr, client, slave=1):
    rr = client.read_holding_registers(mb_addr, 1, slave=slave)
    num = rr.getRegister(0)
    # convert to 32-bit signed integer
    if num & (1 << 15):
        num = -((num ^ 0xffff) + 1)
    return num

def write_register(mb_addr, val, client, slave=1):
    # signed integer to unsigned
    usval = val & 0xffff
    client.write_register(mb_addr, usval, slave=slave)
    
def read_16bits(val):
    return bin(val).replace('0b', '').zfill(15)

def change_bitN(Pn, bit_pos, value=1):
    val =  read_holding_register(Pn) # int number
    register = read_16bits(val) # bin format
    list_reg = list(register) # convert to list to change bit10
    list_reg[15-bit_pos-1]=str(value) # set bit10 to 1
    reg=''
    for elm in list_reg:
        reg += elm
    val = int(reg, 2) # re-convert to int
    write_register(Pn, val)
    return val

def trigger(Pn=71, bit_pos=10, raising=True):
    val =  read_holding_register(Pn)
    register = read_16bits(val)
    list_reg = list(register)
    if raising:
        if list_reg[15-bit_pos-1]=='1':
            change_bitN(Pn, bit_pos, 0)
        else:
            change_bitN(Pn, bit_pos, 1)
    else:
        if list_reg[15-bit_pos-1]=='0':
            change_bitN(Pn, bit_pos, 1)
        else:
            change_bitN(Pn, bit_pos, 0)
    return 0

