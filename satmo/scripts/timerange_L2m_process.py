#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-09-12
Purpose: Produces L2m files from L2 files using the seadas l2mapgen command.
The cli works for a range of date and supports parallel processing.
"""

import argparse
import satmo

def main(aqua, terra, viirs, seawifs, begin, end, var, north, south,
         west, east, data_root, night, flags, n_threads, overwrite,
         width, outmode, threshold):
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

    satmo.l2mapgen_batcher(begin=begin, end=end, sensor_codes=sensor_codes,
                           var=var, n_threads=n_threads, south=south, north=north,
                           west=west, east=east, data_root=data_root,
                           night=night, flags=flags, width=width,
                           outmode=outmode, threshold=threshold, overwrite=overwrite)

if __name__ == '__main__':
    epilog = ("""
              Command line utility to batch produce L2m files. Uses l2mapgen seadas
              command. The cli works for a range of dates and support parallel processing.

              --------------
              Example usage:
              --------------

              # Chlorophyll A processing
              timerange_L2m_process.py --aqua --terra --viirs -b 2014-01-01 -e 2014-12-31
              -v chlor_a --overwrite -multi 3 -north 33 -south 3 -west -122 -east -72
              -d /export/isilon/data2/satmo2_data

              # Night temperature processing
              timerange_L2m_process.py --aqua --terra --viirs -b 2014-01-01 -e 2014-12-31
              -v sst --overwrite -multi 3 -north 33 -south 3 -west -122 -east -72
              -d /export/isilon/data2/satmo2_data --night
              """)

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
                        help = 'L2m variable to process (e.g. \'chlor_a\')')

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument('-flags', '--flags',
                        type=str,
                        nargs='*',
                        required=False,
                        help='Flags used for filtering. Optional, seadas defaults are used if not set.')
    parser.set_defaults(flags=None)

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

    parser.add_argument('--night', action='store_true',
                        help='Process night variables')

    parser.add_argument('--overwrite', action='store_true',
                       help = 'Should existing files be overwritten')

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)

    parser.add_argument('-width', '--width',
                        type=int,
                        help='Maximum width of output raster')
    parser.set_defaults(width=5000)

    parser.add_argument('-outmode', '--outmode',
                        help='Type of output (see l2mapgen doc)')
    parser.set_defaults(outmode='tiff')

    parser.add_argument('-threshold', '--threshold',
                        type=float,
                        help='Minimum percentage of filled pixels for the file to be generated, defaults to 0')
    parser.set_defaults(threshold=0)
    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
