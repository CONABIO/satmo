import os
import netCDF4 as nc
import numpy as np
import numpy.ma as ma
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

def compose_mean(filename, *args):
    """Mean value compositing function

    Takes n input raster files (geotiff), computes a mean value composite
    and writes the result back to file.
    Shape and extent of all input files should match perfectly

    Args:
        filename (str): Output file name
        *args (str): Input file names

    Returns:
        In addition to writing a file to disk the function returns the
        output filename
    """
    # Define reading function to use in list comprehension
    def read_masked_array(file):
        with rasterio.open(file) as src:
            array = src.read(1, masked=True)
            return array
    # Get meta to use for output array
    with rasterio.open(args[0]) as src:
        meta = src.meta
    # Get list of masked arrays
    array_list = [read_masked_array(x) for x in args]
    # Reduce
    array_out = np.mean(ma.array(array_list), axis=0)
    # Write to file
    with rasterio.open(filename, 'w', **meta) as dst:
        dst.write(array_out.astype(meta['dtype']), 1)
    return filename