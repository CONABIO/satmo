#!/usr/bin/env bash

# A Bug was discovered in the spatial binning and masking step whendealing with sst. Previously processed
# sst and night sst products have large amounts of low quality/unfiltered data included.
# The script below reprocesses the entire archive, overwritting previously generated results

timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x1002 -multi 8
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s NSST -v sst --night -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x2 -multi 8

timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x1002 -multi 8
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-07-20 -s NSST -v sst --night -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x2 -multi 8

# Spatial binning
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v sst -s SST -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v sst -s NSST -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 8 

timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v sst -s SST -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 8 
timerange_daily_composite.py -b 2000-01-01 -e 2017-07-20 -v sst -s NSST -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 8 

# 8 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 

timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 8 

# 16 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 

timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 8 

# Monthly composites
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 8 

timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 8 
timerange_time_composite.py -b 2000-01-01 -e 2017-07-20 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 8 
