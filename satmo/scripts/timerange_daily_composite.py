#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-05-18
Purpose: Command line utility for batch production of sensors composites for a given time
    range. Runs satmo.timerange_daily_composite from the command line.

"""

import argparse
import satmo

def main(aqua, terra, viirs, seawifs, begin, end, var, suite, data_root, resolution,
         fun, preview, overwrite, n_threads):
    # Handle the sensor_codes argument of timerange_daily_composites
    if any([aqua, terra, viirs, seawifs]):
        sensor_codes = []
        if aqua:
            sensor_codes.append('A')
        if terra:
            sensor_codes.append('T')
        if seawifs:
            sensor_codes.append('S')
        if viirs:
            sensor_codes.append('V')
    else:
        sensor_codes = 'all'

    satmo.timerange_daily_composite(begin=begin, end=end, variable=var,
                                    suite=suite, data_root=data_root,
                                    resolution=resolution,
                                    sensor_codes=sensor_codes, fun=fun,
                                    preview=preview, overwrite=overwrite,
                                    n_threads=n_threads)

if __name__ == '__main__':
    epilog = ('Command line utility to batch processing daily composites\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n\n'
              'timerange_daily_composite.py -b 2000-01-01 -e 2016-12-31 -v chlor_a -s CHL -d /home/ldutrieux/sandbox/satmo2_data -r 2km --overwrite -multi 3')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--aqua', action='store_true',
                        help = 'Include aqua sensor in the compositing, when available')

    parser.add_argument('--terra', action='store_true',
                        help = 'Include terra sensor in the compositing, when available')

    parser.add_argument('--seawifs', action='store_true',
                        help = 'Include seawif sensor in the compositing, when available')

    parser.add_argument('--viirs', action='store_true',
                        help = 'Include viirs sensor in the compositing, when available')

    parser.add_argument('-b', '--begin',
                        required = True,
                        help = 'Anterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-e', '--end',
                        required = True,
                        help = 'Posterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-v', '--var',
                        required = True,
                        help = 'L3m variable (e.g. chlor_a)')

    parser.add_argument('-s', '--suite',
                        required = True,
                        help = 'L3m suite (e.g. CHL)')

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument("-r", "--resolution",
                        required=True,
                        help="Resolution (e.g. 1km)")

    parser.add_argument("-f", "--fun",
                        required=False,
                        help="Compositing function (can be mean (default), median, max, min")
    parser.set_defaults(fun='mean')

    parser.add_argument('--overwrite', action='store_true',
                        help = 'overwrite existing files?')

    parser.add_argument('--preview', action='store_true',
                        help = 'Generate png previews?')

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
