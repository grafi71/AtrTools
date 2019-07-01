"""
This is converter of indexed gif files (1-8 colors) to Atari .asm data file.
Requires pillow package to be installed.
"""

import re
import argparse
import logging
import itertools
from collections import namedtuple

RGX = re.compile(r'([A-Z]*)\s"?([^"]*)')
MusicData = namedtuple('MucicData', 'address_start address_end music_data')


def log():
	return logging.getLogger(__name__)

    
class AtariSAPConverter:
    def __init__(self, args):
        self.args=args
        self.sap=args.source.read()
        self.header = {}
        self.labels = {}
        self.data = []

    def process(self):
        index = self.sap.index(b'\xff\xff')
        logging.debug("Binary index: %d ; Data total length: %d", index, len(self.sap))
        header = self.sap[0: index].decode()
        for line in header.split('\r\n'):
            match = RGX.match(line)
            if match:
                k = match.group(1).upper()
                v  = match.group(2).upper()
                if k in self.args.labels:
                    self.labels[k] = v
                else:
                    self.header[k] = v
        index +=2
        while True:
            beg_byte_low, beg_byte_high = self.sap[index:index+2]
            index += 2
            end_byte_low, end_byte_high = self.sap[index:index+2]
            index += 2
            address_start = "{:02x}{:02x}".format(beg_byte_high, beg_byte_low)
            address_end = "{:02x}{:02x}".format(end_byte_high, end_byte_low)
            size_bytes = (end_byte_high*256+end_byte_low)-(beg_byte_high*256+beg_byte_low)
            logging.debug("Start address: %s ; End address: %s ; Size: %d",address_start, address_end, size_bytes)
            self.data.append(MusicData(address_start=address_start,
                                       address_end=address_end, music_data=self.sap[index: index+size_bytes+1]))
            index += size_bytes
            if index == len(self.sap)-1:
                break

    def generate_music_data(self, data):
        buf = []
        for i in data:
            buf.append(i)
            if len(buf)==20:
                bts = ['${:02x}'.format(n) for n in buf]
                yield ".byte {}".format(','.join(bts))
                buf = []
        if buf:
            bts = ['${:02x}'.format(n) for n in buf]
            yield ".byte {}".format(','.join(bts))

    def save(self):
        for k in self.labels:
                print('SAP_MUSIC_{} = ${}'.format(k, self.labels[k]), file=self.args.destination)
        print("\n\t.local sap_music_header", file=self.args.destination)
        for k in self.header:
                print('{}\t.byte "{}"'.format(k, self.header[k]), file=self.args.destination)
        print("\t.endl", file=self.args.destination)

        for idx, data in enumerate(self.data):
            print("\n\torg ${}\n".format(data.address_start), file=self.args.destination)
            print("\t.local sap_music_data{} ; start={}, end={}".format(idx, data.address_start, 
                                                                 data.address_end), 
                                                                 file=self.args.destination)
            gen_data = self.generate_music_data(data.music_data)
            for row in gen_data:
                print("\t{}".format(row), file=self.args.destination)
            print("\t.endl", file=self.args.destination)

            if self.args.out:
                self.args.out.write(data.music_data)

def add_parser_args(parser):
    parser.add_argument('source', type=argparse.FileType('rb'), help='path to source sap file')
    parser.add_argument('destination', type=argparse.FileType('w'), help='path to destination asm file')
    parser.add_argument('-l', '--labels', nargs='+', default=['INIT', 'PLAYER'], help='labelled header keys', required=False)
    parser.add_argument('-o', '--out', type=argparse.FileType('wb'), help='path to binary output file')

def get_parser():
    parser = argparse.ArgumentParser()
    add_parser_args(parser)
    return parser

def process(args):
    sap_converter = AtariSAPConverter(args)
    sap_converter.process()
    sap_converter.save()

def main():
    parser = get_parser()
    args = parser.parse_args()
    process(args)

if __name__ == '__main__':
    main()
