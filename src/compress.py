from collections import namedtuple

UniqueValues = namedtuple('UniqueValues', 'values')
SameValues = namedtuple('SameValues', 'value', 'repeats')

data_to_compress = b'\0\0\0\1\2\2\3\4\5\6\7\7\7\0\1\1'
compressed = []

buff_same = []
buff_diff = []

for val in data_to_compress:
    if len(buff_same)==1: # start
        buff_same.append(val)
        buff_diff.append(val)
    else:
        if buff_same[-1] == val: # check if next value is the same
            buff_same.append(val)
        else:                   # we have different value
            if len(buff_same)>1:    # check if same buffer is not empty
                compressed.append(SameValues(value=buff_same[0], repeats=len(buff_same))
            else:
                


