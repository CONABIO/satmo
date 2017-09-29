from datetime import datetime, timedelta
import itertools
import multiprocessing as mp
import functools
import os
from pprint import pprint
import warnings

from .query import query_from_extent, make_download_url, get_subscription_urls
from .download import download_robust
from .utils import (file_finder, is_day,
                    is_night, resolution_to_km_str, filename_builder,
                    filename_parser, pre_compose, processing_meta_from_list,
                    find_composite_date_list, time_limit, viirs_geo_filename_builder,
                    get_date_list)
from .preprocessors import l2gen

from .global_variables import (L2_L3_SUITES_CORRESPONDENCES, SUBSCRIPTIONS, L3_SUITE_FROM_VAR,
                               BIT_MASK_FROM_L3_SUITE, QUAL_ARRAY_NAME_FROM_SUITE,
                               BAND_MATH_FUNCTIONS, FLAGS, VARS_FROM_L2_SUITE,
                               SENSOR_CODES, STANDARD_L3_SUITES)
from .processors import (L3mProcess, FileComposer, make_time_composite, l2_append,
                         l2mapgen, l3mapgen, l2bin, l3bin)
from .visualization import make_preview
from .errors import TimeoutException

def timerange_download(sensors, begin, end, write_dir,\
                north, south, west, east, day = True, night = True,\
                product = 'L1A', overwrite = False, check_integrity = False):
    """Queries and download data for a given timerange

    Wrapper around downdload and query

    Args:
        sensors: (list) list of strings, Valid entries are 'am' (aqua), 'tm' (terra),
            'sw' (seawifs), 'v0' (viirs)
        begin (datetime or str): Beginning of time range. 'yyyy-mm-dd' if str
        end (datetime or str): End of time range. 'yyyy-mm-dd' if str
        write_dir (str): Host directory to which the data will be written
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        day (bool): Order day data ?
        night (bool): Order night data ?
        product (str): Product to order, defaults to 'L1A'. Other possible values include
            'CHL' for L2_OC, 'SST' for L2_SST, and 'SST4' for L2_SST4
        overwrite (bool): Should existing files on the host be overwritten
        check_integrity (bool): Only makes sense if overwrite is set to False (when updating the archive)

    Returns:
        list: list of boolean
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    ndays = (end - begin).days + 1
    date_range = [begin + timedelta(days=x) for x in range(0, ndays)]
    local_files_list = []
    for item in date_range:
        try:
            file_list = query_from_extent(sensors, item, 'DAY', north, south, west, east,
                                          day = day, night = night, product = product)
        except Exception as e:
            pprint('Error encountered for %s' % item.isoformat())
            pprint(e.message)
            continue
        url_list = [make_download_url(x) for x in file_list]
        # Viirs only: Build urls of GEO files and append to url list
        geo_files = [viirs_geo_filename_builder(x) for x in url_list if filename_parser(x)['sensor'] == 'viirs']
        url_list += geo_files
        for url in url_list:
            local_file = download_robust(url, write_dir, overwrite = overwrite,
                                         check_integrity = check_integrity)
            local_files_list.append(local_file)
    return local_files_list

def make_daily_composite(date, variable, suite, data_root, resolution,
                         sensor_codes = 'all',
                         fun='mean', filename = None, preview=True,
                         overwrite=False):
    """Wrapper for making daily composites (from multiple sensors)

    Args:
        date (str or datetime): Date of the data to be composited
        variable (str): L3m variable (e.g. 'chlor_a')
        suite (str): L3m suite (e.g. 'CHL')
        data_root (str): Root of the data archive
        resolution (str): e.g. '1km'
        sensor_codes (list): Sensors to include in the composite. Defaults to
            'all', which is automatically transformed to ['A', 'T', 'V'] for
            aqua, terra and viirs.
        fun (str): Compositing function. Can be 'mean', 'median', 'min', 'max'.
            Defaults to 'mean'
        filename (str): Optional output filename. Defaults to None, in which
            case the filename is automatically generated.
        preview (bool): Generate a png preview. Defaults to True
        overwrite (bool): Overwrite existing L3m file. Defaults to False

    Returns:
        str: The filename of the created composite.

    Examples:
        >>> import satmo

        >>> satmo.make_daily_composite(date='2016-01-01', variable='chlor_a', suite='CHL',
                                       resolution='2km',
                                       data_root='/home/ldutrieux/sandbox/satmo2_data',
                                       overwrite=True, fun='mean', sensor_codes=['A', 'V'])

    """
    # Search the files that correspond to a date/variable, etc Do not restrict
    # sensor code
    file_list = file_finder(data_root=data_root, date=date, level='L3m',
                               suite=suite, variable=variable,
                               resolution=resolution, composite='DAY',
                               sensor_code=None)
    # Filter in case only a subset of the sensors is asked
    if sensor_codes == 'all':
        sensor_codes = ['A', 'T', 'V']
    file_list = [x for x in file_list if filename_parser(x)['sensor_code'] in sensor_codes]
    # Given a date (string or datetime), a variable (e.g. chlor_a) and a list of sensors, make 
    compositing_class = FileComposer(*file_list)
    # Run the compositing method using string provided in fun= argument
    func = getattr(compositing_class, fun)
    func()
    # Generate filename if not provided
    if filename is None:
        filename = filename_builder(level='L3m', full_path=True,
                                       data_root=data_root, date=date,
                                       sensor_code='X',
                                       suite=suite,
                                       composite='DAY', variable=variable,
                                       resolution=resolution)
    if not (os.path.isfile(filename) and not overwrite):
        # Create directory if not already exists
        out_dir = os.path.dirname(filename)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        compositing_class.to_file(filename)
        if preview:
            make_preview(filename)
    return filename


def make_daily_composite_error_catcher(date, variable, suite, data_root, resolution,
                                       sensor_codes = 'all',
                                       fun='mean', filename = None, preview=True,
                                       overwrite=False):
    try:
        make_daily_composite(date=date, variable=variable, suite=suite,
                             data_root=data_root, resolution=resolution,
                             sensor_codes=sensor_codes,
                             fun=fun, filename=filename, preview=preview,
                             overwrite=overwrite)
    except Exception as e:
        pprint('%s composite, could not be processed, reason: %s' % (str(date),
                                                                str(e)))


def timerange_daily_composite(begin, end, variable, suite, data_root,
                              resolution, sensor_codes='all', fun='mean',
                              preview=True, overwrite=False, n_threads=1):
    """Produce daily composite for individual dates in a time-range in batch

    Args:
        begin (datetime or str): Beginning of time range. 'yyyy-mm-dd' if str
        end (datetime or str): End of time range. 'yyyy-mm-dd' if str
        n_threads (int): Number of threads to use for running the
            make_daily_composite function in parallel.
        others (*): See help of make_daily_composite for the other parameters.

    Examples:
        >>> import satmo

        >>> satmo.timerange_daily_composite(begin='2015-01-01', end='2016-06-30',
                                            variable='chlor_a', suite='CHL',
                                            data_root='/home/ldutrieux/sandbox/satmo2_data',
                                            resolution='2km')

    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    ndays = (end - begin).days + 1
    date_range = [begin + timedelta(days=x) for x in range(0, ndays)]
    kwargs = {'sensor_codes': sensor_codes,
              'suite': suite,
              'variable': variable,
              'data_root': data_root,
              'resolution': resolution,
              'fun': fun,
              'overwrite': overwrite,
              'preview': preview}
    pool = mp.Pool(n_threads)
    # Use of map_async().get(9999999) enables KeyboardInterrupt to work
    pool.map_async(functools.partial(make_daily_composite_error_catcher,
                                         **kwargs), date_range).get(9999999)

