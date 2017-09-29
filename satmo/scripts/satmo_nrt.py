#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-06-23
Purpose: Command line utility to launch near real time mode of the satmo with various
    options.
Details: The script does a bit of parsing and calls several time the nrt_wrapper functions
    in a scheduler. Changes made to this script must therefore be mirrored in nrt_wrapper,
    nrt_wrapper_l1, and refined_processing_wrapper_l1.
"""

import argparse
from satmo import (nrt_wrapper, time_limit, TimeoutException,
                   refined_processing_wrapper_l1, nrt_wrapper_l1)
import schedule
import time
from pprint import pprint
import os

# Handle function running time (no step should take more than 2 hr, otherwise it probably means that
# it's hanging, and it should be stopped to not affect the other tasks). This is likely to happen in case of
# the internet connection momentarily breaks during download. All processes are launched with at least 3 hr interval

def main(day_vars, night_vars, l1a_vars, refined, eight_day, month, data_root,
         binning_resolution, mapping_resolution, north, south, west, east,
         flags, proj, delay, n_threads):

    pprint(os.environ['OCSSWROOT'] + '\n')

    def day_nrt():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='day', pp_type='nrt', var_list=day_vars, north=north,
                            south=south, west=west, east=east, binning_resolution=binning_resolution,
                            mapping_resolution=mapping_resolution, data_root=data_root,
                            eight_day=eight_day, month=month, flags=flags, proj=proj)
        except TimeoutException:
            pprint('A process timed out for not completing after 2hr!')

    def day_refined():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='day', pp_type='refined', var_list=day_vars, north=north,
                            south=south, west=west, east=east, binning_resolution=binning_resolution,
                            mapping_resolution=mapping_resolution, data_root=data_root,
                            eight_day=eight_day, month=month, flags=flags, proj=proj)
        except TimeoutException:
            pprint('A processed timed out for not completing after 2hr!')

    def night_nrt():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='night', pp_type='nrt', var_list=night_vars, north=north,
                            south=south, west=west, east=east, binning_resolution=binning_resolution,
                            mapping_resolution=mapping_resolution, data_root=data_root,
                            eight_day=eight_day, month=month, flags=flags, proj=proj)
        except TimeoutException:
            pprint('A processed timed out for not completing after 2hr!')

    def night_refined():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='night', pp_type='refined', var_list=night_vars, north=north,
                            south=south, west=west, east=east, binning_resolution=binning_resolution,
                            mapping_resolution=mapping_resolution, data_root=data_root,
                            eight_day=eight_day, month=month, flags=flags, proj=proj)
        except TimeoutException:
            pprint('A processed timed out for not completing after 2hr!')

    def l1a_nrt():
        try:
            with time_limit(18000 - 60): # 5 hrs - 60 seconds
                nrt_wrapper_l1(north=north, south=south, west=west, east=east,
                               var_list=l1a_vars, data_root=data_root, n_threads=n_threads)
        except TimeoutException:
            pprint('A processed timed out for not completing after 5hr!')

    def l1a_refined_processing():
        try:
            with time_limit(21600 - 60): # Almost 6 hrs
                refined_processing_wrapper_l1(north=north, south=south, west=west,
                                              east=east, var_list=l1a_vars,
                                              data_root=data_root, delay=delay)
        except TimeoutException:
            pprint('A processed timed out for not completing after 6hr!')


    schedule.every().day.at("18:30").do(l1a_nrt)
    schedule.every().day.at("23:30").do(day_nrt)
    schedule.every().day.at("05:30").do(night_nrt)
    if refined:
        schedule.every().day.at("01:30").do(day_refined)
        schedule.every().day.at("03:30").do(night_refined)
        # Refined L1A to L2 processing does not require any download, it can therefore
        # be executed during the day
        schedule.every().day.at("11:00").do(l1a_refined_processing)

# 18.30 -- l1a_nrt (5hr)---23.30---day_nrt(2hr)---1.30---day_refined(2hr)---3.30---night_refined(2hr)---5.30---night_nrt(2hr)
# Normally night download and processing should be faster (lighter files, and lesser amount of variables
# so reducing available time for night products and increasing it for day products
# could be a way to adjust timing if needed)

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    epilog = """

Command Line utility to control the operational mode of the satmo system. Enables download of L2 and (day only) L1A data from OBPG server (NRT and refined processing),
processing of L3m and L2m files for several night and day variables, processing of daily composites, and processing of temporal composites. All these download and processing steps
are scheduled and ran operationally. Temporal composites are enabled by default. Use the --no-daily_compose, and --no-8DAYto disable their generation.

The L2 suite generated from L1A data by this command line is named OC2, and contains a list of variables defined in the global variable VARS_FROM_L2_SUITE. Additional variables can be
appended to the OC2 suite by passing them to --l1a_vars (these variable must have an entry in the BAND_MATH_FUNCTIONS satmo global variable). At the moment the OC2 suite is only
used for fai and afai generation, and therefore only processed up to level 2m (L2m).

------------------
Example usage:
------------------
satmo_nrt.py --day_vars chlor_a nflh sst Kd_490 --night_vars sst --l1a_vars afai fai --north 33 --south 3 --west -122 --east -72 -d /export/isilon/datos2/satmo2_data/ -multi 3
"""


    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-day_vars', '--day_vars',
                        type = str,
                        nargs = '*',
                        required = True,
                        help = 'day time variables to process')

    parser.add_argument('-night_vars', '--night_vars',
                        type = str,
                        nargs = '*',
                        required = True,
                        help = 'night time variables to process')

    parser.add_argument('-l1a_vars', '--l1a_vars',
                        type = str,
                        nargs = '*',
                        required = False,
                        help = 'Additional L2 variables to process from OC2 collection (generated from L1A files)')
    parser.set_defaults(l1a_vars=['fai', 'afai'])

    parser.add_argument('--no-refined', dest='refined', action='store_false',
                        help='Disable download of refined processed L2 data, reprocessing of L2 data from L1A, and L3m processing from them')

    parser.add_argument('--no-8DAY', dest='eight_day', action='store_false',
                        help='Disable processing of 8 days temporal composites')

    parser.add_argument('--no-month', dest='month', action='store_false',
                        help='Disable processing of monthly temporal composites')

    parser.add_argument("-d", "--data_root",
                        required=True,
                        type = str,
                        help="Root of the local archive")

    parser.add_argument("-map_res", "--mapping_resolution",
                        required=False,
                        type = int,
                        help="Output resolution in meters (defaults to 1000)")
    parser.set_defaults(mapping_resolution=1000)

    parser.add_argument("-bin_res", "--binning_resolution",
                        required=False,
                        type = str,
                        help="Output resolution in meters (defaults to 1000)")
    parser.set_defaults(binning_resolution='1')

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

    parser.add_argument('-p', '--proj',
                        type = str,
                        required = False,
                        help = ('Optional Coordinate reference system of the output in proj4 format,'
                                ' or any predifined crs name in seadas l3mapgen. If None is provided,'
                                ' +proj=eqc +lon_0=0 is used'))
    parser.set_defaults(proj=None)

    parser.add_argument('-flags', '--flags',
                        required = False,
                        nargs = '*',
                        help = ('List of flags to use in the binning step. If not provided defaults are retrieved'
                                ' for each L3 suite independently from the satmo global variable FLAGS'))
    parser.set_defaults(flags=None)

    parser.add_argument('-delay', '--delay',
                        required=False,
                        type = int,
                        help = 'NUmber of days to wait before triggering refined reprocessing of the L2 OC2 suite from L1A')
    parser.set_defaults(delay=30)

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
