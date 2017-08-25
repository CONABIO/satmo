#!/usr/bin/env bash

# I discovered a bug in the last processing batch (when doing cross sensor compositing), the
# compositing algorithm when sensor_codes was set to all was including existing combined
# files from previous preprocessing in the generation of the new composites. This was fixed in commit
# 18ae6d

# Produce daily composites
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-09 -v chlor_a -s CHL -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-09 -v nflh -s FLH -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-09 -v Kd_490 -s KD490 -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-09 -v sst -s SST -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-09 -v sst -s NSST -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 


# Produce 8 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 8 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 8 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 8 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 

# Produce 16 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 16 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 16 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 16 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 

# produce monthly composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta month -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta month -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta month -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-09 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 

# end message
echo Processing done


