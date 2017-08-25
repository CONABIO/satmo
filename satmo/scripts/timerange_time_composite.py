#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-05-23
Purpose: Produces time composites from daily composites (L3m files), for a
    given compositing period and time range. Supports parallel processing.
"""

import satmo
import argparse

def main(sensor, begin, end, delta, var, suite, resolution, data_root, fun, overwrite,
         preview, n_threads):
    if sensor == 'aqua':
        sensor_code = 'A'
    elif sensor == 'terra':
        sensor_code = 'T'
    elif sensor == 'viirs':
        sensor_code = 'V'
    elif sensor == 'combined':
        sensor_code = 'X'
    elif sensor == 'seawifs':
        sensor_code == 'S'
    else:
        raise ValueError('Non suported value for --sensor. If you think it should be supported change the code in satmo/scripts/timerange_time_composite.py')

    # Deal with the delta
    if delta.isdigit():
        delta = int(delta)
        # Generate composite name
        composite = '%dDAY' % delta
    elif delta == 'month':
        composite = 'MO'
    else:
        raise ValueError('--delta must be an integer or month')

    satmo.timerange_time_compositer(begin=begin, end=end, delta=delta, var=var, suite=suite,
                          resolution=resolution, composite=composite, data_root=data_root,
                          sensor_code=sensor_code, fun=fun, overwrite=overwrite,
                          preview=preview, n_threads=n_threads)

if __name__ == '__main__':
    epilog = ('Command line utility to batch produce time composites from daily composites. \n'
              'works for a range of date and supports parallel processing.\n'
              'Composites are truncated at the end of each year and resetted at the first of January of each year.\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n\n'
              'timerange_time_composite.py -sensor combined -b 2005-01-01 -e 2017-06-01 -delta 16'
              '-s CHL -v chlor_a -f mean -d /home/ldutrieux/sandbox/satmo2_data -r 2km'
              '--overwrite --preview -multi 4 ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--sensor', '-sensor',
                        required = False,
                        type = str,
                        help = 'Which sensor should be processed. Optional, defaults to combined, which corresponds to daily composites. (Run timerange_daily_composite.py before this command in that case)')
    parser.set_defaults(sensor='combined')

    parser.add_argument('-b', '--begin',
                        required = True,
                        help = 'Anterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-e', '--end',
                        required = True,
                        help = 'Posterior time-range boundary in yyyy-mm-dd')

    parser.add_argument('-delta', '--delta',
                       required = True,
                       type = str,
                       help = 'Compositing period, in number of days, or \'month\' to create monthly composites.')

    parser.add_argument('-v', '--var',
                        required = True,
                        help = 'L3m variable to compose (e.g. \'chlor_a\')')

    parser.add_argument('-s', '--suite',
                        required = True,
                        help = 'L3m suite to compose (e.g. \'CHL\')')

    parser.add_argument("-r", "--resolution",
                        required=True,
                        help="Resolution (e.g. 1km)")

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

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
