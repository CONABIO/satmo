import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import Proj

from datetime import datetime
import re
import os
import warnings

from .global_variables import SENSOR_CODES, COMPOSITES

file = 'T2014027.L3m_DAY_CHL.tif'

def make_map_title(file):
    """Generate figure title from file name

    Meant to be used by the make_preview() function. Parses a file name
    and produces a string to be used as title for the preview figure

    Details:
        Example map titles include:
        Daily Chlor_a aqua 2014-01-27
        Daily SST combined 2014-01-27
        8 day composite SST combined 2014-01-27 (date corresponds to first day of the compositing period)
        8 day composite SST Climatology January 1
        Example file names are:
        T2014027.L3m_DAY_Chor_a.tif
        X2014027.L3m_DAY_SST.tif
        X2014027.L3m_8DAY_SST.tif
        XCLIM027.L3m_8DAY_SST.tif (climatology)

    Args:
        file (str): File name (usually a geoTiff)

    Returns:
        str: Figure title
    """
    file = os.path.basename(file)
    pattern = re.compile(r"(?P<sensor>[A-Z])(?P<year>[CLIM0-9]{4})(?P<doy>\d{3})\.(?P<level>[A-Za-z1-3]{3,4})_(?P<composite>.*?)_(?P<var>.*)\.")
    m = pattern.search(file)
    if m is None:
        return file
    try:
        sensor = SENSOR_CODES[m.group('sensor')]
        composite = COMPOSITES[m.group('composite')]
    except KeyError:
        return file
    var = m.group('var')
    if re.search(r'\d{4}', m.group('year')) is None: # It's CLIM
        date  = datetime.strptime(m.group('doy'), '%j').strftime("%B %d")
        title = '%s %s climatology %s' % (composite, var, date)
    else:
        date = str(datetime.strptime(m.group('year') + m.group('doy'), '%Y%j').date())
        title = '%s %s %s %s' % (composite, var, sensor, date)
    return title



def make_preview(file, stretch_range):
    """
    Args:
        file (str): Path to a raster file containing a single layer
        stretch_range (list or tupple): List or tupple of floats giving the upper and lower
        bounds used for color stretch
    """
    

    with rasterio.open(file) as src:
        meta = src.meta
        data = src.read(1, masked=True)

    try:
        from mpl_toolkits.basemap import Basemap
    except ImportError:
        warnings.warn('Install matplotlib basemap for full functionality (graticules and coastlines)')

        

    crs = meta['crs']
    p = Proj(**crs)
    map_width = meta['width'] * meta['affine'][0]
    map_height = meta['height'] * meta['affine'][0]
    xmin = meta['affine'][2]
    xmax = xmin + map_width
    ymax = meta['affine'][5]
    ymin = ymax - map_height
    llproj = (xmin, ymin)
    urproj = (xmax, ymax)
    llll = p(*llproj, inverse=True)
    urll = p(*urproj, inverse=True)
    extent = [xmin, xmax, ymin, ymax] # [left, right, bottom, top]

    # Instantiate Basemap
    m = Basemap(llcrnrlon=llll[0], llcrnrlat=llll[1], urcrnrlon=urll[0], urcrnrlat=urll[1],
                projection=crs['proj'],
                resolution='l', lat_0=crs['lat_0'], lon_0=crs['lon_0'])

    # draw coastlines.
    m.drawcoastlines()
    m.drawmapboundary(fill_color='darkgrey')
    m.drawlsmask(ocean_color='darkgrey')
    m.imshow(data, origin='upper', extent = extent, vmin=0, vmax=3)
    m.colorbar()
    # fill continents, set lake color same as ocean color.
    m.fillcontinents(color='grey',lake_color='black')
    # draw parallels and meridians.
    parallels = np.arange(0.,81,5.)
    meridians = np.arange(10.,351.,5.)
    # labels = [left,right,top,bottom]
    m.drawparallels(parallels,labels=[True,False,False,False])
    m.drawmeridians(meridians,labels=[False,False,False,True])
    plt.title('Daily Chlor_a Aqua 2014-01-27')
    plt.savefig('T2014027.L3m_DAY_CHL.png',dpi=100, transparent=True)




