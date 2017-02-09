import os
import netCDF4 as nc
import numpy as np
import rasterio
from .geo import geo_dict_from_nc
from .visualization import get_var_name

def nc2tif(file, proj4string = None):
    """Generate geotiff from L3m netcdf array

    Reads an existing array from a netcdf file and writes it
    with georeference as tif

    Args:
        file (str): Path to the netcdf file containing the desired array
        proj4string (str): Coordinate reference system (opional, see geo_dict_from_nc)

    Returns:
        The function is used for its side effect of writing a geotiff on
        disk.
        The function also returns the file name of the produced file
    """
    # Generate output file name
    # l3m nc products should only contain one variable, so that simply changing extension should suffice
    base = os.path.splitext(file)[0]
    file_out = base + ".tif"
    # Get geo dict
    geo_dict = geo_dict_from_nc(file, proj4string)
    # Retrieve var name from file name
    var = get_var_name(file)
    # Read array
    with nc.Dataset(file) as src:
        dtype = src.variables[var].dtype
        nodata = src.variables[var]._FillValue
        array = src.variables[var][:]
    # Update geo_dict
    # TODO: Check if dtype and nodata are constant across products, otherwise retrieve from nc metadata
    geo_dict.update(driver = u'GTiff', dtype = dtype, count = 1, nodata = nodata, compress='lzw')
    # Write file
    with rasterio.open(file_out, 'w', **geo_dict) as dst:
        dst.write_band(1, array.astype(rasterio.float32))
    # Return output filename
    return file_out