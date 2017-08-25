#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2016-01-07
Purpose: Command line utility to generate previews from nc or tiff
        files

"""

import satmo
import argparse
import os

def main(file):
    satmo.make_preview(file)


if __name__ == '__main__':

    epilog = ('Command line utility for generating jpg previews of ocean color variables\n' 
              'Takes a nc or geotiff file. \n'
              'File names must follow a standardized naming convention for the utility to\n'
              'produce the best preview possible. Typical file names are:\n\n'
              'T2014027.L3m_DAY_CHL_chlor_a_1km.tif\n\n'
              'A2015001.L3m_DAY_CHL_chlor_a_1km.nc\n\n'
              'The preview file produced has the same file name as the input, with the png extension\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n'
              'make_preview.py A2015001.L3m_DAY_CHL_chlor_a_1km.nc\n\n'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("file", help="L3m nc or tiff file with appropriate name convention")

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))