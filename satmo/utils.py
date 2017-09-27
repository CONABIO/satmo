import re
import glob
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import calendar
import os
from pint import UnitRegistry
import signal
from contextlib import contextmanager
import random
import string

from .errors import TimeoutException
from .global_variables import SENSOR_CODES, DATA_LEVELS, VARS_FROM_L2_SUITE


# unit database for pint
ureg = UnitRegistry()

def filename_parser(filename, raiseError = True):
    """File parser for ocean color products

    Extract metadata information from a typical ocean color file name
    
    The parser will probably fail for the following products:
        * L0
        * Sentinel 3
        * Meris for levels lower than L2

    Args:
        filename (str): String containing an ocean color file filename
        raiseError (bool): Behavior when no valid pattern is found.
        True (default) returns a ValueError, false returns a dictionaries of
            Nones


    Returns:
        dict: A dictionary with the following keys::

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
    pattern_0 = re.compile(r'(?P<sensor_code>CLIM\.|ANOM\.|[A-Z]{1})(?P<time_info>\d{3}\.|\d{7}\.|\d{13}\.)(?P<level>L0|L1A|L1B|GEO|GEO-M|L2|L2m|L3b|L3m)_.*')
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
    elif m_0.group('level') in ['GEO', 'GEO-M']:
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
    elif m_0.group('level') == 'L2m':
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})(?P<time>\d{6})\.(?P<level>L2m)_(?P<suite>.*?)_(?P<variable>.*)\..*')
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
                     'variable': m.group('variable'),
                     'suite': m.group('suite'),
                     'composite': None,
                     'begin_year': None,
                     'end_year': None}
    elif m_0.group('level') == 'L3b':
        pattern = re.compile(r'(?P<sensor>[A-Z])(?P<date>\d{7})\.(?P<level>L3b)_(?P<composite>.*?)_(?P<suite>.*)\..*')
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
                     'composite': m.group('composite'),
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

def filename_builder(level, climatology = False, anomaly = False, full_path = False, data_root = None, **kwargs):
    """Utility to build valid ocean color filenames for every level
    
    Each level= chosen requires different kwargs.

    'L2': filename and suite OR sensor_code, suite, date, and time

    'L3b': filename, composite and suite OR sensor_code, date, composite, suite

    'L3m' climatology: (date OR doy), composite, suite, variable, resolution, begin_year, end_year. If a date is provided, year does not matter
        
    'L3m' anomaly: filename OR date, composite, suite, variable, resolution
        
    'L3m': filename, composite, variable, resolution, (nc) OR date, sensor_code, suite, composite, variable, resolution, (nc)

    Args:
        level (str): the data level of the desired filename
        climatology (bool): Does the filename correspond to climatology data
        anomaly (bool): Does the filename correspond to anomaly data
        full_path (bool): Should file path be computed (using path_builder)
        data_root (str): To be used in combination with full_path = True, see path_builder()
            doc for more details
        **kwargs:
            level specific kwargs (See details section to know which kwargs are required for each chosen level):

            filename (str): filename of the main input file used to produce the output (typically filename of a lower level file)
            
            suite (str): product suite of the desired file name (e.g. OC, SST, SST4, IOP)
            
            sensor_code (str): e.g.: 'A', 'V', 'X'
            
            date (datetime.datetime or str): IN the case of climatologies the year is ignored so that '1970-05-01' can
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

    Examples:
        >>> import satmo
        >>> from datetime import datetime, time
        >>>
        >>> satmo.filename_builder('L2', filename = 'T2001117063500.L1A_LAC.bz2', suite = 'OC', full_path = True, data_root = '/export/isilon/datos2/satmo2_data')
        >>> satmo.filename_builder('L2', sensor_code = 'T', date = '1987-11-21', time = time(6, 35, 0), suite = 'OC')

    Returns:
        str: a syntactically correct ocean color filename
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
            input_meta = filename_parser(filename)
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
            input_meta = filename_parser(filename)
            sensor_code = input_meta['sensor_code']
            year = input_meta['year']
            doy = input_meta['doy']
        else:
            year = kwargs['date'].year
            doy = kwargs['date'].timetuple().tm_yday
            sensor_code = kwargs['sensor_code']
        composite = kwargs['composite']
        suite = kwargs['suite']
        filename_elements = [sensor_code, year, str(doy).zfill(3), '.', level, '_', composite, '_', suite, '.nc']
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
            input_meta = filename_parser(filename)
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
    #####
    # L2m
    #####
    elif level == 'L2m':
        # A2008085203500.L2m_CHL_chlor_a.tif
        # filename, suite, variable OR sensor, date, composite, nc
        if 'filename' in kwargs:
            filename = kwargs['filename']
            input_meta = filename_parser(filename)
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
        variable = kwargs['variable']
        filename_elements = [sensor_code, year, str(doy).zfill(3), time, '.', level, '_', suite, '_', variable, '.tif']
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
            input_meta = filename_parser(filename)
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
        filename_out = path_builder(filename_out, data_root = data_root, add_file = True)
    return filename_out


