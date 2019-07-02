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

Convert indexed gif image to Atari Masm assembly format. The rgb colors from the image palette are converted as well.

### Usage

To get help type:

`python -m atrtools.imgconv -h`

or 

`atrtools imgconv -h`

or simply

`imgconv -h`

### Example

Convert indexed 4-colors gif (2-bits per color) to .asm file (Atari ANTIC mode 14 data):

`imgconv path_to_input_file.gif path_to_output.asm -r 4`

Convert monochrome (1-bit per color) to .asm file (Atari ANTIC mode 15 data):

`imgconv path_to_input_file.gif path_to_output.asm -r 8`

Convert indexed 9-colors gif (4-bits per color) to .asm file (Atari GTIA mode 8 data):

`imgconv path_to_input_file.gif path_to_output.asm -r 2`

Convert monochrome 16-colors gif (4-bits per color) to .asm file (Atari GTIA mode 4 data):

`imgconv path_to_input_file.gif path_to_output.asm -r 2`

## SAPConv

Convert Atari SAP music file to Atari Masm assembly format (bytes).

### Usage

To get help type:

`python -m atrtools.sapconv -h`

or 

`atrtools sapconv -h`

or simply

`sapconv -h`

### Example

Convert SAP file to .asm format (bytes):

`sapconv path_to_input_file.sap path_to_output_file.asm`