def l2mapgen_wrapper(date, sensor_codes, var, south, north, west, east, data_root,
                     night=False, flags=None, width=5000, outmode='tiff',
                     overwrite=False, threshold=0):
    """Runs l2mapgen for a given variable on all the files of a given date.

    All possible errors are caugth

    Args:
        date (datetime or str): Date of L2 data to process
        sensor_codes (list): List of strings corresponding to sensor codes to process
        var (str): Variable to process
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        data_root (str): Root of the data archive
        night (bool): Is night data? Default to False
        flags (list): List of flags to apply. Defaults to None, in which case
            default flags for the product suite are retrieved from the FLAGS global
            variable and used
        width (int): Width in pixels of the output image
        outmode (str): See seadas l2mapgen doc
        overwrite (bool): Overwrite existing files? Return ValueError if file exists
            and overwrite is set to False (default)
        threshold (float): Minimum percentage of the filled pixels


    """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    # Determine L2 suite corresponding to var
    dn = 'night' if night else 'day'
    l3_suite = L3_SUITE_FROM_VAR[dn][var]
    l2_suite = L2_L3_SUITES_CORRESPONDENCES[l3_suite]
    if flags is None:
        flags = FLAGS[l3_suite]

    # Query L2 files
    for sensor_code in sensor_codes:
        file_list = file_finder(data_root=data_root, date=date, level='L2',
                                   suite=l2_suite, sensor_code=sensor_code)
        if file_list:
            for file in file_list:
                try:
                    l2mapgen(x=file, north=north, south=south, west=west,
                             east=east, prod=var, flags=flags, data_root=data_root,
                             width=width, outmode=outmode, threshold=threshold,
                             overwrite=overwrite)
                except Exception as e:
                    pprint('An error occured while processing %s file. %s' % (file, e))

