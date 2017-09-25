import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import re
from datetime import datetime
import os.path

def query_from_extent(sensors, date_begin, per, north, south, west, east, day = True,
                      night = True, product = 'L1A', base_url = 'https://oceancolor.gsfc.nasa.gov/cgi/browse.pl'):
    """Query L1A data for a given period and spatial extent

    Uses an old school perl 'API' to get a list of filenames that intersect with a
    geographical area and a time period. The function was initially designed to query
    L1A products; capability to query different L2 collection was added later and may not
    function as well than the L1A query capability.

    Args:
        sensors: (list) list of strings, Valid entries are 'am' (aqua), 'tm' (terra),
        'sw' (seawifs), 'v0' (viirs)
        date_begin (datetime or str): date of the first day of the period queried
            use 'yyyy-mm-dd' format if passing it as a string
        per (str): The period queried. One of 'DAY', 'MO', 'YR'
        north (float): north latitude of bounding box in DD
        south (float): south latitude of bounding box in DD
        west (float): west longitude of bounding box in DD
        east (float): east longitude of bounding box in DD
        day (bool): Order day data ?
        night (bool): Order night data ?
        product (str): Product to order, defaults to 'L1A'. Other possible values include
            'CHL' for L2_OC, 'SST' for L2_SST, and 'SST4' for L2_SST4
        base_url (str): 'api' host

    Returns:
         list: List of filenames

    """
    # Instantiate a requests session and set number of retries and pause between them
    s = requests.Session()
    retries = Retry(total = 15, backoff_factor = 0.1, status_forcelist = [500, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries = retries))
    # Collect elements to build the first request url
    if type(sensors) is not list:
        raise TypeError('sensors must be a list')
    # Seawifs special case
    if 'sw' in sensors:
        typ = 'MLAC'
        sensors.remove('sw')
    else:
        typ = ''
    sensors = '@'.join(sensors)
    if type(date_begin) is str:
        date_begin = datetime.strptime(date_begin, "%Y-%m-%d")
    dnm = []
    if day is True:
        dnm.append('D')
    if night is True:
        dnm.append('N')
    if product == 'L1A':
        prm = 'TC'
    else:
        prm = product # Only useful for second request
    dnm = '@'.join(dnm)
    day = (date_begin - datetime(1970, 1, 1)).days
    # BUild dictionary of arguments
    query0_args = {'sub': 'level1or2list',
                   'per': per,
                   'day': day,
                   'sen': sensors,
                   'dnm': dnm,
                   'prm': 'TC',
                   'typ': typ,
                   'n': north,
                   's': south,
                   'w': west,
                   'e': east}
    # This first query will return an html page from which the order id can be retrieved
    # and used to send a second request
    r0 = s.get(base_url, params=query0_args)
    if r0.status_code != 200:
        raise requests.HTTPError
    # regular expression to find the orderid in the html page
    orderid_grep = re.compile(r"filenamelist&id=(\d+\.\d+)")
    m = orderid_grep.search(r0.text)
    query1_args = {'sub': 'filenamelist',
                   'id': m.group(1),
                   'prm': prm}
    r1 = s.get(base_url, params=query1_args)
    if r1.status_code != 200:
        raise requests.HTTPError
    file_list = r1.text.split('\n')
    return file_list[:-1]

# file_list = query_from_extent(['am'], '2007-01-01', 'MO', 33, 10, -100, -70)

def make_download_url(file_name, host = 'https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/'):
    """Builds a download URL from a (L1A) file name

    Simple helper that given a filename (obtained with query_from_extent
    for example), prepends the 'getFile url' of the oceancolor DAAC and appends 
    '.gz' when files are not netcdf.

    Args:
        file_name (str): name of a L1A file present on oceancolor servers
        host (str): Address of the root of the archive. DON'T FORGET TRAILING SLASH

    Details:
        In line with query_from_extent, this function is designed to work
        with L1A files from MODIS, VIIRS and SeaWifs. Untested for other sensors and
        other data levels.

    Returns:
        A string of the URL at which the file can be downloaded (ready to be passed to
        download_robust)
    """
    url_components = [host, file_name]
    if os.path.splitext(file_name)[1] != '.nc':
        url_components.append('.bz2')
    return ''.join(url_components)

def get_subscription_urls(id):
    """Send a request to a subscription number to get a list of download URLs

    Args:
        id (int): Ocean color subscription number

    Returns:
        A list of download urls
    """
    args_dict = {'subID': id,
                 'addurl': 1,
                 'results_as_file': 1}
    r = requests.get("https://oceandata.sci.gsfc.nasa.gov/search/file_search.cgi",
                    params=args_dict)
    url_list = r.text.split('\n')[:-1]
    return url_list
