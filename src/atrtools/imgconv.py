"""
This is converter of indexed gif files (1-8 colors) to Atari .asm data file.
Requires pillow package to be installed.
"""

import os
import argparse
import logging
import math
import itertools

from PIL import Image

from atrtools.compress import (LegacyCompress, Lz4Compress, Compress)

def log():
	return logging.getLogger(__name__)

class RGB2AtariColorConverter:
    "Convert RGB value to ATARI HUE/SAT"
    
    def __init__(self, hex_val):
        self.colors = (int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16))
        self.min_y = 0
        self.max_y = 0xe0
        self.colintens = 80
        self.colshift = 40
        self.calc = [0 for i in range(0,256)]
        self.rgb = [[0 for i in range(0,3)] for j in range(0,256)]
        self.value = self.convert()

    def convert(self):
        "Convert colors"
        ir, ig, ib = self.colors
        m = 0xFFFFF
        clip_var = lambda x: 0xff if x>0xff else (0 if x <0 else x)

        for i in range(0, 16):
            if not i:
                r=b=0
            else:
                angle = math.pi * (i * (1.0 / 7.0) - self.colshift * 0.01)
                r = math.cos(angle) * self.colintens
                b = math.cos(angle - math.pi * (2.0 / 3.0)) * self.colintens

            for j in range(0, 16):
                y = (self.max_y * j + self.min_y * (0xf - j)) / 0xf
                r1 = y + r
                g1 = y - r - b
                b1 = y + b
                r1 = clip_var(r1)
                g1 = clip_var(g1)
                b1 = clip_var(b1)

                self.rgb[i * 16 + j][0] = r1
                self.rgb[i * 16 + j][1] = g1
                self.rgb[i * 16 + j][2] = b1

        for i in range(0, 256):
            r2 = ir - self.rgb[i][0]
            r2 = r2 * r2
            g2 = ig - self.rgb[i][1]
            g2 = g2 * g2
            b2 = ib - self.rgb[i][2]
            b2 = b2 * b2
            self.calc[i] = r2 + g2 + b2

        for i in range(0, 256):
            if self.calc[i] < m:
                m = self.calc[i]
                j = i

        val =  (ir, ig, ib, j, j/16, j%16)
        log().debug("R=%3d G=%3d B=%3d : $%02X Hue = %d Lum = %d", *val)
        return val


