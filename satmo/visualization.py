import warnings
import cartopy.crs as ccrs
import cartopy.feature as cfeature
# Silence a warning that is in fact caused by a bug in this version of cartopy
# https://github.com/SciTools/cartopy/issues/839
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import matplotlib.ticker as mticker
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

from .global_variables import SENSOR_CODES, COMPOSITES, VIZ_PARAMS
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
        Filename of the png file created

    """
    # Retrieve color stretch information of available
    var = OC_filename_parser(file)['variable']
    try:
        stretch = VIZ_PARAMS[var]['stretch']
        log = VIZ_PARAMS[var]['log']
        cmap = VIZ_PARAMS[var]['cmap']
    except KeyError:
        stretch = {}
        log = False
        cmap = 'jet'

    title = make_map_title(file)

    fig_name = os.path.splitext(file)[0] + '.png'

    # IMport continent
    continent = cfeature.NaturalEarthFeature(category='cultural',
                                             name='admin_0_countries',
                                             scale='50m')

    with rasterio.open(file) as src:
        meta = src.meta
        data = src.read(1, masked=True)
        bounds = src.bounds

    # Create figure
    fig = plt.figure(figsize = (12, 8))

    crs = ccrs.PlateCarree()
    extent = (bounds.left, bounds.right, bounds.bottom, bounds.top)

    ax = plt.axes(projection=crs)
    ax.background_patch.set_facecolor('darkgrey')
    plt.title(title, fontsize=15, weight='bold')
    if log:
        plt.imshow(data, origin='upper', extent=extent, transform=crs,
                   interpolation = "none", norm=LogNorm(**stretch), cmap = cmap, zorder=3)
    else:
        plt.imshow(data, origin='upper', extent=extent, transform=crs,
                   interpolation = "none", cmap = cmap, zorder=3, **stretch)
    ax.add_feature(continent, facecolor='grey', edgecolor='black', zorder=4)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), color='black', linestyle='dotted',
                      draw_labels=True, zorder=7)
    gl.xlabels_top = False
    gl.ylabels_right = False
    gl.ylocator = mticker.FixedLocator(np.arange(0.,81.,5.))
    gl.xlocator = mticker.FixedLocator(np.arange(-170.,171.,5.))
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'size': 15, 'color': 'black'}
    gl.ylabel_style = {'size': 15, 'color': 'black'}

    cbar = plt.colorbar(fraction=0.025)
    cbar.ax.tick_params(labelsize=20)
    plt.savefig(fig_name, dpi=300, transparent=True)
    plt.close(fig)
    return fig_name


