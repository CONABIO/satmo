#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2016-12-27
Purpose: Command line utility to download L1A data from the 
        oceancolor servers for a given time range and spatial
        extent

"""

import argparse
import satmo


def main(aqua, terra, seawifs, viirs, begin, end,\
         north, south, east, west, day, night, write_dir, overwrite, check_integrity):
    sensors = []
    if aqua:
        sensors.append('am')
    if terra:
        sensors.append('tm')
    if seawifs:
        sensors.append('sw')
    if viirs:
        sensors.append('v0')

    satmo.timerange_download(sensors = sensors, begin = begin, end = end, write_dir = write_dir,\
                north = north, south = south, west = west, east = east, day = day, night = night,\
                overwrite = overwrite, check_integrity = check_integrity)


if __name__ == '__main__':
    epilog = ('Command line utility to download L1A data from the\n' 
              'oceancolor servers for a given time range and spatial\n'
              'extent\n\n'
              'If data extraction is to be performed on the data after download\n'
              'it is recommended to order a slightly smaller extent than the extraction inputs\n\n'
              'The download should be robust enough to handle breaking connections\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n'
              'timerange_download.py --terra --aqua -b 2010-01-01 -e 2012-12-31 -north 32 -south 4 -west -121 -east -73 -d /some/directory/with/free/space\n\n'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    

    parser.add_argument('--aqua', action='store_true',
                        help = 'Download data from aqua sensor')

    parser.add_argument('--terra', action='store_true',
                        help = 'Download data from terra sensor')

    parser.add_argument('--seawifs', action='store_true',
                        help = 'Download data from seawifs sensor')
    
    parser.add_argument('--viirs', action='store_true',
                        help = 'Download data from viirs sensor')

    parser.add_argument('-b', '--begin',
                        required = True,
                        help = 'Anterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-e', '--end',
                        required = True,
                        help = 'Posterior time-range boundary in yyyy-mm-dd')
    
    parser.add_argument('-north', '--north',
                        type = float,
                        required = True,
                        help = 'Northern boundary in DD')

    parser.add_argument('-south', '--south',
                        type = float,
                        required = True,
                        help = 'Southern boundary in DD')

    parser.add_argument('-east', '--east',
                        type = float,
                        required = True,
                        help = 'Eastern most boundary in DD')
    
    parser.add_argument('-west', '--west',
                        type = float,
                        required = True,
                        help = 'Western most boundary in DD')

    parser.add_argument('--no-day', dest='day', action='store_false')
    parser.set_defaults(day=True)

    parser.add_argument('--no-night', dest='night', action='store_false')
    parser.set_defaults(night=True)
                        
    parser.add_argument("-d", "--write_dir",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument('--overwrite', action='store_true',
                        help = 'Should existing data be overwritten')
    parser.set_defaults(overwrite=False)

    parser.add_argument('--check_integrity', action='store_true',
                        help = 'Only makes sense if overwrite is not set. Should existing data be checked for integrity?')
    parser.set_defaults(check_integrity=False)

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))