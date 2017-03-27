import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import rasterio
from pyproj import Proj
import netCDF4 as nc

from datetime import datetime
import re
import os
import warnings

from .global_variables import SENSOR_CODES, COMPOSITES, INDICES
from .geo import geo_dict_from_nc
from .utils import OC_filename_parser

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
        T2014027.L3m_DAY_CHL_chlor_a_1km.tif
        X2014027.L3m_DAY_SST_sst_1km.tif
        X2014027.L3m_8DAY_SST_sst_1km.tif
        XCLIM027.L3m_8DAY_SST_sst_1km.tif (climatology)
        T2004005.L3m_DAY_CHL_chlor_a_250m.tif
        A2007009.L3m_DAY_SST4_sst4_4km.nc

    Args:
        file (str): File name (usually a geoTiff)

    Returns:
        str: Figure title
    """
    try:
        meta_dict = OC_filename_parser(file, raiseError = True)
    except:
        return os.path.basename(file)
    try:
        sensor = meta_dict['sensor']
        composite = COMPOSITES[meta_dict['composite']]
    except KeyError:
        return os.path.basename(file)
    var = meta_dict['variable']
    resolution = meta_dict['resolution']
    if meta_dict['climatology']:
        date  = datetime.strptime(str(meta_dict['doy']), '%j').strftime("%B %d")
        title = '%s %s climatology %s %s' % (composite, var, date, resolution)
    else:
        date = str(meta_dict['date'])
        title = '%s %s %s %s %s' % (composite, var, sensor, date, resolution)
    return title


def make_preview(file):
    """
    Args:
        file (str): Path to a raster file containing a single layer (usually a geoTiff)
        
    Returns:

    """
    # Retrieve color stretch information of available
    var = OC_filename_parser(file)['variable']
    try:
        stretch = INDICES[var]['stretch']
    except KeyError:
        stretch = {}

    title = make_map_title(file)

    fig_name = os.path.splitext(file)[0] + '.png'

    # Handle both L3m tif and nc files
    if file.endswith('.tif'):
        with rasterio.open(file) as src:
            meta = src.meta
            data = src.read(1, masked=True)
    elif file.endswith('.nc'):
        meta = geo_dict_from_nc(file)
        # Read array
        with nc.Dataset(file) as src:
            data = src.variables[var][:]

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
    if INDICES[var]['log']:
        m.imshow(data[::5,::5], origin='upper', extent = extent, interpolation = "none", norm=LogNorm(**stretch), cmap = 'jet')
    else:
        m.imshow(data[::5,::5], origin='upper', extent = extent, interpolation = "none", cmap = 'jet', **stretch)
    m.colorbar()
    # fill continents, set lake color same as ocean color.
    m.fillcontinents(color='grey',lake_color='black')
    # draw parallels and meridians.
    parallels = np.arange(0.,81,5.)
    meridians = np.arange(10.,351.,5.)
    # labels = [left,right,top,bottom]
    m.drawparallels(parallels,labels=[True,False,False,False])
    m.drawmeridians(meridians,labels=[False,False,False,True])
    plt.title(title)
    plt.savefig(fig_name, dpi=100, transparent=True)




