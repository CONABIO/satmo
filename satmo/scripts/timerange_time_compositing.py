#!/usr/bin/env python

"""
Author: Loic Dutrieux
Date: 2017-09-25
Purpose: Produces time composites via temporal binning (seadas l3bin) and mapping
(seadas l3mapgen)"""

import satmo
import argparse

def main(aqua, terra, viirs, seawifs, begin, end, delta, day_vars, night_vars,
         south, north, west, east, mapping_resolution, proj, data_root,
         overwrite, n_threads):
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

    # Deal with the delta
    if delta.isdigit():
        delta = int(delta)
        # Generate composite name
        composite = '%dDAY' % delta
    elif delta == 'month':
        composite = 'MO'
    else:
        raise ValueError('--delta must be an integer or month')

    # Day variables processing
    if day_vars is not None:
        satmo.l3bin_map_batcher(begin=begin, end=end, delta=delta, sensor_codes=sensor_codes,
                                var_list=day_vars, night=False, south=south, north=north,
                                west=west, east=east, composite=composite, data_root=data_root,
                                mapping_resolution=mapping_resolution, proj=proj, overwrite=overwrite,
                                n_threads=n_threads)

    # NIght variables processing
    if night_vars is not None:
        satmo.l3bin_map_batcher(begin=begin, end=end, delta=delta, sensor_codes=sensor_codes,
                                var_list=night_vars, night=True, south=south, north=north,
                                west=west, east=east, composite=composite, data_root=data_root,
                                mapping_resolution=mapping_resolution, proj=proj, overwrite=overwrite,
                                n_threads=n_threads)
if __name__ == '__main__':
    epilog = """
Command line to produce temporal composites via temporal binning and mapping (seadas l3bin and l3mapgen).

---------------------------
Examples Usage
---------------------------
# Generate 8 days composites for aqua, viirs and terra for the period 2000-2017 (for chlor_a, chl_ocx, sst and night sst)
timerange_time_compositing.py --aqua --terra --viirs -b 2000-01-01 -e 2017-12-31 -delta 8 -day_vars chlor_a chl_ocx sst -night_vars sst -north 33 -south 3 -west -122 -east -72 -d /export/isilon/datos2/satmo2_data

# Generate monthly composites for aqua, viirs and terra for the period 2000-2017 (for chlor_a, chl_ocx, sst and night sst)
timerange_time_compositing.py --aqua --terra --viirs -b 2000-01-01 -e 2017-12-31 -delta month -day_vars chlor_a chl_ocx sst -night_vars sst -north 33 -south 3 -west -122 -east -72 -d /export/isilon/datos2/satmo2_data
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

    parser.add_argument('-delta', '--delta',
                       required = True,
                       type = str,
                       help = 'Compositing period, in number of days, or \'month\' to create monthly composites.')

    parser.add_argument('-day_vars', '--day_vars', nargs = '*',
                        required = False, default=None,
                        help = 'OPtional day time L3m variables to process (e.g. chlor_a). Can receive multiple arguments')

    parser.add_argument('-night_vars', '--night_vars', nargs = '*',
                        required = False, default=None,
                        help = 'OPtional night time L3m variables to process (e.g. sst). Can receive multiple arguments')

    parser.add_argument("-d", "--data_root",
                        required=True,
                        help="Root of the local archive")

    parser.add_argument("-map_res", "--mapping_resolution",
                        required=False,
                        type = int,
                        help="Output resolution in meters (defaults to 1000)")
    parser.set_defaults(mapping_resolution=1000)

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

    parser.add_argument('--no-overwrite', action='store_false', dest='overwrite',
                       help = 'Disable defaults overwritting of existing files')
    parser.set_defaults(overwrite=True)

    parser.add_argument('-multi', '--n_threads',
                        type = int,
                        required = False,
                        help = 'Number of threads to use for parallel implementation')
    parser.set_defaults(n_threads=1)
    parsed_args = parser.parse_args()

    main(**vars(parsed_args))

