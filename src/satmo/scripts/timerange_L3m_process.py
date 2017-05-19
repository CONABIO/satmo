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
         west, east, data_root, resolution, day, bit_mask, proj4string,
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
    satmo.timerange_auto_L3m_process(begin=begin, end=end,
                                     sensor_codes=sensor_codes, suite=suite,
                                     var=var, north=north, south=south,
                                     west=west, east=east,
                                     data_root=data_root,
                                     resolution=resolution, bit_mask=bit_mask,
                                     proj4string=proj4string,
                                     overwrite=overwrite, preview=preview,
                                     n_threads=n_threads)

if __name__ == '__main__':
    epilog = ('Command line utility to batch process L3m variables. Works by \n'
              'binning an existing L2 variable to a user defined grid. The cli \n'
              'works for a range of date and supports parallel processing\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n\n'
              '')
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
                        help="Resolution (e.g. 1km)")
timerange_auto_L3m_process
auto_L3m_process
        >>> satmo.timerange_auto_L3m_process(begin='2001-01-01',
                                             end='2017-12-31',
                                             sensor_codes=['V', 'T', 'A'],
                                             suite='CHL', var='chlor_a',
                                             north=33, south=3, west=-122,
                                             east=-72,
                                             data_root='/home/ldutrieux/sandbox/satmo2_data',
                                             resolution=2000)

        >>> # Second example with calculation of new variable from Rrs layers
        >>> import satmo
        >>> import numpy as np

        >>> def add_bands(x, y):
        >>>     return np.add(x, y)

        >>> satmo.timerange_auto_L3m_process(begin='2016-01-01',
                                             end='2016-01-16',
                                             sensor_codes=['A', 'T'],
                                             suite='RRS', var='rrs_add',
                                             north=33, south=3, west=-122,
                                             east=-72,
                                             data_root='/home/ldutrieux/sandbox/satmo2_data',
                                             resolution=2000,
                                             n_threads=3, overwrite=True, fun=add_bands,
                                             band_list=['Rrs_555', 'Rrs_645'])
