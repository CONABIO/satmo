#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-09-23
Purpose: Compute a new variable from the bands of an existing L2 file and appends it to
that same L2 file.
The cli works for a range of date and supports parallel processing.
"""

import argparse
import satmo

def main(aqua, terra, viirs, seawifs, begin, end, data_root, n_threads, var,
         suite):
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

    satmo.l2_append_batcher(begin=begin, end=end, sensor_codes=sensor_codes,
                            n_threads=n_threads, var=var, suite=suite,
                            data_root=data_root)

if __name__ == '__main__':
    epilog = """
Command line utility to batch compute a new variable from the bands of an existing
L2 file and appends it to that same L2 file.
The cli works for a range of dates and support parallel processing.

--------------
Example usage:
--------------

# Compute afai for the OC2 suite (generated from L1A files using timerange_L2_process.py cli utility
timerange_L2_append.py --aqua --terra --viirs -b 2014-01-01 -e 2014-12-31
-multi 3 -v afai -s OC2 -d /export/isilon/data2/satmo2_data
              """

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

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)

    parser.add_argument('-v', '--var',
                        type=str,
                        required = True,
                        help = 'Short name of the variable to process. Must exist in the global variable BAND_MATH_FUNCTIONS')

    parser.add_argument("-s", "--suite",
                        required=True,
                        help="Name of the L2 suite containing the input bands, and to with the new variable will be appended")

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))

