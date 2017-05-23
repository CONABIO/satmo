# Processing mode

- Update archive
- Process new variables for the entire archive

## Download data

> Note: Downloading full speed causes problems of breaking connection (and the IT department doesn't like it much), it is therefore preferable to limit download speed with tools like **trickle**.
> In accordance with the recommandations of the IT department the overall download speed for the whole system should not exceed 15 MB/s. Therefore if running two download commands in parallel, use for each command `nohup trickle -d 7 timerange_download.py ... &`

### L1A data

`nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &`


### L2 collections

Ocean color variables (Blue reflectances, chlor\_a, etc)
`nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -p OC --no-night -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &`

Day time SST
`nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -p SST --no-night -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &`

Night time SST
`nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -p SST --no-day -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &`

## Process a L3m variable for the entire archive

- Generates L3m files, projected to a regular grid using a custom binning algorithm. Input data are L2 files.
- Support multi core processing
- Although the engine can process new variables on the fly, the current version of the CLI (23 May 2017) requires that the variable selected already exist in the L2 files.
- Each variable has to be processed separately (But multiple sensors can be processed at the same time)

### Examples

- Cholorophyl a

`nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -multi 4 -north 33 -south 3 -west -122 -east -72 -multi 4 &`

- SST

`nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s SST -v sst -mask 0x1002 -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -multi 4 -north 33 -south 3 -west -122 -east -72 -multi 4 &`

- PAR

`nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s PAR -v par -mask 0x600000a -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -multi 4 -north 33 -south 3 -west -122 -east -72 -multi 4 &`

- FLH

`nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s FLH -v nflh -mask 0x679d73f -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -multi 4 -north 33 -south 3 -west -122 -east -72 -multi 4 &`

- NSST

`nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s NSST -v sst -mask 0x2 --night -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -multi 4 -north 33 -south 3 -west -122 -east -72 -multi 4 &`


## Generate multisensor composites

- Output data are written in the `combined` archive (sensor code `X`)
- Can only be ran once `timerange_L3m_process.py` has completed.
- Each variable has to be processed separately

### Examples

`nohup timerange_daily_composite.py -b 2000-01-01 -e 2016-12-31 -v chlor_a -s CHL -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 &`

## Generate time composites

`nohup timerange_time_composite.py -b 2000-01-01 -e 2017-06-01 -delta 16 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4`

## Generate climatologies


## Generate anomalies


# Operational mode

- Automatically download newly acquired data
- Process variables upon download


# Installation

There is an optional dependency on matplotlib basemap for generating png previews (available in most cli with the --preview flag). Basemap won't be automoatically installed (because it is a heavy package and is not on pypi).
To install it: `pip install https://github.com/matplotlib/basemap/archive/v1.1.0.tar.gz`