def l2mapgen_batcher(begin, end, sensor_codes, var, south, north, west, east,
                     data_root, night=False, flags=None, width=5000,
                     outmode='tiff', overwrite=False, threshold=0, n_threads=1):
    """Batch L2m processing with parallel support; to be ran from cli
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    # Get list of individual dates between begin and end
    ndays = (end - begin).days + 1
    date_list = [begin + timedelta(days=x) for x in range(0, ndays)]
    # Build kwargs
    kwargs = {'sensor_codes': sensor_codes,
              'var': var,
              'south': south,
              'north': north,
              'west': west,
              'east': east,
              'data_root': data_root,
              'night': night,
              'flags': flags,
              'width': width,
              'outmode': outmode,
              'overwrite': overwrite,
              'threshold': threshold}
    # Run wrapper for every date with // support
    pool = mp.Pool(n_threads)
    pool.map_async(functools.partial(l2mapgen_wrapper, **kwargs), date_list).get(9999999)

def l2gen_wrapper(date, sensor_codes, var_list, suite, data_root, night=False,
                  get_anc=True):
    """Runs l2gen on all the files of a given date.

    All possible errors are caught

    Args:
        date (datetime or str): Date of L2 data to process
        sensor_codes (list): List of strings corresponding to sensor codes to process
        var_list (list): List of strings representing the variables to process
        suite (str): Output L2 suite name
        data_root (str): Root of the data archive
        night (bool): Is night data? Default to False
        get_anc (bool): Download ancillary data for improved atmospheric correction.
            Defaults to True.

    Examples:
        >>> import satmo
        >>> l2gen_wrapper(date='2004-11-21', sensor_codes=['A', 'T', 'V'],
        >>>               var_list=['chlor_a'], data_root='/export/isilon/datos2/satmo2_data',
        >>>               suite='OC3', night=False, get_anc=True)

    Returns:
        list: List of processed L2 files
    """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    # Query L2 files
    out_list = []
    for sensor_code in sensor_codes:
        file_list = file_finder(data_root=data_root, date=date, level='L1A',
                                   sensor_code=sensor_code)
        # Filter for day/night files
        file_list = [x for x in file_list if is_night(x) is night]
        if file_list:
            for file in file_list:
                try:
                    out = l2gen(file, var_list=var_list, suite=suite, data_root=data_root,
                                get_anc=get_anc)
                    out_list.append(out)
                except Exception as e:
                    pprint('An error occured while processing %s file. %s' % (file, e))
    return out_list

def l2_append_wrapper(date, sensor_codes, var, suite, data_root):
    """Wrapper to run l2_append on all matching files of a given date

    Args:
        date (datetime or str): Date of L2 data to process
        sensor_codes (list): List of strings corresponding to sensor codes to process
        var (str): Short name of the variable to process. Must exist in the
            global variable BAND_MATH_FUNCTIONS.
        suite (str): Suite name of the L2 files containing the required input
            bands.
        data_root (str): Root of the data archive

    Returns:
        list: The list of files to which a variable was appended. However, the
        function is mostly used for its side effect of appending a variable
        to each file of a list of netcdf files.
    """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    # Query L2 files
    out_list = []
    for sensor_code in sensor_codes:
        sensor = SENSOR_CODES[sensor_code]
        file_list = file_finder(data_root=data_root, date=date, level='L2',
                                   sensor_code=sensor_code, suite=suite)
        if file_list:
            for file in file_list:
                try:
                    kwargs = BAND_MATH_FUNCTIONS[var][sensor]
                    out = l2_append(file, **kwargs)
                    out_list.append(out)
                except Exception as e:
                    pprint('An error occured while appending variable %s to %s. %s' % (var, file, e))

def l2_append_batcher(begin, end, sensor_codes, var, suite, data_root,
                      n_threads=1):
    """Compute a new variable and append it to existing L2 files in batch mode
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    # Get list of individual dates between begin and end
    ndays = (end - begin).days + 1
    date_list = [begin + timedelta(days=x) for x in range(0, ndays)]
    # Build kwargs
    kwargs = {'sensor_codes': sensor_codes,
              'var': var,
              'suite': suite,
              'data_root': data_root}
    # Run wrapper for every date with // support
    pool = mp.Pool(n_threads)
    pool.map_async(functools.partial(l2_append_wrapper, **kwargs), date_list).get(9999999)

