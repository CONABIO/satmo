import pyproj
import affine
import netCDF4 as nc

def geo_dict_from_nc(nc_file, proj4string):
    """Retrieves the georeferencing parameters from a netcdf file produced with l3mapgen

    Args:
        nc_file (str): Path to netcdf file
        proj4string (str): proj4string previously passed to l3mapgen (projection=)

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
    con = nc.Dataset(nc_file)
    res = float(con.spatialResolution[:-2]) * 1000
    height = con.number_of_lines
    width = con.number_of_columns
    lon_0 = con.sw_point_longitude
    lat_0 = con.sw_point_latitude
    # close connection
    con.close()
    # Setup pyproj object
    p = pyproj.Proj(proj4string)
    sw_coords = p(lon_0, lat_0)
    nw_coords = (sw_coords[0], sw_coords[1] + height * res)
    # make geotransform
    geot = affine.Affine.from_gdal(nw_coords[0], res, 0, nw_coords[1], 0, -res)
    out_dict = {'affine': geot,
                'height': height,
                'width': width}
    try:
        from rasterio.crs import CRS
        crs = CRS.from_string(proj4string)
    except ImportError:
        crs = proj4string
    out_dict.update({'crs': crs})
    return out_dict

