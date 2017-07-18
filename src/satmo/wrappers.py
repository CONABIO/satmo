from datetime import datetime, timedelta
import itertools
import multiprocessing as mp
import functools
import os
from pprint import pprint
import warnings

from .query import query_from_extent, make_download_url, get_subscription_urls
from .download import download_robust
from .utils import (file_path_from_sensor_date, OC_file_finder, is_day,
                    is_night, resolution_to_km_str, OC_filename_builder,
                    OC_filename_parser, pre_compose, processing_meta_from_list,
                    find_composite_date_list)
from .preprocessors import extractJob, OC_l2bin, OC_l3mapgen

from .global_variables import (L2_L3_SUITES_CORRESPONDENCES, SUBSCRIPTIONS, L3_SUITE_FROM_VAR,
                               BIT_MASK_FROM_L3_SUITE)
from .processors import L3mProcess, FileComposer, make_time_composite
from .visualization import make_preview

def timerange_download(sensors, begin, end, write_dir,\
                north, south, west, east, day = True, night = True,\
                product = 'L1A', overwrite = False, check_integrity = False):
    """Queries and download data for a given timerange

    Wrapper around downdload and query

    Args:
        sensors: (list) list of strings, Valid entries are 'am' (aqua), 'tm' (terra),
        'sw' (seawifs), 'v0' (viirs)
        begin (datetime or str): Begining of time range. 'yyyy-mm-dd' if str
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
        list of boolean
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
        for url in url_list:
            local_file = download_robust(url, write_dir, overwrite = overwrite, check_integrity = check_integrity)
            local_files_list.append(local_file)
    return local_files_list

    # test = satmo.timerange_download(['tm'], '2005-01-01', '2005-01-06', '/home/loic/sandbox/dl_tests', north = 33, south = 10, west = -133, east = -110)
def extract_wrapper(input_dir, north, south, west, east, compress = True, clean = True, init_kwargs = {},\
                    extract_kwargs = {}, compress_kwargs = {}, clean_kwargs = {}):
    """Wrapper for performing spatial extraction on L1A data

    Performs data unpacking (implicit), extraction, repacking (optional), and cleaning of
    junk files.

    Args:
        input_dir (str): path of directory that contains the data
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        compress (bool): Should data be recompressed after extraction, defaults to True
        clean (bool): Should intermediary output be deleted from directory,
        defaults to True. If compress is set to False, and clean is set to True,
        you should probably put sonething in the clean_kwargs argument
        init_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob class instantation
        'pattern' is the only one at the moment
        extract_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob.extract()
        method. 'overwrite' is the only one at the moment
        compress_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob.compress()
        method. 'overwrite' is the only one at the moment
        clean_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob.clean()
        method. 'keep_uncompressed' is the only one at the moment

    Return:
        A dict with 'input_dir' as key and status as value (0 for successful, 1 if crash
        or directory did not exist)
    """
    if os.path.isdir(input_dir):
        try:
            ext = extractJob(input_dir, **init_kwargs)
            ext.extract(north=north, south=south, west=west, east=east, **extract_kwargs)
            if compress:
                ext.compress(**compress_kwargs)
            if clean:
                ext.clean(**clean_kwargs)
            return {input_dir: 0}
        except Exception as e:
            pprint(e)
            return {input_dir: 1}
    else:
        return {input_dir: 1}


def timerange_extract(sensors, data_root, begin, end,\
                      north, south, west, east,\
                      compress = True, clean = True,\
                      init_kwargs = {}, extract_kwargs = {}, compress_kwargs = {}, clean_kwargs = {},\
                      n_threads = 1):
    """Extract spatial extent for a given time range

    Parallel batcher for satmo.extract_wrapper()

    Args:
        sensors (list): List of sensor names for which data should be extracted
            e.g. ['aqua', 'terra']
        data_root (str): Root of the system local archive
        begin (datetime or str): Begining of time range. 'yyyy-mm-dd' if str
        end (datetime or str): End of time range. 'yyyy-mm-dd' if str
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        compress (bool): Should data be recompressed after extraction, defaults to True
        clean (bool): Should intermediary output be deleted from directory,
            defaults to True. If compress is set to False, and clean is set to True,
            you should probably put sonething in the clean_kwargs argument
        init_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob class instantation
            'pattern' is the only one at the moment
        extract_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob.extract()
            method. 'overwrite' is the only one at the moment
        compress_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob.compress()
            method. 'overwrite' is the only one at the moment
        clean_kwargs (dict): dictionary of arguments passed as **kwargs to the extractJob.clean()
            method. 'keep_uncompressed' is the only one at the moment
        n_treads (int): Number of threads to use for the parallel implementation

    Returns:
        List of dicts returned by satmo.extract_wrapper()
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    ndays = (end - begin).days + 1
    date_range = [begin + timedelta(days=x) for x in range(0, ndays)]
    ## Make a list of all combinations to pass as args in list comprehension
    sensor_date_combo = list(itertools.product(sensors, date_range))
    dir_list = [file_path_from_sensor_date(*x, data_root = data_root) for x in sensor_date_combo]
    kwargs = {'north': north,
              'south': south,
              'west': west,
              'east': east,
              'compress': compress,
              'clean': clean,
              'init_kwargs': init_kwargs,
              'extract_kwargs': extract_kwargs,
              'compress_kwargs': compress_kwargs,
              'clean_kwargs': clean_kwargs}
    pool = mp.Pool(n_threads)
    out = pool.map(functools.partial(extract_wrapper, **kwargs), dir_list)
    return out


