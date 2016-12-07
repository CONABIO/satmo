import re
import glob
from datetime import datetime, time
import os

from .global_variables import SENSOR_CODES

def parse_file_name(id):
    """Filename parser for modis, viirs, seawifs

    Identifies a typical sequence corresponding to a satelite data filename
    and parses it to return a dictonary with sensor, level, date, etc

    Args:
        id (string) string containing a Landsat scene ID

    Returns:
        dictionary: Dictionary containing information on sensor, date, level, etc
        year, month, doy, dom are integers
    """
    pattern = re.compile(r"([A-Z])(\d{7})(\d{4})?(?:\d{2})?\.([A-Za-z1-3\-]{2,5})_(?:[A-Z]{3,4})_?(?:[A-Z]{3})?.*")
    m = pattern.search(id)
    if m is None:
        raise ValueError('No valid data name found for %s' % id)
    dt_date = datetime.strptime(m.group(2), "%Y%j")
    if m.group(3) is not None:
        dt_time = datetime.strptime(m.group(3), "%H%M").time()
    else:
        dt_time = None
    id_meta = {'sensor': SENSOR_CODES[m.group(1)], #TODO: a KeyError will be thrown if a key is not in SENSOR_CODES, what to do with it
               'date': dt_date.date(),
               'time': dt_time,
               'year': dt_date.year,
               'month': dt_date.month,
               'doy': dt_date.timetuple().tm_yday,
               'dom': dt_date.timetuple().tm_mday,
               'level': m.group(4),
               'filename': m.group(0)}
    return id_meta


# 'A2004003000000.L1A_LAC.bz2' Aqua L1A
# T2002003002500.L1A_LAC.bz2 Terra L1A
# V2012005001200.L1A_SNPP.nc Viirs L1A
# V2012005001800.GEO-M_SNPP.nc Viirs L1A GEO
# V2014004000000.L2_SNPP_IOP.nc
# V2014004000000.L2_SNPP_OC.nc
# V2014004000000.L2_SNPP_SST.nc
# V2014004000000.L2_SNPP_SST3.nc
# S2001005025918.L1A_GAC.Z
# S2001005025918.L1A_MLAC.bz2
# http://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2005047193000.L2_LAC_IOP.nc

def make_file_path(filename, add_file = True):
    """Generate file path from its name

    Parses typical filename to build the path where the file should be
    written/found

    Args:
        filename (str): Filename or string containing the filename (e.g. Download url)
        add_file (bool): Path alone, or with filename appended

    Return:
        File path.
    """
    file_meta = parse_file_name(filename)
    file_path = os.path.join(file_meta['sensor'], file_meta['level'],\
                             str(file_meta['year']), str(file_meta['doy']).zfill(3))
    if add_file:
        file_path = os.path.join(file_path, file_meta['filename'])
    return file_path

def super_glob(dir, pattern):
    """glob with regex

    Args:
        dir (str): Search dir
        pattern (str): regex pattern

    Returns:
        List of matches
    """
    full_list = glob.glob(os.path.join(dir, '*'))
    re_pattern = re.compile(pattern)
    reduced_list = filter(re_pattern.search, full_list)
    return reduced_list

def is_day(filename):
    """Logical function to check whether a file is a night or a day file

    Details:
        Because time reported in file names are GMT times and not local
        times, this function has been customized for the satmo project area
        and is only valid for that area

    Args:
        filename (str): file name of a dataset

    Returns:
        Boolean, True if day file, False otherwise
    """
    dt_time = parse_file_name(filename)['time']
    # 12pm threshold validated against a full year for aqua, terra, viirs
    if dt_time > time(12, 0): 
        return True
    else:
        return False