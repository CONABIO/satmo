#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-06-23
Purpose: Command line utility to launch near real time mode of the satmo with various
    options.
"""

import argparse
import satmo
import schedule
import time

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



    parser.add_argument('-day_vars', '--day_vars',
                        nargs = '*',
                        help = 'day time variables to process')

    parser.add_argument('-night_vars', '--night_vars',
                        nargs = '*',
                        help = 'night time variables to process')
