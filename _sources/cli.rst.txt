========================
Command Line Users Guide
========================

Satmo operates in two modes; an update mode, to download archive data and (re-)process these archive data, and a near real time mode.

These operation can be operated by a set of consistent command line interfaces.
The present document presents the main uses, features and examples of operation of the interface.

Update mode
===========

Update mode is used primarilly to download and process archive data. All command start by the prefix ``timerange``, indicating that their action apply to time range.

Download data
-------------

Description
^^^^^^^^^^^

The general data download interface is called ``timerange_download.py``; running ``timerange_download.py --help`` displays the help page of the command line interface.

> Note: Downloading full speed causes problems of breaking connection, it is therefore preferable to limit download speed with tools like **trickle**.
> In accordance with the recommandations of the CONABIO IT department the overall download speed for the whole system should not exceed 15 MB/s. Therefore if running two download commands in parallel, use for each command ``nohup trickle -d 7 timerange_download.py ... &``

Examples usage
^^^^^^^^^^^^^^

* L1A data download

.. code-block:: console

    $ nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &

* L2 data download

.. code-block:: console

    # Ocean color variables (Blue reflectances, chlor\_a, etc)
    $ nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -p OC --no-night -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &

    # Day time SST
    $ nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -p SST --no-night -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &

    # Night time SST
    $ nohup timerange_download.py --terra --aqua --viirs -b 2000-02-24 -e 2016-12-31 -north 32 -south 4 -west -121 -east -73 -p SST --no-day -d /export/isilon/datos2/satmo2_data/ > ~/dl_log.log &

L3m products processing
-----------------------

Description
^^^^^^^^^^^

The commands ``timerange_L3m_process.py`` generates L3m files, projected to a regular georeferenced grid, from the input L2 files, downloaded using the ``timerange_download.py`` command line interface. Each variable has to be processed separately (But multiple sensors can be processed at the same time). Running ``timerange_L3m_process.py --help`` displays the help page of the command line interface.

Examples usage
^^^^^^^^^^^^^^

.. code-block:: console

    # Process Cholorophyll-a at 2000 m resolution for aqua, terra and viirs.
    $ nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4 &

    # Process SST at 2000 m resolution for aqua, terra and viirs.
    $ nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s SST -v sst -mask 0x1002 -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4 &

    # Process PAR at 2000 m resolution for aqua, terra and viirs.
    $ nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s PAR -v par -mask 0x600000a -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4 &

    # Process FLH at 2000 m resolution for aqua, terra and viirs.
    $ nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s FLH -v nflh -mask 0x679d73f -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4 &

    # Process NSST at 2000 m resolution for aqua, terra and viirs (note the `--night` flag)
    $ nohup timerange_L3m_process.py --aqua --terra --viirs -b 2000-01-01 -e 2017-05-10 -s NSST -v sst -mask 0x2 --night -d /export/isilon/datos2/satmo2_data/ -r 2000 --overwrite -north 33 -south 3 -west -122 -east -72 -multi 4 &


Generate multisensor composites
-------------------------------

Description
^^^^^^^^^^^

The command ``timerange_daily_composite.py`` produces multi sensors composites (e.g.: Data from aqua and terra, acquired on the same day are combined into a single product). The input files for this operation are sensor specific L3m files; it is therefore essential to run ``timerange_L3m_process.py`` prior to this command. The files generated use the sensor code prefix ``X`` and are written to the ``combined`` sensor subdirectory of the data archive. Running ``timerange_daily_composite.py --help`` displays the help page of the command line interface.


Examples usage
^^^^^^^^^^^^^^

.. code-block:: console

    # Combine chlorophyll-a data from all the sensors available:
    $ nohup timerange_daily_composite.py -b 2000-01-01 -e 2016-12-31 -v chlor_a -s CHL -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite -multi 4 &

Generate time composites
------------------------

Description
^^^^^^^^^^^

The command ``timerange_time_composite.py`` produces temporal composites for a given variable using daily data from a given sensor (which can be combined (default)). Running ``timerange_time_composite.py --help`` displays the help page of the command line interface.

Examples usage
^^^^^^^^^^^^^^

.. code-block:: console

    # Generate 16 days composites from the daily composites of chlorophyll-a produced by the `timerange_daily_composite.py` command.
    $ nohup timerange_time_composite.py -b 2000-01-01 -e 2017-06-01 -delta 16 -s CHL -v chlor_a -d /export/isilon/datos2/satmo2_data/ -r 2km --overwrite --preview -multi 4

Near real time mode
===================

The main command to operate satmo near real time mode is called ``satmo_nrt.py``.

Description
-----------

``satmo_nrt.py`` starts the near real time mode of the satmo system. The current version of the near real time mode handles downloading of NRT and refined processing data, processing to L3m level and production of daily and temporal composites (8 and 16 days).
Running ``satmo_nrt.py --help`` displays the help page of the command line interface.

Examples usage
--------------

.. code-block:: console

    # Start the system with download of NRT + refined processing L2 data, processing of `chlor_a`, `nflh` and `sst` (day and night), at 2km resolution
    $ nohup satmo_nrt.py --day_vars chlor_a nflh sst Kd_490 --night_vars sst --north 33 --south 3 --west -122 --east -72 -d /export/isilon/datos2/satmo2_data/ -r 2000 > ~/nrt_log.log &

