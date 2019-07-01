"""
This is converter of indexed gif files (1-8 colors) to Atari .asm data file.
Requires pillow package to be installed.
"""

import argparse
import logging
import math
import itertools

from PIL import Image


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

    @staticmethod
    def clip_var(x):
        if x > 0xff:
            return 0xff 
        if x < 0:
            return 0
        return x

    def convert(self):
        ir, ig, ib = self.colors
        m = 0xFFFFF

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
                r1 = self.__class__.clip_var(r1)
                g1 = self.__class__.clip_var(g1)
                b1 = self.__class__.clip_var(b1)

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
        logging.debug("R=%3d G=%3d B=%3d : $%02X Hue = %d Lum = %d", *val)
        return val


class AtariImageConverter:
    "Atari image converter class"

    def __init__(self, args):
        self.args = args
        self.lines = []
        self.width = None
        self.height = None
        self.compressed = []
        self.colors = []

    def process(self):
        def color_generator():
            buffer = []
            for c in img.palette.palette:
                buffer.append(c)
                if len(buffer)==3:
                    yield "{:02x}{:02x}{:02x}".format(*buffer)
                    buffer = []

        lines = []
        img = Image.open(self.args.source)
        logging.debug("image width=%d, height=%d", img.width, img.height)
        self.width, self.height = (img.width, img.height)
        for vpos in range(0, img.height):
            line = []
            for hbyte in range(0, int(img.width/self.args.ratio)):
                bval = 0
                for i in range(0, self.args.ratio):
                    col = img.getpixel((hbyte*self.args.ratio+i, vpos))
                    bval <<= int(8/self.args.ratio)
                    bval |= col
                line.append(bval)
            lines.append(line)
        self.lines = lines
        for color in color_generator():
            self.colors.append(color)
    
    # image.width / ratio = bytes per row

    def compress(self):
        def data_generator(data):
            yield 1
        logging.debug('Size before: %d', (sum(len(i) for i in self.lines)))
        flat_data = list(itertools.chain.from_iterable(self.lines))
        data = data_generator(flat_data)
        logging.debug('Size after: %d', (sum(self.compressed)))


    def save(self):
        print("\t\t.local image ; WIDTH={} HEIGHT={}".format(self.width, self.height), file=self.args.destination)
        for line in self.lines:
            sval = ",".join("${:02x}".format(i) for i in line)
            print("\t\t.byte {}".format(sval), file=self.args.destination)
        print("\t\t.endl", file=self.args.destination)
        
        print("\t\t.local colors", file=self.args.destination)
        for color in self.colors:
            cnv = RGB2AtariColorConverter(color)
            print("\t\t.byte ${:02x}".format(cnv.value[3]), file=self.args.destination)
        print("\t\t.endl", file=self.args.destination)

def add_parser_args(parser):
    parser.add_argument('source', type=argparse.FileType('rb'), help='path to source gif file')
    parser.add_argument('destination', type=argparse.FileType('w'), help='path to destination asm file')
    parser.add_argument('-z', '--compress', help='compress data', action='store_true')
    parser.add_argument('-r', '--ratio', help='color bits per byte ratio', type=int, choices=(8,4,2), default=8)

def get_parser():
    parser = argparse.ArgumentParser()
    add_parser_args(parser)
    return parser  

def process(args):
    img_converter = AtariImageConverter(args)
    img_converter.process()
    img_converter.compress()
    img_converter.save()

def main():
    parser = get_parser()
    args = parser.parse_args()  
    process(args)

if __name__ == '__main__':
    main()
