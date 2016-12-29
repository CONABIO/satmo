from datetime import datetime, timedelta
import itertools
from .query import query_from_extent, make_download_url
from .download import download_robust
from .utils import file_path_from_sensor_date
import warnings
from pprint import pprint


def timerange_download(sensors, begin, end, write_dir,\
                north, south, west, east, day = True, night = True,\
                overwrite = False, check_integrity = False):
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
            file_list = query_from_extent(sensors, item, 'DAY', north, south, west, east, day = day, night = night)
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
def extract_wrapper(input_dir, north, south, west, east, compress, clean, pattern,\
                    overwrite = False, keep_uncompressed = False):
    pass

def timerange_extract(sensors, data_root, begin, end,\
                      north, south, west, east,\
                      overwrite = False, compress = True, clean = True,\
                      n_threads = 1):
    """Extract spatial extent for a given time range

    Wrapper around satmo.extractJob class
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

