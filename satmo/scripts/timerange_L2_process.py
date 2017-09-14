#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-09-14
Purpose: Produces L2 files from L2 files using the seadas l2gen command.
The cli works for a range of date and supports parallel processing.
"""

import argparse
import satmo

def main(aqua, terra, viirs, seawifs, begin, end, data_root, night,
         n_threads, var_list, suite, get_anc):
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

    satmo.l2gen_batcher(begin=begin, end=end, sensor_codes=sensor_codes,
                        n_threads=n_threads, var_list=var_list, suite=suite,
                        data_root=data_root, get_anc=get_anc, night=night):

if __name__ == '__main__':
    epilog = ("""
              Command line utility to batch produce L2 files. Uses l2gen seadas
              command. The cli works for a range of dates and support parallel processing.

              --------------
              Example usage:
              --------------

              # Chlorophyll A and rrs processing
              timerange_L2_process.py --aqua --terra --viirs -b 2014-01-01 -e 2014-12-31
              -multi 3 -v chlor_a rrs_nnn -s OC2 -d /export/isilon/data2/satmo2_data
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

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument('--night', action='store_true',
                        help='Process night variables')

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)

    parser.add_argument('-v', '--var_list',
                        type=str,
                        required = True,
                        nargs='*',
                        help = 'variables to include in the output L2 files')

    parser.add_argument("-s", "--suite",
                        required=True,
                        help="Name of the L2 suite generated")

    parser.add_argument("--no-anc", dest='get_anc', action='store_false',
                        help='Use climatologies instead of ancillary data for atmospheric correction.')
    parser.set_defaults(get_anc=True)

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
