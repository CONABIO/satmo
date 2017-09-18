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

# Handle function running time (no step should take more than 2 hr, otherwise it probably means that
# it's hanging, and it should be stopped to not affect the other tasks). This is likely to happen in case of
# the internet connection momentarily breaks during download. All processes are launched with at least 3 hr interval

def main(day_vars, night_vars, refined, eight_day, month, sixteen_day, daily_compose,
         data_root, resolution, north, south, west, east, preview, compositing_function):

    def day_nrt():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='day', pp_type='nrt', var_list=day_vars, north=north,
                            south=south, west=west, east=east, resolution=resolution, preview=preview,
                            data_root=data_root, daily_compose=daily_compose, eight_day=eight_day,
                            sixteen_day=sixteen_day, month=month, compositing_function=compositing_function)
        except TimeoutException:
            pprint('A process timed out for not completing after 2hr!')

    def day_refined():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='day', pp_type='refined', var_list=day_vars, north=north,
                            south=south, west=west, east=east, resolution=resolution, preview=preview,
                            data_root=data_root, daily_compose=daily_compose, eight_day=eight_day,
                            sixteen_day=sixteen_day, month=month, compositing_function=compositing_function)
        except TimeoutException:
            pprint('A processed timed out for not completing after 2hr!')

    def night_nrt():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='night', pp_type='nrt', var_list=night_vars, north=north,
                            south=south, west=west, east=east, resolution=resolution, preview=preview,
                            data_root=data_root, daily_compose=daily_compose, eight_day=eight_day,
                            sixteen_day=sixteen_day, month=month, compositing_function=compositing_function)
        except TimeoutException:
            pprint('A processed timed out for not completing after 2hr!')

    def night_refined():
        try:
            with time_limit(7200 - 60):
                nrt_wrapper(day_or_night='night', pp_type='refined', var_list=night_vars, north=north,
                            south=south, west=west, east=east, resolution=resolution, preview=preview,
                            data_root=data_root, daily_compose=daily_compose, eight_day=eight_day,
                            sixteen_day=sixteen_day, month=month, compositing_function=compositing_function)
        except TimeoutException:
            pprint('A processed timed out for not completing after 2hr!')

    def l1a_nrt():
        try:
            with time_limit(18000 - 60): # 5 hrs - 60 seconds
                nrt_wrapper_l1(north=north, south=south, west=west, east=east,
                               data_root=data_root)
        except TimeoutException:
            pprint('A processed timed out for not completing after 5hr!')

    def l1a_refined_processing():
        try:
            with time_limit(21600 - 60): # Almost 6 hrs
                refined_processing_wrapper_l1(north=north, south=south, west=west,
                                              east=east, data_root=data_root)
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

"""
18.30 -- l1a_nrt (5hr)---23.30---day_nrt(2hr)---1.30---day_refined(2hr)---3.30---night_refined(2hr)---5.30---night_nrt(2hr)
Normally night download and processing should be faster (lighter files, and lesser amount of variables
so reducing available time for night products and increasing it for day products
could be a way to adjust timing if needed)
"""

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    epilog = ('Command Line utility to control the operational mode of the satmo system \n'
              'Enables download of L2 and L1A data from OBPG server (NRT and refined processing), processing of L3m files for several night and \n'
              'day variables, processing of daily composites, and processing of temporal composites. \n'
              'All these download and processing steps are scheduled and ran operationally. \n'
              'Daily composites and temporales composites are enabled by default \n'
              'Use the --no-daily_compose, --no-8DAY, and --no-16DAY to disable their generation \n\n'
              '------------------\n'
              'Example usage:\n'
              '------------------\n\n'
              'satmo_nrt.py --day_vars chlor_a nflh sst Kd_490 --night_vars sst --north 33 --south 3 --west -122 \n'
              '--east -72 -d /export/isilon/datos2/satmo2_data/ -r 2000')

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

    parser.add_argument('--no-refined', dest='refined', action='store_false',
                        help='Disable download of refined processed L2 data, reprocessing of L2 data from L1A, and L3m processing from them')

    parser.add_argument('--no-8DAY', dest='eight_day', action='store_false',
                        help='Disable processing of 8 days temporal composites')

    parser.add_argument('--no-16DAY', dest='sixteen_day', action='store_false',
                        help='Disable processing of 16 days temporal composites')

    parser.add_argument('--no-month', dest='month', action='store_false',
                        help='Disable processing of monthly temporal composites')

    parser.add_argument('--no-daily_compose', dest='daily_compose', action='store_false',
                        help='Disable processing of daily composites. Because temporal composites are produced from daily composites, you must disable temporal composites when disabling daily composites.')

    parser.add_argument("-d", "--data_root",
                        required=True,
                        type = str,
                        help="Root of the local archive")

    parser.add_argument("-r", "--resolution",
                        required=True,
                        type = int,
                        help="Output resolution (in meters)")

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

    parser.add_argument('--preview', action='store_true',
                        help = 'Generate png previews in addition to geotiffs')

    parser.add_argument('--fun', dest='compositing_function', type=str,
                       help='Compositing function for generating daily and temporal coposites. Default to mean. Other options are min, max, and median')
    parser.set_defaults(compositing_function='mean')
    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
