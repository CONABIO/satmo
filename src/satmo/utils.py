import re
import glob
from datetime import datetime, time
import os
from pint import UnitRegistry

from .global_variables import SENSOR_CODES, DATA_LEVELS

# unit database for pint
ureg = UnitRegistry()


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

def OC_filename_builder(level, climatology = False, anomaly = False, full_path = False, data_root = None, **kwargs):
    """Utility to build valid ocean color filenames for every level

    Args:
        Positional arguments:
            level (str): the data level of the desired filename
        keywork arguments:
            climatology (bool): Does the filename correspond to climatology data
            anomaly (bool): Does the filename correspond to anomaly data
            full_path (bool): Should file path be computed (using OC_path_builder)
            data_root (str): To be used in combination with full_path = True, see OC_path_builder()
                doc for more details
        kwargs:
            General kwargs:
                None
            level specific kwargs (See details section to know which kwargs are required for each chosen level):
                filename (str): filename of the main input file used to produce the output (typically filename of a lower level file)
                suite (str): product suite of the desired file name (e.g. OC, SST, SST4, IOP)
                sensor_code (str): e.g.: 'A', 'V', 'X'
                date (datetime.datetime or str). IN the case of climatologies the year is ignored so that '1970-05-01' can
                be specified for example
                time (datetime.time): with hour, min, sec (e.g. datetime.time(12, 35, 0))
                doy (str or int): Day of the year
                composite (str): e.g. DAY, 8DAY, 16DAY, etc
                variable (str)
                resolution (str): e.g. '1km'
                begin_year (int or str): for climatologies, see CONVENTIONS.md
                end_year (int or str): for climatologies, see CONVENTIONS.md
                nc (bool): Should extension be '.nc' (instead of '.tif') (Only useful for L3m level, to distinguish between
                    tif files which are produced by e.g. custom compositing functions, and netcdf output of l3mapgen)

                
    Details:
        Each level= chosen requires different kwargs.
        'L2':
            filename and suite OR sensor_code, suite, date, and time
        'L3b':
            filename and suite OR sensor_code, date, suite
        'L3m' climatology:
            (date OR doy), composite, suite, variable, resolution, begin_year, end_year. If a date is provided, year does not matter
            # TODO: There could be a problem with the leap year when using date
        'L3m' anomaly:
            filename OR date, composite, suite, variable, resolution
        'L3m':
            filename, composite, variable, resolution, (nc) OR date, sensor_code, suite, composite, variable, resolution, (nc)

    Example usage:
        > import satmo
        > from datetime import datetime, time
        >
        > satmo.OC_filename_builder('L2', filename = 'T2001117063500.L1A_LAC.bz2', suite = 'OC', full_path = True, data_root = '/export/isilon/datos2/satmo2_data')
        > satmo.OC_filename_builder('L2', sensor_code = 'T', date = '1987-11-21', time = time(6, 35, 0), suite = 'OC')

    Returns:
        str: a syntactically ocean color filename
    """
    if level not in DATA_LEVELS:
        raise ValueError("Invalid level set")
    # Convert kwargs['date'] to datetime if it exists and is of type str
    try:
        if type(kwargs['date']) is str:
            kwargs['date'] = datetime.strptime(kwargs['date'], "%Y-%m-%d")
    except:
        pass
    #####
    # L2
    #####
    if level == 'L2':
        # A2008085203500.L2_LAC_OC.nc
        # filename and suite (OC, SST, SST4) OR sensor, date, time, sensor, suite, 
        if 'filename' in kwargs:
            filename = kwargs['filename']
            input_meta = OC_filename_parser(filename)
            sensor_code = input_meta['sensor_code']
            year = input_meta['year']
            doy = input_meta['doy']
            time = input_meta['time'].strftime('%H%M%S')
        else: # Assumes sensor_code, date, time and suite are provided
            year = kwargs['date'].year
            doy = kwargs['date'].timetuple().tm_yday
            time = kwargs['time'].strftime('%H%M%S')
            sensor_code = kwargs['sensor_code']
        suite = kwargs['suite']
        filename_elements = [sensor_code, year, str(doy).zfill(3), time, '.', level, '_', 'LAC', '_', suite, '.nc']
    #####
    # L3b
    #####
    elif level == 'L3b':
        # A2004005.L3b_DAY_CHL.nc
        # filename and suite OR sensor, date, suite
        if 'filename' in kwargs:
            filename = kwargs['filename']
            input_meta = OC_filename_parser(filename)
            sensor_code = input_meta['sensor_code']
            year = input_meta['year']
            doy = input_meta['doy']
        else:
            year = kwargs['date'].year
            doy = kwargs['date'].timetuple().tm_yday
            sensor_code = kwargs['sensor_code']
        suite = kwargs['suite']
        filename_elements = [sensor_code, year, str(doy).zfill(3), '.', level, '_', 'DAY', '_', suite, '.nc']
    #####
    # L3m CLIM
    #####
    elif level == 'L3m' and climatology:
        # CLIM.027.L3m_8DAY_SST_sst_1km_2000_2015.tif
        if 'date' in kwargs:
            doy = kwargs['date'].timetuple().tm_yday
        else:
            doy = kwargs['doy']
        composite = kwargs['composite']
        suite = kwargs['suite']
        variable = kwargs['variable']
        resolution = kwargs['resolution']
        begin_year = kwargs['begin_year']
        end_year = kwargs['end_year']
        filename_elements = ['CLIM.', str(doy).zfill(3), '.', level, '_', composite, '_', suite, '_', variable, '_', resolution, '_', begin_year, '_', end_year, '.tif']
    #####
    # L3m ANOM
    #####
    elif level == 'L3m' and anomaly:
        # ANOM.2014027.L3m_8DAY_SST_sst_1km.tif
        if 'filename' in kwargs:
            filename = kwargs['filename']
            input_meta = OC_filename_parser(filename)
            year = input_meta['year']
            doy = input_meta['doy']
            composite = input_meta['composite']
            resolution = input_meta['resolution']
            suite = input_meta['suite']
            variable = input_meta['variable']
        else:
            year = kwargs['date'].year
            doy = kwargs['date'].timetuple().tm_yday
            composite = kwargs['composite']
            suite = kwargs['suite']
            variable = kwargs['variable']
            resolution = kwargs['resolution']
        filename_elements = ['ANOM.', year, str(doy).zfill(3), '.', level, '_', composite, '_', suite, '_', variable, '_', resolution, '.tif']
    elif level == 'L3m':
        # filename, composite, suite, variable, resolution, nc OR sensor, date, composite, nc
        # X2014027.L3m_8DAY_SST_sst_1km.tif
        # X2014027.L3m_8DAY_SST_sst_1km.nc
        ext = '.tif'
        try:
            if kwargs['nc']:
                ext = '.nc'
        except:
            pass
        if 'filename' in kwargs:
            filename = kwargs['filename']
            input_meta = OC_filename_parser(filename)
            year = input_meta['year']
            doy = input_meta['doy']
            sensor_code = input_meta['sensor_code']
            suite = input_meta['suite']
        else:
            year = kwargs['date'].year
            doy = kwargs['date'].timetuple().tm_yday
            sensor_code = kwargs['sensor_code']
            suite = kwargs['suite']
        composite = kwargs['composite']
        variable = kwargs['variable']
        resolution = kwargs['resolution']
        filename_elements = [sensor_code, year, str(doy).zfill(3), '.', level, '_', composite, '_', suite, '_', variable, '_', resolution, ext]
    # Join filename elements
    filename_out = ''.join(str(x) for x in filename_elements)
    if full_path:
        filename_out = OC_path_builder(filename_out, data_root = data_root, add_file = True)
    return filename_out

    

