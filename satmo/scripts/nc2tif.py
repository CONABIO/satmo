#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2016-01-09
Purpose: Command line utility to generate georeferenced tif file from
         L3m netCDF4 file

"""

import satmo
import argparse
import os

def main(file):
    satmo.nc2tif(file)


if __name__ == '__main__':

    epilog = ('Command line utility to generate georeferenced tif file from\n'
              'a L3m netCDF4 file \n'
              'Typical input file names are:\n\n'
              'T2014027.L3m_DAY_CHL_chlor_a_1km.nc\n\n'
              'Output file name (same as input with tif extension) is automatically generated\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n'
              'nc2tif.py A2015001.L3m_DAY_CHL_chlor_a_1km.nc\n\n'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("file", help="L3m nc file")

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))