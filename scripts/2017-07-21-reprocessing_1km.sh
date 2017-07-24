#!/usr/bin/env bash

# Re-processing of the entire archive at 1km resolution.
# A bug in the sst and night sst binning routine was found after running these scripts so that part of these
# commands will have to be re-ran once the bug is fixed

# Spatial binning to regular laea grid
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 8
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x679d73f -multi 8
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 8
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x1002 -multi 8
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s NSST -v sst --night -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x2 -multi 8

# Produce daily composites
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v chlor_a -s CHL -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v nflh -s FLH -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v Kd_490 -s KD490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v sst -s SST -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v sst -s NSST -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 

# Produce 8 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 

# Produce 16 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 

# produce monthly composites
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