def OC_path_builder(filename, data_root = None, add_file = True):
    """Universal path builder for Ocean color files

    Builds a file path from its filename

    Args:
        filename (str): syntactically correct ocean color file filename
        data_root (str): OPtional root folder prepended to generated path
            defaults to None
        add_file (bool): append filename to generated path? Defaults to False

    Returns:
        str: path associated to filename
    """
    file_meta = OC_filename_parser(filename)
    if file_meta['level'] == 'L3m':
        if file_meta['climatology']:
            path_elements = ['combined', file_meta['level'], '%s_clim' % file_meta['composite'], str(file_meta['doy']).zfill(3)]
        elif file_meta['anomaly']:
            path_elements = ['combined', file_meta['level'], '%s_anom' % file_meta['composite'], str(file_meta['year']), str(file_meta['doy']).zfill(3)]
        else:
            path_elements = [file_meta['sensor'], file_meta['level'], file_meta['composite'], str(file_meta['year']), str(file_meta['doy']).zfill(3)]
    else:
        path_elements = [file_meta['sensor'], file_meta['level'], str(file_meta['year']), str(file_meta['doy']).zfill(3)]
    if add_file:
        path_elements.append(file_meta['filename'])
    if data_root is not None:
        path_elements.insert(0, data_root)
    file_path = os.path.join(*path_elements)
    return file_path