def l2gen_batcher(begin, end, sensor_codes, var_list, suite, data_root, night=False,
                  get_anc=True, n_threads=1):
    """Batch L2 processing with parallel support; to be ran from cli
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    # Get list of individual dates between begin and end
    ndays = (end - begin).days + 1
    date_list = [begin + timedelta(days=x) for x in range(0, ndays)]
    # Build kwargs
    kwargs = {'sensor_codes': sensor_codes,
              'var_list': var_list,
              'suite': suite,
              'get_anc': get_anc,
              'data_root': data_root,
              'night': night}
    # Run wrapper for every date with // support
    pool = mp.Pool(n_threads)
    pool.map_async(functools.partial(l2gen_wrapper, **kwargs), date_list).get(9999999)

def bin_map_wrapper(date, sensor_codes, south, north, west, east, data_root,
                    binning_resolution = 1, mapping_resolution = 1000,
                    day_vars = None, night_vars = None, flags = None,
                    proj = None, overwrite = True):
    """Wrapper to run l2bin and l3mapgen for a list of variables and a given date

    The function automatically handles the production of the right intermediary
    L3b files.

    Args:
        date (str or datetime): Date of the data to process
        sensor_codes (list): List to sensor codes to include in the processing
        south (int or float): south latitude of mapped file extent
        north (int or float): north latitude of mapped file extent
        west (int or float): west longitude of mapped file extent
        east (int or float): east longitude of mapped file extent
        data_root (str): Root of the data archive.
        binning_resolution (int or str): See resolve argument in l2bin doc
        mapping_resolution (int): Resolution of the output L3m file in meters
        day_vars (list): List of day variables to map (will result in one L3m file being
            produced for each var and each sensor)
        night_vars (list): List of night variables to map (will result in one L3m file being
            produced for each var and each sensor)
        flags (list): A list of flags to mask invalid data (e.g. ['CLDICE', 'LAND', 'HIGLINT'])
            If None (default), a default list of flag for the L3 suite is fetched from
            the global variable FLAGS. When processing several variables belonging to
            different suites, it is not recommended to set a fixed list of flags, since they
            normally differ between suites.
        proj (str): Optional proj4 string. If None (default), a lambert Azimutal Equal Area projection (laea), centered
            on the provided extent is used.
        overwrite (bool): Overwrite existing final (L3m) and intermediary (L3b) files

    Returns:
        This function is used for its side effects of binning and then mapping data,
        producing as a result various L3b and L3m files
    """
    # Day processing
    # For each sensor
    if day_vars is not None:
        for sensor_code in sensor_codes:
            sensor = SENSOR_CODES[sensor_code]
            # Get list of L3 suite (day)
            l3_suites = [L3_SUITE_FROM_VAR['day'][var] for var in day_vars]
            # Remove duplicates
            l3_suites = list(set(l3_suites))
            # Get final list of variables
            var_dict = {}
            for l3_suite in l3_suites:
                var_dict[l3_suite] = list(set(day_vars).intersection(STANDARD_L3_SUITES[l3_suite][sensor]))
            # For each suite
            for suite in l3_suites:
                if var_dict[suite]: # Check that list is not empty
                    # Determine corresponding L2 suite
                    l2_suite = L2_L3_SUITES_CORRESPONDENCES[suite]
                    # Identify L2 input files
                    try:
                        l2_file_list = file_finder(data_root=data_root, date=date, level='L2',
                                                      suite=l2_suite, sensor_code=sensor_code)
                        # Filter to keep day data only
                        l2_file_list = [x for x in l2_file_list if is_day(x)]
                        # Run l2bin
                        l3b_file = l2bin(file_list=l2_file_list, L3b_suite=suite, var_list=var_dict[suite],
                                         resolution=binning_resolution, night=False, data_root=data_root,
                                         overwrite=overwrite, flags=flags)
                    except Exception as e:
                        pprint('Error generating l3b file for %s, %s, %s' % (suite, date.strftime('%Y-%m-%d'), e))
                        continue
                    # for each var in var_list
                    for var in var_dict[suite]:
                        try:
                            # Run l3mapgen
                            l3mapgen(x=l3b_file, variable=var, south=south, north=north,
                                     west=west, east=east, resolution=mapping_resolution,
                                     proj=proj, data_root=data_root, overwrite=overwrite)
                        except Exception as e:
                            pprint('Error generating l3m file for %s, %s, %s' % (var, date.strftime('%Y-%m-%d'), e))
    # Night processing
    if night_vars is not None:
        for sensor_code in sensor_codes:
            sensor = SENSOR_CODES[sensor_code]
            # Get list of L3 suite (day)
            l3_suites = [L3_SUITE_FROM_VAR['night'][var] for var in night_vars]
            # Remove duplicates
            l3_suites = list(set(l3_suites))
            # Get final list of variables
            var_dict = {}
            for l3_suite in l3_suites:
                var_dict[l3_suite] = list(set(night_vars).intersection(STANDARD_L3_SUITES[l3_suite][sensor]))
            # For each suite
            for suite in l3_suites:
                if var_dict[suite]: # Check that list is not empty
                    # Determine corresponding L2 suite
                    l2_suite =  L2_L3_SUITES_CORRESPONDENCES[suite]
                    try:
                        # Identify L2 input files
                        l2_file_list = file_finder(data_root=data_root, date=date, level='L2',
                                                      suite=l2_suite, sensor_code=sensor_code)
                        # Filter to keep night data only
                        l2_file_list = [x for x in l2_file_list if is_night(x)]
                        # Run l2bin
                        l3b_file = l2bin(file_list=l2_file_list, L3b_suite=suite, var_list=var_dict[suite],
                                         resolution=binning_resolution, night=True, data_root=data_root,
                                         overwrite=overwrite, flags=flags)
                    except Exception as e:
                        pprint('Error generating l3b file for %s, %s, %s' % (suite, date.strftime('%Y-%m-%d'), e))
                        continue
                    for var in var_dict[suite]:
                        try:
                            # Run l3mapgen
                            l3mapgen(x=l3b_file, variable=var, south=south, north=north,
                                     west=west, east=east, resolution=mapping_resolution,
                                     proj=proj, data_root=data_root, overwrite=overwrite)
                        except Exception as e:
                            pprint('Error generating l3m file for %s, %s, %s' % (var, date.strftime('%Y-%m-%d'), e))

def bin_map_batcher(begin, end, sensor_codes, south, north, west, east, data_root,
                    binning_resolution = 1, mapping_resolution = 1000,
                    day_vars = None, night_vars = None, flags = None,
                    proj = None, overwrite = True, n_threads = 1):
    """Batch processing of L3m data from L2 for several dates, sensors and variables
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    # Get list of individual dates between begin and end
    ndays = (end - begin).days + 1
    date_list = [begin + timedelta(days=x) for x in range(0, ndays)]
    # Build kwargs
    kwargs = {'sensor_codes': sensor_codes,
              'south': south,
              'north': north,
              'west': west,
              'east': east,
              'data_root': data_root,
              'binning_resolution': binning_resolution,
              'mapping_resolution': mapping_resolution,
              'day_vars': day_vars,
              'night_vars': night_vars,
              'flags': flags,
              'proj': proj,
              'overwrite': overwrite}
    # Run wrapper for every date with // support
    pool = mp.Pool(n_threads)
    pool.map_async(functools.partial(bin_map_wrapper, **kwargs), date_list).get(9999999)

