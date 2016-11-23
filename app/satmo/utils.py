import re
from datetime import datetime
import os

# Global variable that contains sensor information
SENSOR_CODES = {'A': 'aqua',
                'T': 'terra',
                'S': 'seawifs',
                'V': 'viirs'}

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
    id_grep = re.compile("([A-Z])(\d{7})(\d{4})?(?:\d{2})?\.([A-Z1-3\-]{1,5})_(?:[A-Z]{3,4})_?(?:[A-Z]{3})?.*")
    m = id_grep.search(id)
    if m is None:
        raise ValueError('No valid data name found for %s' % id)
    dt = datetime.strptime(m.group(2), "%Y%j%H%M")
    id_meta = {'sensor': SENSOR_CODES[m.group(1)], #TODO: a KeyError will be thrown if a key is not in SENSOR_CODES, what to do with it
               'date': dt.date(),
               'time': dt.time(),
               'year': dt.year,
               'month': dt.month,
               'doy': dt.timetuple().tm_yday,
               'dom': dt.timetuple().tm_mday,
               'level': m.group(3),
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
