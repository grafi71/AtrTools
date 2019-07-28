"Simple compression routine."

import logging
import lz4.frame

from atrtools.uncompress import (UncompressLegacy, UncompressLz4)


def log():
    return logging.getLogger(__name__)


class Compress:
    "Generic compress class"

    def __init__(self, data):
        "Construct object from byte data."
        self.data = data
        self.len = len(data)
        
    def compress(self):
        "Generic compress class"
        raise NotImplementedError('This method is not implemented')

    @classmethod
    def create_compressor(cls, name):
        return {'legacy': LegacyCompress, 'lz4': Lz4Compress}[name]


class Lz4Compress(Compress):
    
    LZ4_SKIP_FIRST = 11
    LZ4_SKIP_LAST = 0

    def compress(self):
        "Compress using lz4 algorithm"
        log().debug('Lz4 compression')
        data = self.data

        if len(data)<=4096:
            input_data = data
        else:
            input_data = data[:4080] + bytearray(0 for i in range(16)) + data[4080:]
        compressed = lz4.frame.compress(input_data, block_linked=False, return_bytearray=True, 
                                        store_size=False)
        if self.__class__.LZ4_SKIP_FIRST:
            compressed = compressed[self.__class__.LZ4_SKIP_FIRST:]
        if self.__class__.LZ4_SKIP_LAST:
            compressed = compressed[:-self.__class__.LZ4_SKIP_LAST]
        return compressed

    @classmethod
    def uncompress(cls):
        "Return 6502 uncompress routine"
        return UncompressLz4()


class LegacyCompress(Compress):
    "Legacy compress class"

    def __pack(self):
        "Compress data"
        compressed = []
        idx = 0
        while idx < self.len-1:
            cnt = 0
            while idx < self.len-1 and self.data[idx] == self.data[idx+1]:
                cnt += 1
                idx += 1
            if cnt:
                compressed.append(RepeatedValues(self.data[idx], cnt+1))
                idx += 1 
            else:
                buf = []
                while idx < self.len-1 and self.data[idx] != self.data[idx+1]:
                    buf.append(self.data[idx])
                    idx += 1
                if buf:
                    compressed.append(UniqueValues(buf))
        
        if idx != self.len:
            lst = self.data[-1]
            if compressed:
                if not compressed[-1].adjust_last(lst):
                    compressed.append(UniqueValues([lst]))
            else:
                compressed.append(UniqueValues([lst]))
        
        return compressed

    def compress(self):
        "Compress and export data to bytearray"
        log().debug('Legacy compression')
        packed = []
        compressed = self.__pack()
        for data in compressed:
            data.export(packed)
        return bytearray(packed)

    @classmethod
    def uncompress(cls):
        "Return 6502 uncompress routine"
        return UncompressLegacy()


class RepeatedValues:
    "Type for single value repeated."

    def __init__(self, value, repeats):
        self.value = value
        self.repeats = repeats

    def __repr__(self):
        return '{}(value={},repeats={})'.format(self.__class__.__name__, self.value, self.repeats)

    def export(self, table):
        "Export compressed values to buffer table"
        cmd = 128 if not self.value else 64

        for _ in range(0, self.repeats//cmd):
            table.append(0b00000000 if not self.value else 0b10000000) # 64 or 128 repeats
            if self.value: 
                table.append(self.value)

        rst = self.repeats%cmd
        if rst:
            table.append(0b00000000|rst if not self.value else 0b10000000|rst) # 64 or 128 repeats
            if self.value:
                table.append(self.value)

    def adjust_last(self, value):
        "Cannot adjust"
        return False

class UniqueValues:
    "Type for set of unique values."

    def __init__(self, values):
        self.values = values

    def __repr__(self):
        return '{}(values={})'.format(self.__class__.__name__, self.values)

    def export(self, table):
        "Export compressed values to buffer table"
        idx = 0
        for _ in range(0, len(self.values)//64):
            table.append(0b11000000) # 64 repeats
            table.extend(self.values[idx:idx+64])
            idx += 64
        rst = len(self.values)%64
        if rst:
            table.append(0b11000000 | rst)
            table.extend(self.values[idx:])
           
    def adjust_last(self, value):
        "Append value to values"
        self.values.append(value)
        return True
