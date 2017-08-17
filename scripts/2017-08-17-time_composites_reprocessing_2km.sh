#!/usr/bin/env bash

# --preview falg was enabled for the previous processing done on 2017-08-11 (for time composites only)
# which resulted in the process crashing entirely. This script reprocesses temporal composites without
# the --preview flag

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