class AtariImageConverter:
    "Atari image converter class"

    def __init__(self, args):
        self.args = args
        self.lines = []
        self.width = None
        self.height = None
        self.compressed = None
        self.compressor_cls = Compress.create_compressor(self.args.compressor)
        self.colors = []

    @property
    def bytes_per_line(self):
        return self.width / self.args.ratio
        
    def process(self):
        "Process image"
        log().debug('Processing image data')
        def color_generator():
            buffer = []
            for c in img.palette.palette:
                buffer.append(c)
                if len(buffer)==3:
                    yield "{:02x}{:02x}{:02x}".format(*buffer)
                    buffer = []

        lines = []
        img = Image.open(self.args.source)
        logging.debug("Image resolution: %dx%d", img.width, img.height)

        if self.args.verbose:
            print("Image resolution: {}x{}".format(img.width, img.height))
        
        self.width, self.height = (img.width, img.height)
        no_bytes = 0
        for vpos in range(0, img.height):
            line = []
            for hbyte in range(0, int(img.width/self.args.ratio)):
                bval = 0
                for i in range(0, self.args.ratio):
                    col = img.getpixel((hbyte*self.args.ratio+i, vpos))
                    bval <<= int(8/self.args.ratio)
                    bval |= col
                assert bval<256, "Error: byte value greater then 255, consider changing color ratio!"
                line.append(bval)
                no_bytes += 1
                if not (no_bytes+16)%4096:
                    line.extend(0 for _ in range(16))
            lines.append(line)
        self.lines = lines
        for color in color_generator():
            self.colors.append(color)
    
    # image.width / ratio = bytes per row

    def lines_to_bytearray(self):
        "Convert all lines to single bytearray" 
        data = bytearray()
        for i in self.lines:
            data.extend(i)
        return data

    def compress(self):
        "Compress routine"
        log().debug('Compressing image data')
        data = self.lines_to_bytearray()
        log().info('Data size: %d', len(data))
        compressor = self.compressor_cls(data)
        self.compressed = compressor.compress()
        sc = len(self.compressed)
        su = len(data)
        rc = sc / su
        if self.args.verbose:
            print("Size: {} Packed: {} Ratio: {:.2f}".format(su, sc, rc))
        log().info('Size: %d Packed: %d Ratio: %d', su, sc, rc)

    def __write(self, value):
        self.args.destination.write(("{}{}".format(value, os.linesep)).encode())

    def __write_text(self, text):
        for i in text.splitlines():
            self.__write(i)
    
    def __save_asm(self):
        "Save image data as asm"
        log().debug('Saving image data to file')

        def generate_lines(lines):
            "Generator for uncompressed asm data lines"
            for line in lines:
                yield "\t\t.byte {}".format(",".join("${:02x}".format(i) for i in line))

        def generate_compressed_lines(data):
            "Generator for compressed asm data lines"
            n = self.args.number
            lines = [data[i*n: i*n+n] for i in range(len(data)//n+(1 if len(data)%n else 0))]
            for line in lines:
                yield "\t\t.byte {}".format(",".join("${:02x}".format(i) for i in line))

        if self.args.align:
            self.__write("\t.align $1000")

        self.__write("\t.local image_{} ; width={} height={}".format(
                     self.args.label, self.width, self.height))

        generated_lines = generate_lines(self.lines) if not self.args.compress else \
                          generate_compressed_lines(self.compressed)
        
        for line in generated_lines:
            self.__write(line)
        
        self.__write("\t.endl")
        self.write_dlist()
        self.write_colors()
        self.write_uncompress()

    def write_uncompress(self):
        "Write uncompress routine"
        if self.args.uncompress:
            log().debug('Saving uncompress routine')
            uncompress = self.compressor_cls.uncompress()
            contents = uncompress.assembly.splitlines()
            for content in contents:
                print(content, file=self.args.uncompress)
            
    def write_colors(self):
        "Append color information"
        log().debug('Saving color palette')
        self.__write("\t.local colors_{}".format(self.args.label))
        for index, color in enumerate(self.colors):
            clr = (index, *(RGB2AtariColorConverter(color).value[:4]))
            self.__write("c{}\t\t.byte ${:02x}".format(index, clr[-1]))
            if self.args.verbose:
                print("Color {} [{:02x}{:02x}{:02x}] = {}".format(*clr))
        self.__write("\t.endl")

    def write_dlist(self):
        "Append display list"
        log().debug('Saving display list')
        if self.args.display_list and not self.args.compress:
            if self.args.align:
                self.__write("\t.align $400")
            self.__write_text("""\t.local dlist_{label}
:3		.byte $70
		.byte $4{antic}, a(image_{label})
:101	.byte $0{antic}
		.byte $4{antic}, a(image_{label}+$1000)
:89		.byte $0{antic}
		.byte $41, a(dlist_{label})
\t.endl""".format(label=self.args.label, antic=hex(self.args.antic_mode)[-1]))

    def __save_bin(self):
        "Save binary data"
        if not self.args.compress:
            data = self.lines_to_bytearray()
            self.args.destination.write(data)
            log().debug('Saved raw file')
        else:
            self.args.destination.write(self.compressed)
            log().debug('Saved compressed file')

    def save(self):
        "Save image data"
        if self.args.type == 'asm':
            log().debug('Saving asm file')
            self.__save_asm()
        elif self.args.type == 'bin':
            log().debug('Saving binary file')
            self.__save_bin()

def add_parser_args(parser):
    "Add cli arguments to parser"
    parser.add_argument('-s', '--source', type=argparse.FileType('rb'), help='path to source gif file', required=True)
    parser.add_argument('-d', '--destination', type=argparse.FileType('wb'), help='path to destination asm file', required=True)
    parser.add_argument('-n', '--number', type=int, default=20, help='number of bytes per line for compressed data')
    parser.add_argument('-l', '--label', help='label name', default='1')
    parser.add_argument('-i', '--display-list', help='generate display list in asm file (uncompressed only)', action='store_true')
    parser.add_argument('-r', '--ratio', help='color ratio (8/ratio=colors per byte)', type=int, choices=(8,4,2), default=4)
    parser.add_argument('-t', '--type', choices=('asm', 'bin'), help='select output type', default='asm')
    parser.add_argument('-e', '--verbose', action='store_true', help='generate more verbose output')
    parser.add_argument('-m', '--compressor', choices=('legacy', 'lz4'), help='select compress type', default='legacy')
    parser.add_argument('-c', '--compress', help='compress data', action='store_true')
    parser.add_argument('-u', '--uncompress', help='save routine for data uncompress', type=argparse.FileType('w'))
    parser.add_argument('-o', '--antic-mode', help='set antic mode', type=int, choices=(13,14,15), default=14)
    parser.add_argument('-a', '--align', help='include .align command (uncompressed only)', action='store_true')

def get_parser():
    "Create parser and add cli arguments"
    parser = argparse.ArgumentParser()
    add_parser_args(parser)
    return parser  

def process(args):
    "Main processing"
    log().debug("Start processing")
    img_converter = AtariImageConverter(args)
    img_converter.process()
    img_converter.compress()
    img_converter.save()
    log().debug("Done")

def main():
    "Parse arguments and process data"
    parser = get_parser()
    args = parser.parse_args()  
    process(args)

if __name__ == '__main__':
    main()
