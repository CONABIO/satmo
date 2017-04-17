import os
import netCDF4 as nc
import numpy as np
import numpy.ma as ma
import rasterio
from .geo import geo_dict_from_nc, get_raster_meta
from .utils import OC_filename_parser

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
    var = OC_filename_parser(file)['variable']
    # Read array
    with nc.Dataset(file) as src:
        dtype = str(src.variables[var].dtype)
        nodata = src.variables[var]._FillValue
        array = src.variables[var][:]
    # Update geo_dict
    # TODO: Check if dtype and nodata are constant across products, otherwise retrieve from nc metadata
    geo_dict.update(driver = u'GTiff', dtype = dtype, count = 1, nodata = nodata, compress='lzw')
    # Write file
    with rasterio.open(file_out, 'w', **geo_dict) as dst:
        dst.write_band(1, array.astype(dtype))
    # Return output filename
    return file_out


class Composer(object):
    """Compose arrays with min, max, median, max
    For inheritance only, not exported to package __init__"""
    def __init__(self, *args):
        """Instantiate Composer class

        Args:
            *args: numpy arrays (typically 2D) of similar shape
        """
        self.array_list = args
        self.composed_array = None
    def mean(self):
        self.composed_array = np.mean(ma.array(self.array_list), axis=0)
    def median(self):
        self.composed_array = np.median(ma.array(self.array_list), axis=0)
    def max(self):
        self.composed_array = np.amax(ma.array(self.array_list), axis=0)
    def min(self):
        self.composed_array = np.amin(ma.array(self.array_list), axis=0)

# Compose time 

class FileComposer(Composer):
    """Class to compose multiple raster files into one (with methods inherited
    from the Composer class), and write the output to a file

    Details:
        Typically designed to produce composites from L3m files.
        Can be used with single band geoTiff or single band netcdf files

    Example usage:
        >>> import satmo
        >>> file1 = 'aqua/L2/2015/001/A2015001.L3m_DAY_CHL_chlor_a_1km.tif'
        >>> file2 = 'terra/L2/2015/001/T2015001.L3m_DAY_CHL_chlor_a_1km.tif'
        >>> file3 = 'viirs/L2/2015/001/V2015001.L3m_DAY_CHL_chlor_a_1km.tif'
        >>> compose_class = satmo.FileComposer(file1, file2, file3)
        >>> compose_class.mean()
        >>> compose_class.to_file('combined/X2015001.L3m_DAY_CHL_chlor_a_1km_2.tif')
    """
    def _read_masked_array(self, file):
        """Util function to read a single layer raster file as masked np array

        Args:
            file (str): Input file name
        """
        _, ext = os.path.splitext(file)
        if ext == '.nc':
            var = OC_filename_parser(file)['variable']
            # Read array
            with nc.Dataset(file) as src:
                array = src.variables[var][:]
        else:
            with rasterio.open(file) as src:
                array = src.read(1, masked=True)
        return array

    def __init__(self, *args):
        """Instantiate FileComposer class

        Args:
            *args: Filenames pointing to raster files
        """
        self.file_list = args
        self.meta = get_raster_meta(args[0])
        array_list = [self._read_masked_array(x) for x in args]
        super(FileComposer, self).__init__(*array_list)
        
    def to_file(self, filename):
        """Write the composed array to file

        Args:
            filename (str): Name of file to which array has to be written
        """
        # One of the method of the child class must have been ran before
        # running this method
        with rasterio.open(filename, 'w', **self.meta) as dst:
            dst.write(self.composed_array.astype(self.meta['dtype']), 1)
        return filename


import netCDF4 as nc
import numpy as np
from pyproj import Proj
from affine import Affine
import rasterio
from rasterio.crs import CRS

from glob import glob
from math import floor

class BasicBinMap(object):
    """ Class to produce daily gridded data for a given date/variable from L2 files

    The class is instantiated with a list of L2 files. The methods give the option to
        processed new variables from reflectance layers present in the L2 file, extract an existing
        one, mask the invalid observations and bin the resulting cleaned variable to a regular grid.
    
    Args:
        file_list (list): List of L2 files (they should all belong to the same collection/day/etc)
        var (str): Optional name of variable to bin. Use when bining a variable that is already present in the archive

    Attributes:
        file_list: list of strings (the pathnames of individual L2 files)
        lon_dd: 1D Np array containing longitude coordinates
        lat_dd: 1D Np array containing latitude coordinates
        flag_array: 1D np array containing flag values
        var_array: 1D np array containing variable to bin
        

    """
    def __init__(self, file_list, var = None):
        self.file_list = file_list
        self.lon_dd = np.array([])
        self.lat_dd = np.array([])
        self.flag_array = np.array([])
        self.var_array = None
        for file in self.file_list:
            self.lon_dd = np.append(self.lon_dd, _get_lon(file))
            self.lat_dd = np.append(self.lat_dd, _get_lat(file))
            self.flag_array = np.append(self.flag_array, _read_band(file, 'l2_flags'))
        if var is not None:
            var_array = np.array([])
            for file in file_list:
                var_array = np.append(var_array, _read_band(file, var))
                set_variable(var_array)

    @classmethod
    def from_sensor_date(cls, sensor_code, date, day, suite, data_root):
        """Alternative class buider that builds automatically the right file list

        Args:
            sensor_code (str): Sensor code (e.g. 'A', 'T', 'V') of the files to query. 
            date (str or datetime): Date of the data to find
            day (bool): Are we looking for day data
            suite (str): L2 suite of input files (e.g. OC, SST, SST4, SST3)
            data_root (str): Root of the data archive
        """
        file_list = OC_file_finder(data_root, date, level = 'L2', suite = suite, sensor_code = sensor_code)
        file_list = [x for x in file_list if is_day == day]
        bin_class = cls(file_list)
        return bin_class 

    def _read_band(self, file, var):
        """Internal function to read a band as a numpy array
            
        Args:
            file (str): File name to read the variable from
            var (str): Name of the variable/band to read

        Returns:
            Numpy.array: Flattened numpy array
        """
        with nc.Dataset(file) as src:
            out = src.groups['geophysical_data'].variables[var][:].flatten()
        return out

    def _get_lon(self, file):
        """Internal function to retrieve geolocation arrays from a L2 file

        Args:
            file (str): File name to read the variable from
            
        Return:
            np.array: flattened numpy arrays representing long
        """
        with nc.Dataset(file) as src:
            lon = src.groups['navigation_data'].variables['longitude'][:].flatten()
        return lon

    def _get_lat(self, file):
        """Internal function to retrieve geolocation arrays from a L2 file

        Args:
            file (str): File name to read the variable from
            
        Return:
            np.array: flattened numpy arrays representing lat
        """
        with nc.Dataset(file) as src:
            lat = src.groups['navigation_data'].variables['longitude'][:].flatten()
        return lat
    
    def set_variable(self, x):
        """Setter for variable to bin 
        
        Args:
            x (np.array): A flattened numpy array that should match with the self.lon_dd
                self.lat_dd, self.flags_array
        """
        if x.shape != self.lat_dd:
            raise ValueError('Dimension missmatch')
        self.var_array = x

    def apply_mask(self, bit_mask):
        if self.var_array is None:
            raise ValueError('A variable needs to be set or selected before masking')
        

 
class Process(BasicBinMap):
    """Class to put the functions to compute, inherits from BasicBinMap so that
        computing a new variable from reflectance bands is an optional step before
        binning
    """
    def __init__():
        pass
