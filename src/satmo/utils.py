import re
import glob
from datetime import datetime, time
import os

from .global_variables import SENSOR_CODES, DATA_LEVELS


def OC_filename_parser(filename, raiseError = True):
    """File parser for ocean color products

    Extract metadata information from a typical ocean color file name

    Args:
        filename (str): String containing an ocean color file filename
        raiseError (bool): Behavior when no valid pattern is found.
        True (default) returns a ValueError, false returns a dictionnaries of
        Nones

    Details:
        The parser will probably fail for the following products:
        - L0
        - Sentinel 3
        - Meris for levels lower than L2

    Returns:
        A dictionnary with the following keys:
        sensor (str)
        sensor_code (str)
        date (datetime.date)
        time (datetime.time)
        year (int)
        month (int)
        doy (int)
        dom (int)
        level (str)
        filename (str)
        climatology (bool)
        anomaly (bool)
        resolution (str)
        variable (str)
        suite (str)
        composite (str) e.g.: DAY, 8DAY, ...
        begin_year (int) (for climatologies only)
        end_year (int) (for climatologies only)
        Key values are set to None when not applicable
    """
    pattern_0 = re.compile(r'(?P<sensor_code>CLIM\.|ANOM\.|[A-Z]{1})(?P<time_info>\d{3}\.|\d{7}\.|\d{13}\.)(?P<level>L0|L1A|L1B|GEO|L2|L3b|L3m)_.*')
    m_0 = pattern_0.search(filename)
    if m_0 is None:
        if raiseError:
            raise ValueError('No valid data name found for %s' % filename)
        else:
            meta_dict = {'sensor': None,
                         'sensor_code': None,
                         'date': None,
                         'time': None,
                         'year': None,
                         'month': None,
                         'doy': None,
                         'dom': None,
                         'level': None,
                         'filename': os.path.basename(filename),
                         'climatology': None,
                         'anomaly': None,
                         'resolution': None,
                         'variable': None,
                         'suite': None,
                         'composite': None,
                         'begin_year': None,
                         'end_year': None}
            return meta_dict
    # filename with eventual prefixes removed
    filename = m_0.group()
    # Treat each level indepndently
    if m_0.group('sensor_code') == 'CLIM.':
        pattern = re.compile(r'CLIM\.(?P<doy>\d{3})\.(?P<level>[A-Za-z1-3]{3,4})_(?P<composite>.*?)' \
                             r'_(?P<suite>.*?)_(?P<variable>.*)_(?P<resolution>.*?)_(?P<begin_year>\d{4})_(?P<end_year>\d{4})\..*')
        m = pattern.search(filename)
        meta_dict = {'sensor': None,
                     'sensor_code': None,
                     'date': None,
                     'time': None,
                     'year': None,
                     'month': None,
                     'doy': int(m.group('doy')),
                     'dom': None,
                     'level': m.group('level'),
                     'filename': filename,
                     'climatology': True,
                     'anomaly': False,
                     'resolution': m.group('resolution'),
                     'variable': m.group('variable'),
                     'suite': m.group('suite'),
                     'composite': m.group('composite'),
                     'begin_year': int(m.group('begin_year')),
                     'end_year': int(m.group('end_year'))}

    elif m_0.group('sensor_code') == 'ANOM.':
        pattern = re.compile(r'ANOM\.(?P<date>\d{7})\.(?P<level>[A-Za-z1-3]{3,4})_(?P<composite>.*?)' \
                              '_(?P<suite>.*?)_(?P<variable>.*)_(?P<resolution>.*?)\..*')
        m = pattern.match(filename)
        dt_date = datetime.strptime(m.group('date'), "%Y%j")
        meta_dict = {'sensor': None,
                     'sensor_code': None,
                     'date': dt_date.date(),
                     'time': None,
                     'year': dt_date.year,
                     'month': dt_date.month,
                     'doy': dt_date.timetuple().tm_yday,
                     'dom': dt_date.timetuple().tm_mday,
                     'level': m.group('level'),
                     'filename': filename,
                     'climatology': False,
                     'anomaly': True,
                     'resolution': m.group('resolution'),
                     'variable': m.group('variable'),
                     'suite': m.group('suite'),
                     'composite': m.group('composite'),
                     'begin_year': None,
                     'end_year': None}
    elif m_0.group('level') in ['L1A', 'L1B']:
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})(?P<time>\d{6})\.(?P<level>[A-Za-z1-3]{3,4})_.*')
        m = pattern.match(filename)
        dt_date = datetime.strptime(m.group('date'), "%Y%j")
        meta_dict = {'sensor': SENSOR_CODES[m.group('sensor')],
                     'sensor_code': m.group('sensor'),
                     'date': dt_date.date(),
                     'time': datetime.strptime(m.group('time'), "%H%M%S").time(),
                     'year': dt_date.year,
                     'month': dt_date.month,
                     'doy': dt_date.timetuple().tm_yday,
                     'dom': dt_date.timetuple().tm_mday,
                     'level': m.group('level'),
                     'filename': filename,
                     'climatology': False,
                     'anomaly': False,
                     'resolution': None,
                     'variable': None,
                     'suite': None,
                     'composite': None,
                     'begin_year': None,
                     'end_year': None}
    elif m_0.group('level') == 'GEO':
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})(?P<time>\d{6})\..*')
        m = pattern.match(filename)
        dt_date = datetime.strptime(m.group('date'), "%Y%j")
        meta_dict = {'sensor': SENSOR_CODES[m.group('sensor')],
                     'sensor_code': m.group('sensor'),
                     'date': dt_date.date(),
                     'time': datetime.strptime(m.group('time'), "%H%M%S").time(),
                     'year': dt_date.year,
                     'month': dt_date.month,
                     'doy': dt_date.timetuple().tm_yday,
                     'dom': dt_date.timetuple().tm_mday,
                     'level': 'GEO',
                     'filename': filename,
                     'climatology': False,
                     'anomaly': False,
                     'resolution': None,
                     'variable': None,
                     'suite': None,
                     'composite': None,
                     'begin_year': None,
                     'end_year': None}
    elif m_0.group('level') == 'L2':
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})(?P<time>\d{6})\.(?P<level>L2)_(.*?)_(?P<suite>.*)\..*')
        m = pattern.match(filename)
        dt_date = datetime.strptime(m.group('date'), "%Y%j")
        meta_dict = {'sensor': SENSOR_CODES[m.group('sensor')],
                     'sensor_code': m.group('sensor'),
                     'date': dt_date.date(),
                     'time': datetime.strptime(m.group('time'), "%H%M%S").time(),
                     'year': dt_date.year,
                     'month': dt_date.month,
                     'doy': dt_date.timetuple().tm_yday,
                     'dom': dt_date.timetuple().tm_mday,
                     'level': m.group('level'),
                     'filename': filename,
                     'climatology': False,
                     'anomaly': False,
                     'resolution': None,
                     'variable': None,
                     'suite': m.group('suite'),
                     'composite': None,
                     'begin_year': None,
                     'end_year': None}
    elif m_0.group('level') == 'L3b':
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})\.(?P<level>L3b)_(.*?)_(?P<suite>.*)\..*')
        m = pattern.match(filename)
        dt_date = datetime.strptime(m.group('date'), "%Y%j")
        meta_dict = {'sensor': SENSOR_CODES[m.group('sensor')],
                     'sensor_code': m.group('sensor'),
                     'date': dt_date.date(),
                     'time': None,
                     'year': dt_date.year,
                     'month': dt_date.month,
                     'doy': dt_date.timetuple().tm_yday,
                     'dom': dt_date.timetuple().tm_mday,
                     'level': m.group('level'),
                     'filename': filename,
                     'climatology': False,
                     'anomaly': False,
                     'resolution': None,
                     'variable': None,
                     'suite': m.group('suite'),
                     'composite': None,
                     'begin_year': None,
                     'end_year': None}
    elif m_0.group('level') == 'L3m':
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})\.(?P<level>L3m)_(?P<composite>.*?)' \
                             r'_(?P<suite>.*?)_(?P<variable>.*)_(?P<resolution>.*)\..*')
        m = pattern.match(filename)
        dt_date = datetime.strptime(m.group('date'), "%Y%j")
        meta_dict = {'sensor': SENSOR_CODES[m.group('sensor')],
                     'sensor_code': m.group('sensor'),
                     'date': dt_date.date(),
                     'time': None,
                     'year': dt_date.year,
                     'month': dt_date.month,
                     'doy': dt_date.timetuple().tm_yday,
                     'dom': dt_date.timetuple().tm_mday,
                     'level': m.group('level'),
                     'filename': filename,
                     'climatology': False,
                     'anomaly': False,
                     'resolution': m.group('resolution'),
                     'variable': m.group('variable'),
                     'suite': m.group('suite'),
                     'composite': m.group('composite'),
                     'begin_year': None,
                     'end_year': None}
    return meta_dict


def OC_path_builder(filename, add_file = True):
    # Universal path builder for Ocean color files
    pass



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
    file_meta = OC_filename_parser(filename)
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
    input_dict = OC_filename_parser(filename)
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
    dt_time = OC_filename_parser(filename)['time']
    # 12pm threshold validated against a full year for aqua, terra, viirs
    if dt_time > time(12, 0): 
        return True
    else:
        return False