def l2_to_l3m_wrapper(date, sensor_code, suite, variable, south, north, west, east, data_root, night = False,
                      binning_resolution = 1, mapping_resolution = '1000m', projection = None, use_existing = True, overwrite = False):
    """Process from L2 to L3m for a given date and sensor using seadas (l2bin +
        l3mapgen)

    Args:
        date (str or datetime): Date to be processed
        sensor_code (str): Sensor code of the data to be processed (e.g. 'A' for aqua)
        suite (str): L3m suite to obtain (e.g. 'CHL')
        variable (str): L3m variable to process (e.g. 'chlor_a')
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        data_root (str): Root of the data archive
        night (bool): Is this night data or not. Defaults to False
        binning_resolution (int or str): See resolve argument in l2bin doc. Defaults to 1
        mapping_resolution (str): MApping resolution in the form of e.g.'1000m'. Defaults to '1000m'
        projection (str): Optional proj4 string. If None (default), a lambert Azimutal Equal Area projection (laea), centered
            on the provided extent is used.
        use_existing (bool): Use L3b file if already exist? Defaults to True
        overwrite (bool): Overwrite existing L3m file. Defaults to False

    Raises:
        IOError: When no input files can be found for the provided date - sensor - day/night combination

    Returns:
        str: The filename of the L3m file produced
    """
    # list files 
    L2_suite = L2_L3_SUITES_CORRESPONDENCES[suite]
    L2_file_list = OC_file_finder(data_root = data_root, date = date, level = 'L2', suite = L2_suite, sensor_code = sensor_code)
    L2_file_list = [x for x in L2_file_list if is_night(x) == night]
    if len(L2_file_list) == 0:
        raise IOError('No L2 files found')
    L3b_filename = OC_l2bin(file_list = L2_file_list, L3b_suite = suite, resolution = binning_resolution, night = night,
                            data_root = data_root, overwrite = not(use_existing))
    L3m_filename = OC_l3mapgen(ifile = L3b_filename, variable = variable, south = south, north = north, west = west, east = east,
                            resolution = mapping_resolution, projection = projection, data_root = data_root, overwrite = overwrite)
    return L3m_filename


