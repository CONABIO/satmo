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
