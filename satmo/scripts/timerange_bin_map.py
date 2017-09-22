#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-09-21
Purpose: Produces L3m files via binning an mapping existing L2 variable via seadas
l2bin and l2mapgen utilities. The cli works for a range of date and supports parallel processing.
"""

import argparse
import satmo

def main(aqua, terra, viirs, seawifs, begin, end, north, south, west, east,
         data_root, binning_resolution, mapping_resolution, proj, flags,
         day_vars, night_vars, overwrite, n_threads):
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

    satmo.bin_map_batcher(begin=begin, end=end, sensor_codes=sensor_codes,
                          south=south, north=north, west=west, east=east,
                          data_root=data_root, binning_resolution=binning_resolution,
                          mapping_resolution=mapping_resolution, day_vars=day_vars,
                          night_vars=night_vars, flags=flags, proj=proj, overwrite=overwrite,
                          n_threads=n_threads)

if __name__ == '__main__':
    epilog = """
COmmand line Utility to batch process L3m files from existing L2 variables. Runs the seadas
commands l2bin and l3mapgen, for a set of dates, sensors and variables. Support parallel processing
Additionally to the description of the cli argumnts below, see the satmo functions processors.l2bin,
processors.l3mapgen and wrappers.bin_map_wrapper for details on defaults used for flags, binnning resolution, etc

-------------------
Examples usage
-------------------

# Process chlor_a, night sst, sst, and chl_ocx for viirs, aqua and terra between 2000 and 2017
timerange_bin_map.py --aqua --terra --viirs -b 2000-01-01 -e 2017-12-31 -south 3 -north 33 -west -122 -east -72\
        -d /export/isilon/datos2/satmo2_data -bin_res 1 -map_res 1000 -day_vars chlor_a chl_ocx sst\
        -night_vars sst -multi 6
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

    parser.add_argument('-day_vars', '--day_vars', nargs = '*',
                        required = True,
                        help = 'Day time L3m variables to process (e.g. chlor_a). Can receive multiple arguments')

    parser.add_argument('-night_vars', '--night_vars', nargs = '*',
                        required = True,
                        help = 'Night time L3m variables to process (e.g. sst). Can receive multiple arguments')

    parser.add_argument("-d", "--data_root",
                        required=True,
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

    parser.add_argument('--no-overwrite', action='store_false',
                       help = 'Disable defaults overwritting of existing files')

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)
    parsed_args = parser.parse_args()

    main(**vars(parsed_args))

