#!/usr/bin/env bash

# Preview reprocessing ended up stopping for memory limit. Memory is particularly critical when
# producing temporal composites. IN the case of monthly composites at 1km resolution for example
# 31 arrays of shape (5000, 3352) (datatype float32) have to be loaded in memory for each process
# independently. This script attemps to re-run compositing, with reduced number of parallel processes


# Produce 8 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 

# 2km
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4 


# Produce 16 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 

# 2km
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4 


# produce monthly composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite --preview -multi 4 

# 2km
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-05 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4 

# end message
echo Processing done
