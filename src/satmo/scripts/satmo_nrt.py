#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-06-23
Purpose: Command line utility to launch near real time mode of the satmo with various
    options.
Details: The script does a bit of parsing and calls several time the nrt_wrapper function
    in a scheduler. Changes made to this script must therefore be mirrored in nrt_wrapper.
"""

import argparse
import satmo
import schedule
import time

nrt_wrapper(day_or_night, pp_type, var_list, north, south, west, east,
                data_root, resolution, preview=True, daily_compose=False,
                eight_day=False, sixteen_day=False, compositing_function='mean'):

def main(refined, day_vars, night_vars, data_root):
    # Do I need to add argument lists to each job function?
    def day_nrt():
        nrt_wrapper(day_or_night='day', pp_type='nrt', var_list=day_vars,
                    data_root=data_root)

    def day_refined():
        nrt_wrapper(day_or_night='day', pp_type='refined', var_list=day_vars,
                    data_root=data_root)

    def night_nrt():
        pass

    def night_refined():
        pass

    schedule.every().day.at("20:00").do(day_nrt)
    schedule.every().day.at("07:00").do(night_nrt)
    if refined:
        schedule.every().day.at("22:00").do(day_refined)
        schedule.every().day.at("20:00").do(night_refined)

    while True:
        schedule.run_pending()
        time.sleep(1)


    parser.add_argument('-day_vars', '--day_vars',
                        nargs = '*',
                        help = 'day time variables to process')

    parser.add_argument('-night_vars', '--night_vars',
                        nargs = '*',
                        help = 'night time variables to process')