def OC_path_finder(data_root, date, level, sensor_code = None, composite = None, anomaly = False, climatology = False, search = True):
    """Builds and find existing paths from meta information

    Builds a pseudo path name using provided metadata and runs glob.glob on it

    Args:
        data_root (str): Root of the data archive
        date (str or datetime): Date of the directory to find
        level (str): Data level
        sensor_code (str): Sensor of the directory to find. If None (default), is replaced by * in a glob search
        composite (str): Composite period of the directory to find (only for L3m, climatologies and anomalies)
        anomaly (bool): Are we looking for a directory of anomalies
        climatology (bool): Are we looking for a directory of climatologies
        search (bool): Should the function return the output of glob.glob() on the generated. Otherwise the glob pattern
            itself is returned. Defaults to True

    Details:
        if composite or anomaly is True, you only need to provide composite and date

    Returns:
        A list of existing paths matching the 'query'
    """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    if sensor_code is not None:
        sensor = SENSOR_CODES[sensor_code]
    else:
        sensor = '*'
    if climatology:
        path_elements = [data_root, 'combined', 'L3m', '%s_clim' % composite, str(date.timetuple().tm_yday).zfill(3)]
    elif anomaly:
        path_elements = [data_root, 'combined', 'L3m', '%s_anom' % composite, date.year, str(date.timetuple().tm_yday).zfill(3)]
    elif level == 'L3m':
        path_elements = [data_root, sensor, level, composite, date.year, str(date.timetuple().tm_yday).zfill(3)]
    else:
        path_elements = [data_root, sensor, level, date.year, str(date.timetuple().tm_yday).zfill(3)]
    path_pattern = os.path.join(*[str(x) for x in path_elements])
    if search:
        path_list = glob.glob(path_pattern)
        return path_list
    return path_pattern


def OC_file_finder(data_root, date, level, suite = None, variable = None, sensor_code = None, resolution = None, composite = None):
    """Finds existing files on the system from meta information (date, level, variable, sensor_code, ...)

    Builds a glob pattern from the provided information and runs glob.glob on it. THis function is not fully generic, and so mostly
    targetted at L1A, L2, and L3m file (no climatologies or anomalies). Example applications include:
        - list all L2 files required to produce a L3b binned product (don't forget filtering using isDay() as well)
        - list all L3m files from a same date but from different sensors in order to produce cross sensor composites

    Args:
        data_root (str): Root of the data archive
        date (str or datetime): Date of the directory to find
        level (str): Data level
        suite (str): Product suite (e.g. 'OC', 'CHL', 'SST')
        variable (str): Product variable (e.g. 'sst', 'chlor_a')
        sensor_code (str): Sensor code (e.g. 'A', 'T', 'V') of the files to query. If None (default), is replaced by * in a glob search
        resolution (str): e.g. '1km'
        composite (str): Composite period of the files to query

    Details:
        Required arguments differ depending on the level set. See list below:
        - 'L1A':
            data_root, date, level, (sensor_code)
        - 'L2':
            data_root, date, level, suite, (sensor_code)
        - 'L3m':
            data_root, date, level, suite, variable, (sensor_code), resolution, composite

    Returns:
        A list of filenames (empty if no matches)
        
    """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    path_pattern = OC_path_finder(data_root = data_root, level = level, date = date, composite = composite, search = False, sensor_code = sensor_code)
    if sensor_code is None:
        sensor_code = '*'
    if level == 'L1A':
        file_pattern = ''.join([sensor_code, str(date.year), str(date.timetuple().tm_yday).zfill(3), '*.', level, '*'])
    elif level == 'L2':
        file_pattern = ''.join([sensor_code, str(date.year), str(date.timetuple().tm_yday).zfill(3), '*.', level, '*', suite, '.nc'])
    elif level == 'L3m':
        file_pattern = ''.join([sensor_code, str(date.year), str(date.timetuple().tm_yday).zfill(3), '.', level, '_',
                                composite, '_', suite, '_', variable, '_', resolution, '*'])
    else:
        raise ValueError('Unsuported data level')
    full_pattern = os.path.join(path_pattern, file_pattern)
    file_list = glob.glob(full_pattern)
    return file_list



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

def is_night(filename):
    """Logical function to check whether a file is a night or a day file

    Details:
        Because time reported in file names are GMT times and not local
        times, this function has been customized for the satmo project area
        and is only valid for that area

    Args:
        filename (str): file name of a dataset

    Returns:
        Boolean, True if night file, False otherwise
    """
    return not is_day(filename)

def to_km(x):
    """Convert distance string to its km equivalent

    Args:
        x (str): A distance (resolution) string with unit (e.g.: '1000m')

    Return:
        str: A string of the form 'xxkm'
    """
    resolution_km = ureg(x).to(ureg.km)
    return '%dkm' % int(resolution_km.magnitude)
