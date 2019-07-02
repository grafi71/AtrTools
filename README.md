# AtrTools
Set of tools supporting Atari 8-bit development

Currently the package consist of two modules:
- imgconv
- sapconv

## Requirements

Python 3 

## Installation

To install the package execute following command in src folder:

`python setup.py install`

Check installation by typing

`python -m atrtools`

or simply

`atrtools`

## ImgConv

Convert indexed gif image to Atari Masm assembly format. The rgb colors from the image palette are converted as well.

### Usage

To get help type:

`python -m atrtools.imgconv -h`

or simply

`imgconv -h`

## ImgConv

Convert Atari SAP music file to Atari Masm assembly format (bytes).

### Usage

To get help type:

`python -m atrtools.sapconv -h`

or simply

`sapconv -h`
