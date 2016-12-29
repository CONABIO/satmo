import re
import glob
from datetime import datetime, time
import os

from .global_variables import SENSOR_CODES, DATA_LEVELS

def parse_file_name(id, raiseError = True):
    """Filename parser for modis, viirs, seawifs

    Identifies a typical sequence corresponding to a satelite data filename
    and parses it to return a dictonary with sensor, level, date, etc

    Args:
        id (string) string containing a Landsat scene ID
        raiseError (bool): Behavior when no valid pattern is found.
        True (default) returns a ValueError, false returns a dictionnaries of
        Nones

    Returns:
        dictionary: Dictionary containing information on sensor, date, level, etc
        year, month, doy, dom are integers
    """
    pattern = re.compile(r"([A-Z])(\d{7})(\d{4})?(?:\d{2})?\.([A-Za-z1-3\-]{2,5})_?(?:[A-Z]{3,4})?_?(?:[A-Z]{3})?.*")
    m = pattern.search(id)
    if m is None:
        if raiseError:
            raise ValueError('No valid data name found for %s' % id)
        else:
            id_meta = {'sensor': None, #TODO: a KeyError will be thrown if a key is not in SENSOR_CODES, what to do with it
                       'date': None,
                       'time': None,
                       'year': None,
                       'month': None,
                       'doy': None,
                       'dom': None,
                       'level': None,
                       'filename': None}
            return id_meta
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

def make_file_path(filename, add_file = True, doy = True, level = None):
    """Generate file path from its name

    Parses typical filename to build the path where the file should be
    written/found

    Args:
        filename (str): Filename or string containing the filename (e.g. Download url)
        add_file (bool): Path alone, or with filename appended
        doy (bool): Should doy (day of the year) be part of the path (otherwise)
        it finishes by year/(filename)
        level (str): allows to build a path for a different level (useful to set output dir
        when processing higher levels with seadas).

    Details:
        If set, the level argument is checked against a database of valid data levels and automatically
        sets add_file to False

    Return:
        File path.
    """
    file_meta = parse_file_name(filename)
    if level is None:
        level = file_meta['level']
    else:
        if level not in DATA_LEVELS:
            raise ValueError("Invalid level set")
        add_file = False
    path_elements = [file_meta['sensor'], level, str(file_meta['year'])]
    if doy:
        path_elements.append(str(file_meta['doy']).zfill(3))
    if add_file:
        path_elements.append(file_meta['filename'])
    file_path = os.path.join(*path_elements)
    return file_path

def file_path_from_sensor_date(sensor, date, data_root, level = 'L1A', doy = True):
    """Util function to compute a path from 

    Args:
        sensor (str): 'aqua', 'terra', 'seawifs', 'viirs'
        date (datetime or str): date for which path should be computed, 'yyyy-mm-dd' if str
        data_root (str): Root of the data archive to which computed path will be appended
        level (str): data level
        doy (bool): append doy to path, defaults to True

    Return:
        File path
    """
    if level not in DATA_LEVELS:
        raise ValueError("Invalid level set")
    # levels with doy in file path
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    year = date.year
    path_elements = [data_root, sensor, level, str(year)]
    if doy:
        path_elements.append(str(date.timetuple().tm_yday).zfill(3))
    file_path = os.path.join(*path_elements)
    return file_path



def make_file_name(filename, level, suite, ext = '.nc'):
    """Jumps a filename to its corresponding filename at a higher level

    Args:
        filename (str): Input file name (e.g. Level 2A filename)
        level (str): data level of returned file name
        suite (str): product suite name
        ext (str): Extension, defaults to '.nc'

    Details:
        level= argument is checked against a database of valid levels 
    """
    if level not in DATA_LEVELS:
        raise ValueError("Invalid level set")
    input_dict = parse_file_name(filename)
    out_name = '%s.%s_DAY_%s%s' % (input_dict['filename'][:8], level, suite, ext)
    return out_name


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