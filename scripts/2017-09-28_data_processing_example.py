#!/usr/bin/env bash

# Process standard variables from L2 for the 3 sensors for the year 2015
timerange_bin_map.py --aqua --terra --viirs -b 2015-01-01 -e 2015-12-31 -south 3 -north 33 -west -122 -east -72 -d /export/isilon/datos2/satmo2_data -day_vars chlor_a nflh Kd_490 sst -night_vars sst -multi 6

# Generate 8 days composites for aqua, viirs and terra for the same variables and the year 2015
timerange_time_compositing.py --aqua --terra --viirs -b 2015-01-01 -e 2015-12-31 -delta 8 -day_vars chlor_a nflh Kd_490 sst -night_vars sst -north 33 -south 3 -west -122 -east -72 -d /export/isilon/datos2/satmo2_data -multi 6

# Generate monthly composites for aqua, viirs and terra for the period 2000-2017 (for chlor_a, chl_ocx, sst and night sst)
timerange_time_compositing.py --aqua --terra --viirs -b 2015-01-01 -e 2015-12-31 -delta month -day_vars chlor_a nflh Kd_490 sst -night_vars sst -north 33 -south 3 -west -122 -east -72 -d /export/isilon/datos2/satmo2_data -multi 6



