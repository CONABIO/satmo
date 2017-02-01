import netCDF4 as nc
import numpy as np
import rasterio
from .geo import geo_dict_from_nc

def nc2tif(file, var):
    """Generate geotiff from L3m netcdf array

    Reads an existing array from a netcdf file and writes it
    with georeference as tif

    Args:
        file (str): Path to the netcdf file containing the desired array
        var (str): Variable name to read

    Returns:
        The function is used for its side effect of writing a geotiff on
        disk.
        The function also returns the file name of the produced file
    """
    # Generate output file name

    # Get geo dict

    # Read array

    # Update geo_dict

    # Write file

    # Return output filename