def path_builder(filename, data_root = None, add_file = True):
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
    file_meta = filename_parser(filename)
    if file_meta['level'] == 'L3m':
        if file_meta['climatology']:
            path_elements = ['combined', file_meta['level'], '%s_clim' % file_meta['composite'], str(file_meta['doy']).zfill(3)]
        elif file_meta['anomaly']:
            path_elements = ['combined', file_meta['level'], '%s_anom' % file_meta['composite'], str(file_meta['year']), str(file_meta['doy']).zfill(3)]
        else:
            path_elements = [file_meta['sensor'], file_meta['level'], file_meta['composite'], str(file_meta['year']), str(file_meta['doy']).zfill(3)]
    elif file_meta['level'] == 'GEO':
        # Geo files go alongside L1A (useful when downloading viirs L1A)
        path_elements = [file_meta['sensor'], 'L1A', str(file_meta['year']), str(file_meta['doy']).zfill(3)]
    else:
        path_elements = [file_meta['sensor'], file_meta['level'], str(file_meta['year']), str(file_meta['doy']).zfill(3)]
    if add_file:
        path_elements.append(file_meta['filename'])
    if data_root is not None:
        path_elements.insert(0, data_root)
    file_path = os.path.join(*path_elements)
    return file_path

def path_finder(data_root, date, level, sensor_code = None, composite = None, anomaly = False, climatology = False, search = True):
    """Builds and find existing paths from meta information

    Builds a pseudo path name using provided metadata and runs glob.glob on it.

    If composite or anomaly is True, you only need to provide composite and date

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

    Returns:
        list: A list of existing paths matching the 'query'
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
    elif level == 'L3b':
        path_elements = [data_root, sensor, level, date.year, str(date.timetuple().tm_yday).zfill(3)]
    else:
        path_elements = [data_root, sensor, level, date.year, str(date.timetuple().tm_yday).zfill(3)]
    path_pattern = os.path.join(*[str(x) for x in path_elements])
    if search:
        path_list = glob.glob(path_pattern)
        return path_list
    return path_pattern


def file_finder(data_root, date, level, suite = None, variable = None, sensor_code = None, resolution = None, composite = None):
    """Finds existing files on the system from meta information (date, level, variable, sensor_code, ...)

    Builds a glob pattern from the provided information and runs glob.glob on it. THis function is not fully generic, and so mostly
    targeted at L1A, L2, and L3m file (no climatologies or anomalies). Example applications include:
        * list all L2 files required to produce a L3b binned product (don't forget filtering using isDay() as well)
        * list all L3m files from a same date but from different sensors in order to produce cross sensor composites

    Required arguments differ depending on the level set. See list below:
        * 'L1A': data_root, date, level, (sensor_code)
        * 'L2': data_root, date, level, suite, (sensor_code)
        * 'L3m': data_root, date, level, suite, variable, (sensor_code), resolution, composite
        * 'L3b': data_root, date, level, suite, (sdata_root, date, level, suite, (sensor_code), compositeensor_code), composite
    
    Args:
        data_root (str): Root of the data archive
        date (str or datetime): Date of the directory to find
        level (str): Data level
        suite (str): Product suite (e.g. 'OC', 'CHL', 'SST')
        variable (str): Product variable (e.g. 'sst', 'chlor_a')
        sensor_code (str): Sensor code (e.g. 'A', 'T', 'V') of the files to query. If None (default), is replaced by * in a glob search
        resolution (str): e.g. '1km'
        composite (str): Composite period of the files to query

    Returns:
        list: A list of filenames (empty if no matches)
    """
    if type(date) is str:
        date = datetime.strptime(date, "%Y-%m-%d")
    path_pattern = path_finder(data_root = data_root, level = level, date = date, composite = composite, search = False, sensor_code = sensor_code)
    if sensor_code is None:
        sensor_code = '*'
    if level == 'L1A':
        file_pattern = ''.join([sensor_code, str(date.year), str(date.timetuple().tm_yday).zfill(3), '*.', level, '*'])
    elif level == 'L2':
        file_pattern = ''.join([sensor_code, str(date.year), str(date.timetuple().tm_yday).zfill(3), '*.', level, '*', suite, '.nc'])
    elif level == 'L3m':
        file_pattern = ''.join([sensor_code, str(date.year),
                                str(date.timetuple().tm_yday).zfill(3), '.', level, '_',
                                composite, '_', suite, '_', variable, '_',
                                resolution, '.tif'])
    elif level == 'L3b':
        file_pattern = ''.join([sensor_code, str(date.year),
                                str(date.timetuple().tm_yday).zfill(3), '.', level, '_',
                                composite, '_', suite, '.nc'])
    else:
        raise ValueError('Unsuported data level')
    full_pattern = os.path.join(path_pattern, file_pattern)
    file_list = glob.glob(full_pattern)
    return file_list

def viirs_geo_filename_builder(x):
    """Builds the viirs geo filename corresponding to a L1A file

    Args:
        x (str): L1A viirs filename

    Return:
        str: A viirs geo filename
    """
    dirname, basename = os.path.split(x)
    basename = basename.replace('L1A', 'GEO-M')
    return os.path.join(dirname, basename)

def is_day(filename):
    """Logical function to check whether a file is a night or a day file

    Because time reported in file names are GMT times and not local
    times, this function has been customized for the satmo project area
    and is only valid for that area

    Args:
        filename (str): file name of a dataset

    Returns:
        bool: True if day file, False otherwise
    """
    dt_time = filename_parser(filename)['time']
    # 12pm threshold validated against a full year for aqua, terra, viirs
    if dt_time > time(12, 0):
        return True
    else:
        return False

def is_night(filename):
    """Logical function to check whether a file is a night or a day file

    Because time reported in file names are GMT times and not local
    times, this function has been customized for the satmo project area
    and is only valid for that area

    Args:
        filename (str): file name of a dataset

    Returns:
        bool: True if night file, False otherwise
    """
    return not is_day(filename)

def to_km(x):
    """Convert distance string to its km equivalent

    Args:
        x (str): A distance (resolution) string with unit (e.g.: '1000m')

    Returns:
        str: A string of the form 'xxkm'
    """
    resolution_km = ureg(x).to(ureg.km)
    return '%dkm' % int(resolution_km.magnitude)

def resolution_to_km_str(x):
    """Builds a string with unit in km from an int (resolution in m)

    Args:
        x (str): Typically a resolution in meters

    Returns:
        str: A string of the form 'xxkm'
    """
    resolution_m = x * ureg.meter
    resolution_km = resolution_m.to(ureg.km)
    return '%dkm' % int(resolution_km.magnitude)

def bit_pos_to_hex(x):
    """Takes a list containing bit positions and returns the corresponding
    integer

    Args:
        x (list): A list of bit position (e.g.: [0,3] for 1001, aka 9)

    Returns:
        int: The integer corresponding to the list of bit position provided in the
        list
    """
    bit_list = [0] * (max(x) + 1)
    for i in x:
        bit_list[i] = 1
    out = 0
    for bit in bit_list[::-1]:
        out = (out << 1) | bit
    return out

def _range_dt(begin, end, delta):
    """Internal function to make a list of dates with a given delta and retested to first of January on every year jump

    Args:
        begin (datetime.datetime): Begin date of the first composite
        end (datetime.datetime): Begin date of the last composite
        delta (int): composite length in days

    Returns:
        list: A list of datetime.datetime corresponding to first day of each
        composite
    """
    time_keeper = begin
    date_list = []
    while time_keeper <= end:
        date_list.append(time_keeper)
        year_next_step = (time_keeper + timedelta(delta)).year
        if year_next_step != time_keeper.year:
            # Reset to first of January of the new year
            time_keeper = datetime(year_next_step, 1, 1)
        else:
            time_keeper += timedelta(delta)
    return date_list

def _diff_month(d1, d2):
    """INternal function to compute the number of months between two dates

    Args:
        d1 (datatime.datetime): posterior date
        d2 (datatime.datetime): anterior date

    Returns:
        int: The integer corresponding to the number of months between the two dates.
    """
    return (d1.year - d2.year) * 12 + d1.month - d2.month

def _month_dates_from_dt(dt):
    """INternal function to return all the dates of the month to which belong the input date provided

    Args:
        dt (datetime.datetime): Date

    Returns:
        list: A list of dates.
    """
    nday = calendar.monthrange(dt.year, dt.month)[1]
    days = [datetime(dt.year, dt.month, day) for day in range(1, nday+1)]
    return days

def pre_compose(begin, end, delta):
    """Prepare a list of list of datetime to run with a compositing function

    Each sub list in the returned list contains the dates required to make the
    composite. When delta is not a multiple of the number of day of a given
    year, the last composite of the year is truncated and the next composite
    starts on the first of January of the following calendar year.

    Args:
        begin (datetime.datetime): Begin date of the first composite
        end (datetime.datetime): Begin date of the last composite
        delta (int or str): composite length in days if int, 'month' if str.

    Return:
        list: A list of lists.

    Examples:
        >>> import satmo
        >>> satmo.pre_compose(datetime.datetime(2000, 1, 1), datetime.datetime(2002,12,31), 16)
        >>> satmo.pre_compose(datetime.datetime(2000, 1, 1), datetime.datetime(2002,12,31), 'month')
    """

    if delta == 'month':
        month_list = [begin + relativedelta(months = m) for m in range(_diff_month(end, begin)+1)]
        dateList_list = [_month_dates_from_dt(x) for x in month_list]
    elif isinstance(delta, int):
        begin_list = _range_dt(begin, end, delta)
        delta_list = [(j-i).days for i, j in zip(begin_list[:-1], begin_list[1:])]
        delta_list.append(delta)
        dateList_list = []
        for (b, d) in zip(begin_list, delta_list):
            dateList_list.append([b + timedelta(days=x) for x in range(0, d)])
    else:
        raise ValueError('delta must be \'month\' or an integer')
    return dateList_list

def processing_meta_from_list(file_list):
    """Takes a list of filenames and returns a list of dictionaries with processing metadata

    The function is meant to be used within satmo.wrappers.nrt_wrapper to know
    which information can be generated from a list of newly downloaded files
    and hence kick-off the right processing chains.

    Args:
        file_list (list): A list of file names parsable by filename_parser

    Returns:
        A list of unique dictionaries containing processing information.
            
        Example of a dict (list element)::

            {'date': datetime.date(2017, 6, 25),
             'products': ['Rrs_412',
                          'Rrs_443',
                          'Rrs_469',
                          'Rrs_488',
                          'Rrs_531',
                          'Rrs_547',
                          'Rrs_555',
                          'Rrs_645',
                          'Rrs_667',
                          'Rrs_678',
                          'Kd_490',
                          'chl_ocx',
                          'aot_869',
                          'ipar',
                          'nflh',
                          'par',
                          'pic',
                          'poc',
                          'chlor_a'],
             'sensor': 'aqua',
             'sensor_code': 'A'}

    """
    def _processing_meta_from_name(x):
        """Function to generate with the appropriate keys from a single list item
        """
        d = filename_parser(x)
        sensor = d['sensor']
        day_night = 'day' if is_day(x) else 'night'
        out_dict = {'date': datetime.combine(d['date'], datetime.min.time()),
                    'sensor': sensor,
                    'sensor_code': d['sensor_code'],
                    'products': VARS_FROM_L2_SUITE[sensor][day_night][d['suite']]}
        return out_dict
    dict_list = [_processing_meta_from_name(file) for file in file_list]
    # Remove duplicate dictionaries
    out = []
    for item in dict_list:
        if item not in out:
            out.append(item)
    return out

def get_date_list(file_list):
    """Get the list of dates covered by a list of files

    Meant to be used within nrt_wrapper to determine generate inputs to run bin_map_wrapper

    Args:
        x (list): A list of valid (parsable with filename_parser) Ocean color filenames

    Returns:
        list: A list of datetime.
    """
    def _get_date(x):
        d = filename_parser(x)['date']
        dt = datetime.combine(d, time())
        return dt
    date_list = [_get_date(x) for x in file_list]
    date_list_unique = list(set(date_list))
    return date_list_unique

def find_composite_date_list(date, delta):
    """Find, given a date and delta, all the dates that compose the composite to which the input date belong

    To be used with the near real time wrapper function to find out, when a new
    L3m file is produced, which composite should be created or updated.

    Args:
        date (datetime.datetime): Input date (probably corresponding to a newly
            created L3m file (e.g.: daily composite))
        delta (int or str): composite length in days if int, 'month' if str.

    Returns:
        list: A list of dates (to be passed to make_time_composite)
    """
    begin = datetime(date.year, 1, 1)
    end = datetime(date.year + 1, 1, 1)
    date_list_list = pre_compose(begin, end, delta)
    date_list = [x for x in date_list_list if date in x][0]
    return date_list

@contextmanager
def time_limit(seconds):
    """Forces call timeout after a defined duration

    Args:
        seconds (int): Timeout limit

    Examples:
        >>> # Use in a context manager, raises a TimeoutException when time spent within
        >>> # the context manger exceeds specified duration in seconds
        >>> import time
        >>> from pprint import pprint
        >>> from satmo import TimeoutException, time_limit

        >>> try:
        >>>     with time_limit(12):
        >>>         time.sleep(13)
        >>> except TimeoutException as e:
        >>>     pprint('Function timed out')
    """
    def signal_handler(signum, frame):
        raise TimeoutException
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def randomword(length):
    """Generate a random string of desired length
    """
    return ''.join(random.choice(string.lowercase) for i in range(length))

