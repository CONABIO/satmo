#!/usr/bin/env bash

# Reprocessing the entire archive at 1km, with 4 cores, 

# Spatial binning to regular laea grid
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-08-15 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-08-15 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x679d73f -multi 4
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-08-15 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-08-15 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x1002 -multi 4
timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-08-15 -s NSST -v sst --night -d /export/isilon/datos2/satmo2_data/ -r 1000 --overwrite -north 33 -south 3 -west -122 -east -72 -mask 0x2 -multi 4

# Produce daily composites
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-15 -v chlor_a -s CHL -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-15 -v nflh -s FLH -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-15 -v Kd_490 -s KD490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-15 -v sst -s SST -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_daily_composite.py -b 2000-01-01 -e 2017-08-15 -v sst -s NSST -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 

# Produce 8 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 8 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 8 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 8 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 8 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 8 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 

# Produce 16 days composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 16 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 16 -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 16 -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 16 -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta 16 -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 

# produce monthly composites
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta month -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta month -s FLH -v nflh -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta month -s KD490 -v Kd_490 -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta month -s SST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 
timerange_time_composite.py -b 2000-01-01 -e 2017-08-15 -delta month -s NSST -v sst -d /export/isilon/datos2/satmo2_data/ -r 1km --overwrite -multi 4 

# end message
echo Processing done