def timerange_l2_to_l3m(sensors, suite, variable, data_root, begin, end, south, north, west, east, night = False, **kwargs):
    """Processes L3m data from L2 for a given list of dates and a list of
        sensor codes using seadas (l2bin + l3mapgen)

    Args:
        sensors (list): List of sensor codes to process (e.g.: ['A', 'T', 'V'])
        suite (str): L3m suite to obtain (e.g. 'CHL')
        variable (str): L3m variable to process (e.g. 'chlor_a')
        data_root (str): Root of the data archive
        begin (datetime or str): Begining of time range. 'yyyy-mm-dd' if str
        end (datetime or str): End of time range. 'yyyy-mm-dd' if str
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        night (bool): Is this night data or not. Defaults to False
        **kwargs: Additional arguments passed to l2_to_l3m_wrapper()

    Returns:
        This function is used for its side effects of batch processing ocean color data
        to level L3m; it doesn't return anything
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    ndays = (end - begin).days + 1
    date_range = [begin + timedelta(days=x) for x in range(0, ndays)]
    for day in date_range:
        for sensor in sensors:
            try:
                l2_to_l3m_wrapper(date = day, sensor_code = sensor, suite = suite, variable = variable,
                                  south = south, north = north, west = west, east = east, data_root = data_root, night = night, **kwargs)
            except IOError as e:
                pprint('date %s, sensor %s could not be processed, raison: %s' % (str(day), str(sensor), str(e)))
                pass
            except Exception as e:
                pprint('date %s, sensor %s could not be processed, raison: %s' % (str(day), str(sensor), str(e)))
                pass
            except KeyboardInterrupt:
                raise



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
            'all'
        fun (str): Compositing function. Can be 'mean', 'median', 'min', 'max'.
            Defaults to 'mean'
        filename (str): Optional output filename. Defaults to None, in which
            case the filename is automatically generated.
        preview (bool): Generate a png preview. Defaults to True
        overwrite (bool): Overwrite existing L3m file. Defaults to False

    Return:
        The filename of the created composite.

    Example:
        >>> import satmo

        >>> satmo.make_daily_composite(date='2016-01-01', variable='chlor_a', suite='CHL',
                                       resolution='2km',
                                       data_root='/home/ldutrieux/sandbox/satmo2_data',
                                       overwrite=True, fun='mean', sensor_codes=['A', 'V'])

    """
    # Search the files that correspond to a date/variable, etc Do not restrict
    # sensor code
    file_list = OC_file_finder(data_root=data_root, date=date, level='L3m',
                               suite=suite, variable=variable,
                               resolution=resolution, composite='DAY',
                               sensor_code=None)
    # Filter in case only a subset of the sensors is asked
    if sensor_codes != 'all':
        file_list = [x for x in file_list if OC_filename_parser(x)['sensor_code'] in sensor_codes]
    # Given a date (string or datetime), a variable (e.g. chlor_a) and a list of sensors, make 
    compositing_class = FileComposer(*file_list)
    # Run the compositing method using string provided in fun= argument
    func = getattr(compositing_class, fun)
    func()
    # Generate filename if not provided
    if filename is None:
        filename = OC_filename_builder(level='L3m', full_path=True,
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
    except KeyboardInterrupt:
        raise


def timerange_daily_composite(begin, end, variable, suite, data_root,
                              resolution, sensor_codes='all', fun='mean',
                              preview=True, overwrite=False, n_threads=1):
    """Produce daily composite for individual dates in a time-range in batch

    Args:
        begin (datetime or str): Begining of time range. 'yyyy-mm-dd' if str
        end (datetime or str): End of time range. 'yyyy-mm-dd' if str
        n_threads (int): Number of threads to use for running the
            make_daily_composite function in parallel.
        others (*): See help of make_daily_composite for the other parameters.

    Example:
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

def auto_L3m_process(date, sensor_code, suite, var, north, south, west, east,
                     data_root, resolution, day=True, bit_mask = 0x0669D73B, proj4string=None, overwrite=False,
                     fun=None, band_list=None, preview=True):
    """Wrapper to easily run generate L3m files (implicitely from L2)

    Details:
        The function generates a L3m file for a given variable in tif format
            from a list of L2 files. The variable can be either an existing
            layer in the input L2 files, or can be calculated given a formula
            (fun=) and a list of reflectance bands (band_list=). File names are
            automatically generated and a png preview is optionally produced as
            well.

    Args:
        date (str or datetime): Date to be processed
        sensor_code (str): Sensor code of the data to be processed (e.g. 'A' for aqua)
        suite (str): L3m suite to obtain (e.g. 'CHL')
        var (str): L3m variable to process (e.g. 'chlor_a'). if a fun= and
            band_list= arguments are not provided, the variable must already exist
            in the input L2 files
        bit_mask (int): The mask to use for selecting active flags from the flag array
            See the help of apply_mask for further details
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        data_root (str): Root of the data archive
        day (bool): Is this day data or not. Defaults to True
        resolution (int): Outout resolution in the unit of the output
            coordinate reference system.
        proj4string (str): Optional proj4 string. If None (default), a lambert Azimutal Equal Area projection (laea), centered
            on the provided extent is used. Note that non metric projections
            are likely to cause problems with the automatic output file naming.
        overwrite (bool): Overwrite existing L3m file. Defaults to False
        preview (bool): Generate a png preview. Defaults to True

    Example:
        >>> import satmo

        >>> filename = satmo.auto_L3m_process(date='2016-01-10', sensor_code='A', suite='CHL',
                                              var='chlor_a', north=33, south=3, west=-122, east=-72,
                                              overwrite=True, resolution=2000,
                                              data_root='/home/ldutrieux/sandbox/satmo2_data')

    Return:
        The filename of the produced file.
    """
    # Build proj4string if not provided
    if proj4string is None:
        lat_0 = (south + north) / 2.0
        lon_0 = (east + west) / 2.0
        proj4string = '+proj=laea +lat_0=%.1f +lon_0=%.1f' % (lat_0, lon_0)

    # Generate output filename 
    resolution_str = resolution_to_km_str(resolution)
    filename = OC_filename_builder(level='L3m', full_path=True, nc=False,
                                   data_root=data_root, date=date,
                                   sensor_code=sensor_code, suite=suite,
                                   variable=var, composite='DAY',
                                   resolution=resolution_str)
    # Process the data (only if file does not yet exist, unless overwrite set
    # to True
    if not (os.path.isfile(filename) and not overwrite):
        # Instantiate L3mProcessing class
        if fun is None or band_list is None:
            # The var exists in the L2 files
            bin_class = L3mProcess.from_sensor_date(sensor_code=sensor_code,
                                                    date=date, day=day,
                                                    suite=L2_L3_SUITES_CORRESPONDENCES[suite],
                                                    data_root=data_root,
                                                    var=var)
        else:
            bin_class = L3mProcess.from_sensor_date(sensor_code=sensor_code,
                                                    date=date, day=day,
                                                    suite=L2_L3_SUITES_CORRESPONDENCES[suite],
                                                    data_root=data_root)
            bin_class.calc(band_list=band_list, fun=fun)

        bin_class.apply_mask(bit_mask)
        bin_class.bin_to_grid(south=south, north=north, west=west, east=east,
                              resolution=resolution, proj4string=proj4string)
        # Create directory if not already exists
        L3m_dir = os.path.dirname(filename)
        if not os.path.exists(L3m_dir):
            os.makedirs(L3m_dir)
        # Write grid to file
        bin_class.to_file(filename)
        if preview:
            make_preview(filename)

    return filename


def auto_L3m_process_with_error_catcher(date, sensor_code, suite, var, north, south, west, east,
                                        data_root, resolution, day=True, bit_mask = 0x0669D73B, proj4string=None, overwrite=False,
                                        fun=None, band_list=None, preview=True):
    try:
        auto_L3m_process(date=date, sensor_code=sensor_code, suite=suite,
                         var=var, north=north, south=south, west=west,
                         east=east, data_root=data_root, resolution=resolution,
                         day=day, bit_mask=bit_mask, proj4string=proj4string,
                         overwrite=overwrite, fun=fun, band_list=band_list,
                         preview=preview)
    except IOError as e:
        pprint('date %s, sensor %s could not be processed, reason: %s' %
               (str(date), str(sensor_code), str(e)))
    except Exception as e:
        pprint('date %s, sensor %s could not be processed, reason: %s' %
               (str(date), str(sensor_code), str(e)))
    except KeyboardInterrupt:
        raise

def timerange_auto_L3m_process(begin, end, sensor_codes, suite, var, north, south, west, east,
                               data_root, resolution, day=True, bit_mask =
                               0x0669D73B, proj4string=None, overwrite=False,
                               fun=None, band_list=None, preview=True,
                               n_threads=1):
    """Wrapper with parallel support for batch processing of L3m files

    Args:
        begin (datetime or str): Begining of time range. 'yyyy-mm-dd' if str
        end (datetime or str): End of time range. 'yyyy-mm-dd' if str
        sensor_codes (list): list of strings with sensor codes (e.g.: ['A',
            'T'])
        n_threads (int): Number of threads to use for running the
            auto_L3m_process function in parallel.
        others (*): See help of auto_L3m_process for the other parameters.

    Return:
        This function does not return anything

    Example:
        >>> import satmo

        >>> satmo.timerange_auto_L3m_process(begin='2001-01-01',
                                             end='2017-12-31',
                                             sensor_codes=['V', 'T', 'A'],
                                             suite='CHL', var='chlor_a',
                                             north=33, south=3, west=-122,
                                             east=-72,
                                             data_root='/home/ldutrieux/sandbox/satmo2_data',
                                             resolution=2000)

        >>> # Second example with calculation of new variable from Rrs layers
        >>> import satmo
        >>> import numpy as np

        >>> def add_bands(x, y):
        >>>     return np.add(x, y)

        >>> satmo.timerange_auto_L3m_process(begin='2016-01-01',
                                             end='2016-01-16',
                                             sensor_codes=['A', 'T'],
                                             suite='RRS', var='rrs_add',
                                             north=33, south=3, west=-122,
                                             east=-72,
                                             data_root='/home/ldutrieux/sandbox/satmo2_data',
                                             resolution=2000,
                                             n_threads=3, overwrite=True, fun=add_bands,
                                             band_list=['Rrs_555', 'Rrs_645'])
    """
    warnings.filterwarnings("ignore")
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    ndays = (end - begin).days + 1
    date_range = [begin + timedelta(days=x) for x in range(0, ndays)]
    # Loop over each sensor and implement the mnultiprocessing there
    for sensor_code in sensor_codes:

        kwargs = {'sensor_code': sensor_code,
                  'suite': suite,
                  'var': var,
                  'north': north,
                  'south': south,
                  'west': west,
                  'east': east,
                  'data_root': data_root,
                  'resolution': resolution,
                  'day': day,
                  'bit_mask': bit_mask,
                  'proj4string': proj4string,
                  'overwrite': overwrite,
                  'fun': fun,
                  'band_list': band_list,
                  'preview': preview}
        pool = mp.Pool(n_threads)
        # Use of map_async().get(9999999) enables KeyboardInterrupt to work
        pool.map_async(functools.partial(auto_L3m_process_with_error_catcher,
                                         **kwargs), date_range).get(9999999)


def timerange_time_compositer(begin, end, delta, var, suite, resolution,
                              composite, data_root, sensor_code='X', fun='mean',
                              overwrite=False, preview=True, n_threads=1):
    """Runs make_time_composite in batch and parallel

    Args:
        begin (datetime.datetime or str): Begin date of the first composite
        end (datetime.datetime or str): Begin date of the last composite
        delta (int or str): composite length in days if int, 'month' if str.
        var (str): L3m variable to composite
        suite (str): L3m suite to compose
        resolution (str): Resolution of data to compose (e.g.: '2km')
        composite (str): Type/name of generated composite (e.g.: '8DAY', '16DAY'). Used
            for automatic output filename generation.
        data_root (str): Root of the data archive
        sensor_code (str): Sensor to composite (defaults to 'X', which
            corresponds to daily (cross sensors) composites.
        fun (str): compositing function, defaults to mean
        overwrite (bool): Should output file be overwritten if it already
            exists.
        preview (bool): Should a png preview be automatically generated
        n_threads (int): Number of threads to use for running the
            auto_L3m_process function in parallel.

    Return:
        Used for its side effect of running make_time_composite in batch; does not
            return anything

    Example:
        >>> import satmo
        >>> # Create 16 days mean value composites of chlor_a
        >>> satmo.timerange_time_compositer('2000-01-01', '2004-12-31', 16, 'chlor_a',
                                            suite='CHL', resolution='2km', composite='16DAY',
                                            data_root='/home/ldutrieux/sandbox/satmo2_data/',
                                            overwrite=True, n_threads=2)
    """
    if type(begin) is str:
        begin = datetime.strptime(begin, "%Y-%m-%d")
    if type(end) is str:
        end = datetime.strptime(end, "%Y-%m-%d")
    dateList_list = pre_compose(begin, end, delta)
    # Define kwargs (arguments passed to make_time_composite other than date_list
    kwargs = {'var': var,
              'suite': suite,
              'resolution': resolution,
              'composite': composite,
              'data_root': data_root,
              'sensor_code': sensor_code,
              'fun': fun,
              'filename': None,
              'overwrite': overwrite,
              'preview': preview}
    pool = mp.Pool(n_threads)
    # Use of map_async().get(9999999) enables KeyboardInterrupt to work
    pool.map_async(functools.partial(make_time_composite,
                                     **kwargs), dateList_list).get(9999999)

def subscriptions_download(sub_list, data_root, refined=False):
    """Update a local archive using a list of data subscription numbers

    Args:
        sub_list (list of int): List of subscription numbers
        data_root (str): Root of the data archive
        efined (bool): Do the subscriptions refer to refined processing data (defaults
            to True), in which case the function will compare file size between the
            local and remote archives before deciding or not to download the file.

    Return:
        TODO: would be good to return a list of the files that did get downloaded

    Example:
        >>> import satmo
        >>> satmo.subscriptions_download([1821, 1823], base_dir='/export/isilon/datos2/satmo2_data',
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
    except KeyboardInterrupt:
        raise

def nrt_wrapper(day_or_night, pp_type, var_list, north, south, west, east,
                data_root, resolution, preview=False, daily_compose=False,
                eight_day=False, sixteen_day=False, month=False,
                compositing_function='mean'):
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
        resolution (int): Outout resolution in the unit of the output
            coordinate reference system.
        preview (bool): Generate a png previews. Defaults to False
        daily_compose (bool): Generate daily composites (defaults to False)
        eight_day (bool): Generate 8 days temporal composites (defaults to False)
        sixteen_day (bool): Generate 16 days temporal composites (defaults to False)
        month (bool): Generate monthly temporal composites (defaults to False)
        compositing_function (str): Function to be used to generate coposites
            (temporal and daily composites). Can be 'mean' (default), 'median',
            'min', or 'max'

    Return:
        The function is used for it's side effects of downloading data, and processing
            associated variables

    Example:
        >>> # The idea is to call this wrapper several time within a scheduler
        >>> import satmo

        >>> satmo.nrt_wrapper(day_or_night='day', pp_type='nrt', var_list=['chlor_a', 'sst', 'nflh', 'Kd_490'],
                              north=33, south=3, west=-122, east=-72, resolution=2000, preview=False,
                              data_root='/export/isilon/datos2/satmo2_data/', daily_compose=True,
                              eight_day=True, sixteen_day=True, compositing_function='mean')

    Details:
        How to adapt this function?
            - To add/remove subscriptions, simply edit the global variable SUBSCRIPTIONS
            - To add new variables you probably have to edit the global variables L3_SUITE_FROM_VAR and
                BIT_MASK_FROM_L3_SUITE (if the variable belongs to a suite that is not referenced in these variables)
            - Adding a new temporal composite means adding the corresponding argument, and following
                the logic of the eight_day and sixteen_day cases (already implemented)
            - Every change that involves changing the function argument should be passed to the CLI
                (satmo_nrt.py)
    """
    # Argument coherence check
    if (eight_day or sixteen_day or month) and not daily_compose:
        raise ValueError('temporal composites are generated from daily composites, so that daily_compose must be set to True for if eight_day, sixteen_day or month are used.')
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
    # Build resolution string, to be used for compositing functions
    resolution_str = resolution_to_km_str(resolution)
    sub_list = SUBSCRIPTIONS['L2'][pp_type][day_or_night]
    # Query subscriptions and download corresponding data (update local data archive) 
    try:
        dl_list = subscriptions_download(sub_list, data_root, refined)
    except Exception as e:
        # Exit function if the download did not work because there would be nothing
        # to do anyway
        pprint('Data download did not work properly. %s' % e)
        return
    except KeyboardInterrupt:
        raise
    # Check that something got downloaded
    if not dl_list:
        # Exit function in case no files were downloaded
        return
    dict_list = processing_meta_from_list(dl_list)
    for item in dict_list:
        # Compare list of potential variable with the list of variables supplied
        vars_to_process = list(set(var_list).intersection(item['products']))
        for var in vars_to_process:
            try:
                suite = L3_SUITE_FROM_VAR[day_or_night][var]
                auto_L3m_process(date=item['date'], sensor_code=item['sensor_code'],
                                 suite=suite, var=var, north=north,
                                 south=south, west=west, east=east, data_root=data_root,
                                 resolution=resolution, day=day, bit_mask=BIT_MASK_FROM_L3_SUITE[suite],
                                 overwrite=True, preview=preview)
            except Exception as e:
                pprint('%s not processed for %s sensor. %s' % (var, item['sensor'], e))
            except KeyboardInterrupt:
                raise
    # Produce daily composites
    if daily_compose:
        # Get date_list from dict_list
        date_list = list(set([x['date'] for x in dict_list]))
        for fecha in date_list:
            for var in var_list:
                try:
                    suite = L3_SUITE_FROM_VAR[day_or_night][var]
                    make_daily_composite(date=fecha, variable=var, suite=suite,
                                         data_root=data_root, resolution=resolution_str,
                                         sensor_codes = 'all',
                                         fun=compositing_function, preview=preview,
                                         overwrite=True)
                except Exception as e:
                    pprint('%s daily composite not processed. %s' % (var, e))
                except KeyboardInterrupt:
                    raise
    # Produce 8DAY composites
    if eight_day:
        # Get date_list from dict_list
        date_list = list(set([x['date'] for x in dict_list]))
        for fecha in date_list:
            for var in var_list:
                try:
                    suite = L3_SUITE_FROM_VAR[day_or_night][var]
                    fecha_list = find_composite_date_list(fecha, 8)
                    make_time_composite(date_list=fecha_list, var=var, suite=suite,
                                       resolution=resolution_str, composite='8DAY',
                                       data_root=data_root, sensor_code='X', fun=compositing_function,
                                       overwrite=True, preview=preview)
                except Exception as e:
                    pprint('%s 8 day composite not processed. %s' % (var, e))
                except KeyboardInterrupt:
                    raise

    # Produce 16DAY composites
    if sixteen_day:
        # Get date_list from dict_list
        date_list = list(set([x['date'] for x in dict_list]))
        for fecha in date_list:
            for var in var_list:
                try:
                    suite = L3_SUITE_FROM_VAR[day_or_night][var]
                    fecha_list = find_composite_date_list(fecha, 16)
                    make_time_composite(date_list=fecha_list, var=var, suite=suite,
                                       resolution=resolution_str, composite='16DAY',
                                       data_root=data_root, sensor_code='X', fun=compositing_function,
                                       overwrite=True, preview=preview)
                except Exception as e:
                    pprint('%s 16 day composite not processed. %s' % (var, e))
                except KeyboardInterrupt:
                    raise

    # Produce monthly composites
    if month:
        # Get date_list from dict_list
        date_list = list(set([x['date'] for x in dict_list]))
        for fecha in date_list:
            for var in var_list:
                try:
                    suite = L3_SUITE_FROM_VAR[day_or_night][var]
                    fecha_list = find_composite_date_list(fecha, 'month')
                    make_time_composite(date_list=fecha_list, var=var, suite=suite,
                                       resolution=resolution_str, composite='MO',
                                       data_root=data_root, sensor_code='X', fun=compositing_function,
                                       overwrite=True, preview=preview)
                except Exception as e:
                    pprint('%s monthly composite not processed. %s' % (var, e))
                except KeyboardInterrupt:
                    raise

