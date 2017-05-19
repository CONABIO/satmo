#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-05-18
Purpose: Produces L3m files via binning an existing L2 variable to a user defined
    grid. The cli works for a range of date and supports parallel processing.
"""

import argparse
import satmo

def main(aqua, terra, viirs, seawifs, begin, end, suite, var, north, south,
         west, east, data_root, resolution, night, bit_mask, proj4string,
         overwrite, preview, n_threads):
    if not any([aqua, terra, viirs, seawifs]):
        raise ValueError('You need to set at least one of the sensors flag')
    sensor_codes = []
    if aqua:
        sensor_codes.append('A')
    if terra:
        sensor_codes.append('T')
    if seawifs:
        sensor_codes.append('S')
    if viirs:
        sensor_codes.append('V')
    bit_mask = int(bit_mask, 0)
    satmo.timerange_auto_L3m_process(begin=begin, end=end,
                                     sensor_codes=sensor_codes, suite=suite,
                                     var=var, north=north, south=south,
                                     west=west, east=east,
                                     data_root=data_root,
                                     resolution=resolution, bit_mask=bit_mask,
                                     proj4string=proj4string, day=not(night),
                                     overwrite=overwrite, preview=preview,
                                     n_threads=n_threads)

if __name__ == '__main__':
    epilog = ('Command line utility to batch process L3m variables. Works by \n'
              'binning an existing L2 variable to a user defined grid. The cli \n'
              'works for a range of date and supports parallel processing\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n\n'
              'timerange_L3m_process.py --aqua --terra -b 2005-01-01 -e 2017-06-01 '
              '-s CHL -v chlor_a -d /home/ldutrieux/sandbox/satmo2_data -r 2000 '
              '--overwrite -multi 3 -north 33 -south 3 -west -122 -east -72')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--aqua', action='store_true',
                        help = 'Process aqua, when available')

    parser.add_argument('--terra', action='store_true',
                        help = 'Process terra, when available')

    parser.add_argument('--seawifs', action='store_true',
                        help = 'Process seawifs, when available')

    parser.add_argument('--viirs', action='store_true',
                        help = 'Process viirs, when available')

    parser.add_argument('-b', '--begin',
                        required = True,
                        help = 'Anterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-e', '--end',
                        required = True,
                        help = 'Posterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-v', '--var',
                        required = True,
                        help = 'L3m variable to process (e.g. \'chlor_a\')')

    parser.add_argument('-s', '--suite',
                        required = True,
                        help = 'L3m suite to obtain (e.g. \'CHL\')')

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument("-r", "--resolution",
                        required=True,
                        help="Output resolution (in the unit of the output coordinate reference system)")

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

    parser.add_argument('-p', '--proj4string',
                        type = str,
                        required = False,
                        help = ('Optional Coordinate reference system of the output in proj4 format',
                                ' If None is provided, +proj=laea centered on the output center is used'))

    parser.add_argument('--night', action='store_true',
                        help='Process night variables')

    parser.set_defaults(proj4string=None)

    parser.add_argument('-mask', '--bit_mask',
                        type = int,
                        required = False,
                        help = ('The mask to use for selecting active flags from the flag array'
    'The array is coded bitwise so that the mask has to be built as a bit mask too. '
    'It is generally more convenient to use hexadecimal to define the mask, for example'
    ' if you want to activate flags 0, 3 and 5, you can pass 0x29 (0010 1001).'
    ' The mask defaults to 0x0669D73B, which is the defaults value for seadas l2bin.'))
    parser.set_defaults(bit_mask='0x0669D73B')

    parser.add_argument('--overwrite', action='store_true',
                       help = 'Should existing files be overwritten')

    parser.add_argument('--preview', action='store_true',
                        help = 'Generate png previews in addition to geotiffs')

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)
    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
