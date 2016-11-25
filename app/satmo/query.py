from future.standard_library import install_aliases
install_aliases()

import urllib.parse

import requests
import re
from datetime import datetime


def query_from_extent(sensors, date_begin, per, north, south, west, east, day = True,\
                      night = True, base_url = 'http://oceancolor.gsfc.nasa.gov/cgi/browse.pl'):
    """Query L1A data for a given period and spatial extent

    Uses an old school perl 'API' to get a list of filenames that intersect with a
    geographical area and a time period. Only L1A products are queried at the moment,
    however, the function could easily be changed to query other collections (see prm
    query argument)

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
        base_url (str): 'api' host

    Returns:
        List of filenames

    """
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
    r0 = requests.get('?'.join([base_url, urllib.parse.urlencode(query0_args)]))
    if r0.status_code != 200:
        raise requests.HTTPError
    # regular expression to find the orderid in the html page
    orderid_grep = re.compile(r"filenamelist&id=(\d+\.\d+)")
    m = orderid_grep.search(r0.text)
    query1_args = {'sub': 'filenamelist',
                   'id': m.group(1),
                   'prm': 'TC'}
    r1 = requests.get('?'.join([base_url, urllib.parse.urlencode(query1_args)]))
    if r1.status_code != 200:
        raise requests.HTTPError
    file_list = r1.text.split('\n')
    return file_list[:-1]

# file_list = query_from_extent(['am'], '01-01-2007', 'MO', 33, 10, -100, -70)