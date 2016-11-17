import re
from datetime import datetime, date

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
    """
    id_grep = re.compile(".*([A-Z])(\d{7})\d{6}\.(.*)_(.*)\..*")
    m = id_grep.search(id)
    if m is None:
        raise ValueError('No valid data name found for %s' % id)
    id_meta = {'sensor': SENSOR_CODES[m.group(1)],
               'date': datetime.strptime(m.group(2), "%Y%j").date(),
               'level': m.group(3),
               'product': m.group(4)}
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