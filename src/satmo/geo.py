import pyproj
from affine import Affine
from rasterio.crs import CRS
import netCDF4 as nc


def geo_dict_from_nc(nc_file, proj4string = None):
    """Retrieves the georeferencing parameters from a netcdf file produced with l3mapgen

    Details:
        See https://oceancolor.gsfc.nasa.gov/forum/oceancolor/topic_show.pl?tid=6429
        for justification of the approach used in this function to retrieve the projected
        extent.

    Args:
        nc_file (str): Path to netcdf file
        proj4string (str): Optional. proj4string previously passed to l3mapgen (projection=)
            retrieved from the file metadata if not provided

    Return:
        Dictionary with georeferencing parameters

    Exmaples:
        Given a netcdf file produced with:
        $l3mapgen ifile=T2016292.L3b_DAY_OC ofile=T2016292.L3B_DAY_RRS_laea.nc resolution=1km south=26 north=40 west=-155 east=-140 projection="+proj=laea +lat_0=33 +lon_0=-147" 
        
        >>> import rasterio
        >>> from pprint import pprint
        >>>
        >>> geo_dict = geo_dict_from_nc('T2016292.L3B_DAY_RRS_laea.nc', "+proj=laea +lat_0=33 +lon_0=-147")
        >>> pprint(geo_dict)
        {'affine': Affine(1160.0, 0.0, -800596.8665952191,
               0.0, -1160.0, -746017.3077247943),
         'crs': CRS({'lon_0': -147, 'proj': 'laea', 'lat_0': 33}),
         'height': 1361,
         'width': 1295}
        >>> geo_dict.update(driver = u'GTiff', dtype = rasterio.float32, count = 1, nodata = -32767)
        >>>
        >>> import numpy as np
        >>>
        >>> nc_con = nc.Dataset(file_path)
        >>> rrs_555 = nc_con.variables['Rrs_555'][:]
        >>> nc_con.close()
        >>>
        >>> with rasterio.open('rrs_555.tif', 'w', **geo_dict) as dst:
        >>>     dst.write_band(1, rrs_555.astype(rasterio.float32))
    """
    with nc.Dataset(nc_file) as src:
        res = src.geospatial_lon_resolution
        height = src.number_of_lines
        width = src.number_of_columns
        if proj4string is None:
            proj4string = src.map_projection
        # Dictionary representation of proj4string
        crs = CRS.from_string(proj4string)
        # sw longlat extent will be used to retrieve xmin
        sw_ll = (src.westernmost_longitude, src.southernmost_latitude)
        # Southest point of the projected extent should be at lon_0 (crs definition)/southernmost_latitude
        # It is used to retrieve ymin
        south_center_ll = (crs['lon_0'], src.southernmost_latitude)
    # Define pyproj transformation object
    p = pyproj.Proj(proj4string)
    # Convert coordinate pairs to projected CRS
    x_min, y_dummy = p(*sw_ll)
    x_dummy, y_min = p(*south_center_ll)
    y_max = y_min + height * res
    # Build geo dict
    geo_dict = {'affine': Affine(res, 0.0, x_min,
                                 0.0, -res, y_max),
                'height': height,
                'width': width,
                'crs': crs}
    return geo_dict

