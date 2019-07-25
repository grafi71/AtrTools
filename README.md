# AtrTools
Set of tools supporting Atari 8-bit development

Currently the package consist of two modules:
- **IMGconv**
- **SAPconv**

## Requirements

Python 3 

## Installation

To install the package execute following command in src folder:

`python setup.py install`

Verify installation by typing

`python -m atrtools`

or simply

`atrtools`

## IMGConv

Converts indexed gif image to Atari MADS assembly format. The rgb colors from the image palette are converted as well.

---
**IMGConv will not change the image resolution. You must provide it a gif image with proper resolution and color depth.**
---

It is possible to compress image data and to save 6502 uncompress routine to specified file.
However, the uncompress routine assumes that the graphics data is 40-bytes per line.

### Usage

To get help type:

`python -m atrtools.imgconv -h`

or 

`atrtools imgconv -h`

or simply

`imgconv -h`

### Examples

Convert indexed 4-colors gif (2-bits per color) to .asm file (Atari ANTIC mode 14 data):

`imgconv -s path_to_input_file.gif -d -d path_to_output.asm -r 4`

Convert monochrome (1-bit per color) to .asm file (Atari ANTIC mode 15 data):

`imgconv -s path_to_input_file.gif -d path_to_output.asm -r 8`

Convert indexed 9-colors gif (4-bits per color) to .asm file (Atari GTIA mode 8 data):

`imgconv -s path_to_input_file.gif -d path_to_output.asm -r 2`

Convert monochrome 16-colors gif (4-bits per color) to .asm file (Atari GTIA mode 4 data):

`imgconv -s path_to_input_file.gif -d path_to_output.asm -r 2`

Convert indexed 4-colors gif (2-bits per color) to compressed .asm file (Atari ANTIC mode 14 data), verbose output and save  uncompress  routine (6502 assembler) to given file:

`imgconv -s path_to_input_file.gif -d path_to_output.asm -r 4 -e -c -u uncompress.asm`

## SAPConv

Converts Atari SAP music file to Atari MADS assembly format (bytes).

### Usage

To get help type:

`python -m atrtools.sapconv -h`

or 

`atrtools sapconv -h`

or simply

`sapconv -h`

### Example

Convert SAP file to .asm format (bytes):

`sapconv -s path_to_input_file.sap -d path_to_output_file.asm`