def l3bin_wrapper(sensor_codes, date_list, suite_list, south, north, west, east,
                  composite, data_root, overwrite=False):
    """Wrapper to run l3bin without having to name explicitly input or output files

    Args:
        sensor_codes (list): List of sensor codes to include (e.g.: ['A', 'T', 'V']
        date_list (list): List of dates
        suite_list (list): List of L3 suites to include
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        data_root (str): Root of the data archive
        composite (str): Composite type (8DAY, MON)
        overwrite (bool): Overwrite existing files?

    Returns:
        list: List of L3b files generated. Mostly used for its side effect of generating
        temporally composited L3b files from daily L3b files.
    """
    out_list = []
    for sensor_code in sensor_codes:
        for suite in suite_list:
            file_list = []
            for date in date_list:
                file = file_finder(data_root=data_root, date=date, level='L3b',
                                   suite=suite, sensor_code=sensor_code,
                                   composite='DAY')
                if file:
                    file_list.append(file[0])
            filename = filename_builder(level='L3b', full_path=True,
                                        data_root=data_root, date=min(date_list),
                                        sensor_code=sensor_code, suite=suite,
                                        composite=composite)
            try:
                out_file = l3bin(file_list=file_list, north=north, south=south, west=west,
                                 east=east, filename=filename, overwrite=overwrite)
                out_list.append(out_file)
            except Exception as e:
                pprint('l3bin: %s could not be produced. %s' % (filename, e))
    return out_list

