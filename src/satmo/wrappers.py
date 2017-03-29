from datetime import datetime, timedelta
import itertools
import multiprocessing.dummy as mp
import functools
import os
from pprint import pprint
import warnings

from .query import query_from_extent, make_download_url
from .download import download_robust
from .utils import file_path_from_sensor_date, OC_file_finder, is_day, is_night
from .preprocessors import extractJob, OC_l2bin, OC_l3mapgen

from .global_variables import L2_L3_SUITES_CORRESPONDENCES

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


def make_daily_composite(date, variable, sensors = 'all', filename = None):
    # Given a date (string or datetime), a variable (e.g. chlor_a) and a list of sensors, make 
    pass

def l2_to_l3m_wrapper(date, sensor_code, suite, variable, south, north, west, east, data_root, night = False,
                      binning_resolution = 1, mapping_resolution = '1000m', projection = None, use_existing = True, overwrite = False):
    """Process from L2 to L3m for a given date and sensor

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