9 June 2017, ideas to reorganize the satmo package

satmo
    utils
        pre_compose
        bit_pos_to_hex (could go directly under general satmo utils)
    oc (short for ocean color)
        utils
            parse_filename
            build_filename
            build_path
            find_path
            find_file
            is_day
            is_night
            to_kmo
            resolution_to_km_str
        query
        download
        process
            nc2tif
            Composer(object)
            FileComposer(Composer)
            BasicBinMap(object)
            L3mProcess(BasicBinMap)
        wrap
            make_daily_composite
            make_time_composite
        batch
            timerange_download
            timerange_L3m_process
            timerange_daily_composite
            timerange_time_composite
            timerange_make_preview
        visualize
            make_preview
            make_map_title
    hicom
        query
        download
    events (module to generate alerts, etc)


Hand drawing of desired satmo structure (11 July 2017):

![](docs/img/refactor.jpg)


Current state and description of the satmo, module by module:

- query:
    - list of functions:
        - query_from_extent
        - make_download_url
        - get_subscription_urls
    - Dependencies on other satmo modules:
        - None
    - Major improvements:
        - None
        - os Vs os.path
    - Minor improvements:
        - Remove urllib dependency and use requests instead (smoother python version
            compatibility)
        - Move make_download_url to oc.utils

- download:
    - list of functions:
        - download_file
        - dowload_to_tree
        - download_robust
    - Dependencies on other satmo modules:
        - utils
        - errors
    - Major improvements:
    - Minor improvements:
        - Not sure timeout is useful or even works
        - Merge all functions into one
        - os Vs os.path
     
- geo:
    - list of functions:
        - geo_dict_from_nc
        - get_raster_meta
    - Dependencies on other satmo modules:
        - utils
    - Major improvements:
        - Module should be called geo_utils
        - inconsistent naming (from Vs get)
    - Minor improvements:
        - first raster file should be x (geo_dict_from_nc)


- preprocessors:
    - list of functions:
        - bz2_unpack
        - bz2_compress
        - extractJob (class)
        - OC_l2bin
        - OC_l3mapgen
    - Dependencies on other satmo modules:
    - Major improvements:
    - Minor improvements:
        - Do something with commented out code
        - replace ifile by x

- preprocessors:
    - list of functions:
    - Dependencies on other satmo modules:
    - Major improvements:
    - Minor improvements:
