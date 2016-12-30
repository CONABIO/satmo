#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2016-12-30
Purpose: Command line utility for spatial extraction of L1A data
         in batch mode and in parallel

"""

import argparse
import satmo


def main(aqua, terra, seawifs, begin, end,\
        north, south, west, east,\
        data_root, compress, clean, n_threads,\
        pattern, overwrite_extract, overwrite_compress, keep_uncompressed):
    sensors = []
    init_kwargs = {}
    extract_kwargs = {'overwrite': overwrite_extract}
    compress_kwargs = {'overwrite': overwrite_compress}
    clean_kwargs = {'keep_uncompressed': keep_uncompressed}
    if aqua:
        sensors.append('aqua')
    if terra:
        sensors.append('terra')
    if seawifs:
        sensors.append('seawifs')
    if pattern is not None:
        init_kwargs['pattern'] = pattern


    satmo.timerange_extract(sensors = sensors, data_root = data_root, begin = begin, end = end,\
                            north = north, south = south, west = west, east = east,\
                            compress = compress, clean = clean, n_threads = n_threads,\
                            init_kwargs = init_kwargs, extract_kwargs = extract_kwargs,\
                            compress_kwargs = compress_kwargs, clean_kwargs = clean_kwargs)




if __name__ == '__main__':
    epilog = ('Command line utility for spatial extraction of L1A data via\n' 
              'seadas l1aextract_<sensor> utilities ran in batch mode with parallel support\n'
              'It is recommended to use an extent slightly larger than used for data download\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n'
              'timerange_extract.py --terra --aqua -b 2010-01-01 -e 2012-12-31 -north 34 -south 2 -west -123 -east -71 -multi 3 -d /some/directory/with/free/space\n\n'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    

    parser.add_argument('--aqua', action='store_true',
                        help = 'Extract data from aqua sensor')

    parser.add_argument('--terra', action='store_true',
                        help = 'Extract data from terra sensor')

    parser.add_argument('--seawifs', action='store_true',
                        help = 'Extract data from seawifs sensor')

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

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)

    parser.add_argument('-p', '--pattern',
                        type = str,
                        required = False,
                        help = 'regex pattern to identify input files (optional)')
    parser.set_defaults(pattern=None)

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument('--no-compress', dest='compress', action='store_false',
                        help = 'Should compression of extracted data be skipped?')
    parser.set_defaults(compress=True)

    parser.add_argument('--no-clean', dest='clean', action='store_false',
                        help = 'Should post extraction directory cleaning be skipped?')
    parser.set_defaults(clean=True)

    parser.add_argument('-oe', '--overwrite_extract', action='store_true',
                        help = 'Should existing files be overwritten during extraction?')
    parser.set_defaults(overwrite_extract=False)

    parser.add_argument('-oc', '--overwrite_compress', action='store_true',
                        help = 'Should existing extracted and compressed files be overwritten during post extraction compression?')
    parser.set_defaults(overwrite_extract=False)

    parser.add_argument('-keep', '--keep_uncompressed', action='store_true',
                        help = 'When cleaning directory at the end of the process, should uncompressed extracted files be kept?')
    parser.set_defaults(keep_uncompressed=False)

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))