def l3bin_map_wrapper(date_list, sensor_codes, var_list, south, north, west, east,
                      composite, data_root, mapping_resolution=1000, night=False,
                      proj=None, overwrite=False):
    """Run l3bin and l3mapgen for a list of dates, sensor_codes, and variables

    automatically retrieve suites that need to be processed from variables

    Args:
        sensor_codes (list): List of sensor codes to include (e.g.: ['A', 'T', 'V']
        date_list (list): List of dates
        var_list (list): List of variables to process
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        data_root (str): Root of the data archive
        composite (str): Composite type (8DAY, MON)
        resolution (int): MApping resolution in meters. Defaults to 1000
        night (bool): Is it night processing?
        overwrite (bool): Overwrite existing files?
    """
    dn = 'night' if night else 'day'
    # Get suite list from var_list
    suite_list = []
    for var in var_list:
        suite = L3_SUITE_FROM_VAR[dn][var]
        suite_list.append(suite)
    # Reduce list to unique suite values
    suite_list = list(set(suite_list))
    # Run l3bin_wrapper on these parameters
    l3b_file_list = l3bin_wrapper(sensor_codes=sensor_codes, date_list=date_list,
                                  suite_list=suite_list, south=south, north=north,
                                  west=west, east=east, composite=composite,
                                  data_root=data_root, overwrite=overwrite)
    # identify input file
    if not l3b_file_list:
        # Exit in case no L3b temporal composite files were produced
        return
    for sensor_code in sensor_codes:
        file_list = [x for x in l3b_file_list if filename_parser(x)['sensor_code'] == sensor_code]
        if file_list:
            for var in var_list:
                suite = L3_SUITE_FROM_VAR[dn][var]
                file = [x for x in file_list if filename_parser(x)['suite'] == suite]
                if file:
                    try:
                        l3mapgen(file[0], variable=var, south=south, north=north,
                                 west=west, east=east, resolution=mapping_resolution, proj=proj,
                                 data_root=data_root, composite=composite, overwrite=overwrite)
                    except Exception as e:
                        pprint('Error while running l3mapgen on %s, %s composite. %s' % (var, composite, e))


def l3bin_map_batcher(begin, end, delta, sensor_codes, var_list, south, north,
                      west, east, composite, data_root, mapping_resolution=1000,
                      night=False, proj=None, overwrite=False, n_threads=1):
    """Takes a begin date, an end date and a compositing period to batch process temporal composites

    Uses the l3bin and l3mapgen seadas utilities and support parallel processing

    Args:
        begin (datetime.datetime or str): Begin date of the first composite
        end (datetime.datetime or str): Begin date of the last composite
        delta (int or str): composite length in days if int, 'month' if str.
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    dateList_list = pre_compose(begin, end, delta)
    kwargs = {'sensor_codes': sensor_codes,
              'var_list': var_list,
              'south': south,
              'north': north,
              'west': west,
              'east': east,
              'composite': composite,
              'data_root': data_root,
              'mapping_resolution': mapping_resolution,
              'night': night,
              'proj': proj,
              'overwrite': overwrite}
    # Run wrapper for every date with // support
    pool = mp.Pool(n_threads)
    pool.map_async(functools.partial(l3bin_map_wrapper, **kwargs), dateList_list).get(9999999)


def subscriptions_download(sub_list, data_root, refined=False):
    """Update a local archive using a list of data subscription numbers

    Args:
        sub_list (list of int): List of subscription numbers
        data_root (str): Root of the data archive
        refined (bool): Do the subscriptions refer to refined processing data (defaults
            to True), in which case the function will compare file size between the
            local and remote archives before deciding or not to download the file.

    Returns:
        list: A list of file paths corresponding to the local paths of downloaded files

    Examples:
        >>> import satmo
        >>> satmo.subscriptions_download([1821, 1823], data_root='/export/isilon/datos2/satmo2_data',
                                         refined=False)

        >>> from satmo.global_variables import SUBSCRIPTIONS
        >>> satmo.subscriptions_download(SUBSCRIPTIONS['L1A']['day'],
                                         data_root='/export/isilon/datos2/satmo2_data',
                                         refined=False)
    """
    try:
        # Send requests for each list element using a list comprehension
        url_list_list = [get_subscription_urls(x) for x in sub_list]
        # Flatten list (becuase it would be a list of lists)
        url_list = [item for sublist in url_list_list for item in sublist]
        # Run download_robust for each element of the list (for loop)
        dl_list = []
        for url in url_list:
            dl_list.append(download_robust(url, base_dir=data_root,
                            check_integrity=refined))
        # Filter dl_list
        dl_list = [x for x in dl_list if x is not None]
        return dl_list
    except Exception as e:
        pprint('There was a problem on %s with download. %s' % (datetime.now().strftime('%d %h at %H:%M'), e))
        return []

def nrt_wrapper(day_or_night, pp_type, var_list, north, south, west, east,
                data_root, binning_resolution = 1, mapping_resolution = 1000,
                eight_day=False, month=False, flags=None, proj=None):
    """Main wrapper to be called from CLI for NRT operation of the system

    Args:
        day_or_night (str): 'day' or 'night'
        pp_type (str): 'nrt' (for near real time) or 'refined' (for refined processing
        var_list (list): list of variables to process after data download (e.g. ['chlor_a', 'sst'])
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        data_root (str): Root of the data archive
        binning_resolution (int or str): See resolve argument in l2bin doc
        mapping_resolution (int): Resolution of the output L3m file in meters
        flags (list): A list of flags to mask invalid data (e.g. ['CLDICE', 'LAND', 'HIGLINT'])
            If None (default), a default list of flag for the L3 suite is fetched from
            the global variable FLAGS. When processing several variables belonging to
            different suites, it is not recommended to set a fixed list of flags, since they
            normally differ between suites.
        proj (str): Optional proj4 string. If None (default), a longlat is used
        eight_day (bool): Generate 8 days temporal composites (defaults to False)
        month (bool): Generate monthly temporal composites (defaults to False)

    Returns:
        The function is used for it's side effects of downloading data, and processing
            associated variables

    Examples:
        >>> # The idea is to call this wrapper several time within a scheduler
        >>> import satmo

        >>> satmo.nrt_wrapper(day_or_night='day', pp_type='nrt', var_list=['chlor_a', 'sst', 'nflh', 'Kd_490'],
                              north=33, south=3, west=-122, east=-72,
                              data_root='/export/isilon/datos2/satmo2_data/',
                              eight_day=True)    
    """
    # Run subscription download on one type of subscription
    if pp_type == 'refined':
        refined = True
    elif pp_type == 'nrt':
        refined = False
    else:
        raise ValueError('Unknown pp_type. Must be \'nrt\' or \'refined\'')
    # Make night day string variable
    if day_or_night == 'day':
        day = True
    elif day_or_night == 'night':
        day = False
    else:
        raise ValueError('day_or_night must be one of \'day\' or \'night\'')
    # Define day_var and night vars (legacy from previous version of the function)
    if day:
        day_vars = var_list
        night_vars = None
    else:
        day_vars = None
        night_vars = var_list
    # List of subscriptions for download
    sub_list = SUBSCRIPTIONS['L2'][pp_type][day_or_night]
    # Query subscriptions and download corresponding data (update local data archive) 
    try:
        dl_list = subscriptions_download(sub_list, data_root, refined)
        date_list = get_date_list(dl_list)
    except Exception as e:
        # Exit function if the download did not work because there would be nothing
        # to do anyway
        pprint('Data download did not work properly. %s' % e)
        return
    # Check that something got downloaded
    if not dl_list:
        # Exit function in case no files were downloaded
        return
    # Generate l2m files for each file and each variable (in an error catcher so that when it
    # attempts to produce a chlor_a l2m file from a SST L2 it gets ignored)
    for var in var_list:
        for f in dl_list:
            try:
                suite = L3_SUITE_FROM_VAR[day_or_night][var]
                l2mapgen(f, south=south, north=north, west=west, east=east,
                         prod=var, flags=FLAGS[suite], data_root=data_root, overwrite=True)
            except Exception as e:
                pprint('L2m file not generated for %s, variable %s. %s' % (f, var, e))
    date_list = get_date_list(dl_list)
    for dt in date_list:
        bin_map_wrapper(date=dt, sensor_codes=['A', 'T', 'V'], north=north,
                        south=south, west=west, east=east, data_root=data_root,
                        binning_resolution=binning_resolution,
                        mapping_resolution=mapping_resolution, day_vars=day_vars,
                        night_vars=night_vars, flags=flags, proj=proj, overwrite=True)
    if eight_day:
        # Might re-run several times the same composite, but this is not so computationally
        # expensive
        for dt in date_list:
            input_dates = find_composite_date_list(dt, 8)
            l3bin_map_wrapper(date_list=input_dates, sensor_codes=['A', 'T', 'V'],
                              var_list=var_list, south=south, north=north, west=west,
                              east=east, composite='8DAY', data_root=data_root,
                              mapping_resolution=mapping_resolution, night=not(day),
                              proj=proj, overwrite=True)

    if month:
            input_dates = find_composite_date_list(dt, 'month')
            l3bin_map_wrapper(date_list=input_dates, sensor_codes=['A', 'T', 'V'],
                              var_list=var_list, south=south, north=north, west=west,
                              east=east, composite='MO', data_root=data_root,
                              mapping_resolution=mapping_resolution, night=not(day),
                              proj=proj, overwrite=True)

def _l2gen_safe(x, suite, data_root, night, get_anc):
    """Custom function for l2gen that allows calling it in parallel on a list of L1A files
    """
    dn = 'night' if night else 'day'
    sensor = filename_parser(x)['sensor']
    var_list = VARS_FROM_L2_SUITE[sensor][dn][suite]
    try:
        out = l2gen(x=x, var_list=var_list, suite=suite, data_root=data_root,
                    get_anc=get_anc)
        return out
    except Exception as e:
        pprint('error running l2gen on %s. %s' % (x, e))

def nrt_wrapper_l1(north, south, west, east, var_list, data_root, n_threads=1):
    """Wrapper to be called from nrt command line once a day

    Handles subscription based download of L1A files, L2 processing, computation
    of additional indices, and mapping of each individual file, separately to
    longlat.

    Args:
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        var_list (list): List of additional variables to generate using l2_append
        data_root (str): Root of the data archive
        n_threads (int): Number of threads to use for running l2gen in parallel

    Returns:
        The function is used for its side effect of running the L1A-download
        to L2m processing chain

    """
    # 1 - Download data
    try:
        file_list = subscriptions_download(SUBSCRIPTIONS['L1A']['day'],
                                           data_root=data_root, refined=False)
    except Exception as e:
        # Exit function if the download did not work because there would be nothing
        # to do anyway
        pprint('Data download did not work properly. %s' % e)
        return
    # Check that something got downloaded
    if not file_list:
        # Exit function in case no files were downloaded
        return
    # Process every L1A file to L2 with error catching
    L2_list = []
    # Remove Geo files from file_list
    file_list = [x for x in file_list if filename_parser(x)['level'] != 'GEO']
    kwargs = {'suite': 'OC2',
              'data_root': data_root,
              'night': False,
              'get_anc': True}
    # Run wrapper for every L1a file with // support
    pool = mp.Pool(n_threads)
    L2_list = pool.map_async(functools.partial(_l2gen_safe, **kwargs),
                             file_list).get(9999999)
    # Clean list (may contain Nones where l2gen failed)
    L2_list = [x for x in L2_list if x is not None]
    # For each L2 file, append AFAI to netCDF file
    for L2_file in L2_list:
        sensor = filename_parser(L2_file)['sensor']
        for var in var_list:
            try:
                param = BAND_MATH_FUNCTIONS[var][sensor]
                suite = L3_SUITE_FROM_VAR['day'][var]
                l2_append(L2_file, **param)
                l2mapgen(L2_file, south=south, north=north, west=west, east=east,
                         prod=var, flags=FLAGS[suite], data_root=data_root)
            except Exception as e:
                pprint('Problem while generating L2m file from %s. %s' % (L2_file, e))

def refined_processing_wrapper_l1(north, south, west, east, var_list, data_root,
                                  delay = 30):
    """Wrapper to be called from nrt command line once a day

    Reprocesses L2 OC2 suite a month after initial processing for improved
    atmospheric correction

    Args:
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        data_root (str): Root of the data archive
        delay (int): Delay in number of days between data acquisition and refined
            processing. Defaults to 30.

    Returns:
        The function is used for its side effect of running l2gen on 1 month
        old L1A data
    """
    today = datetime.today()
    last_month = today - timedelta(delay)

    L2_list = l2gen_wrapper(last_month, sensor_codes=['A', 'T', 'V'], var_list=['rhos_nnn'],
                            suite='OC2', data_root=data_root)

    for L2_file in L2_list:
        sensor = filename_parser(L2_file)['sensor']
        for var in var_list:
            try:
                param = BAND_MATH_FUNCTIONS[var][sensor]
                suite = L3_SUITE_FROM_VAR['day'][var]
                l2_append(L2_file, **afai_param)
                l2mapgen(L2_file, south=south, north=north, west=west, east=east,
                         prod=var, flags=FLAGS[suite], data_root=data_root)
            except Exception as e:
                pprint('Problem while generating L2m file from %s. %s' % (L2_file, e))
