import os
from glob import glob

import numpy as np
import numpy.ma as ma

import netCDF4 as nc
import rasterio
from rasterio.crs import CRS
from pyproj import Proj
from affine import Affine

from .geo import geo_dict_from_nc, get_raster_meta
from .utils import OC_filename_parser, OC_file_finder, is_day

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
        self.composed_array = np.nanmean(ma.array(self.array_list), axis=0)
    def median(self):
        self.composed_array = np.nanmedian(ma.array(self.array_list), axis=0)
    def max(self):
        self.composed_array = np.nanmax(ma.array(self.array_list), axis=0)
    def min(self):
        self.composed_array = np.nanmin(ma.array(self.array_list), axis=0)

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

        Note:
            The 'masked' part has been removed when input is a geotiff (most
            likely produced by the binning function), rasterio reads cells flagged as
            nodata as np.nan in a geotiff by default.

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
                array = src.read(1)
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

    def to_scidb(self):
        pass


class BasicBinMap(object):
    """ Class to produce daily gridded data for a given date/variable from L2 files

    The class is instantiated with a list of L2 files. The methods give the option to
        processed new variables from reflectance layers present in the L2 file, extract an existing
        one, mask the invalid observations and bin the resulting cleaned variable to a regular grid.
        All the methods of this class are exposed in the L3mProcess class so
        that there shouldn't be any need to use this class directly.

    Args:
        file_list (list): List of L2 files (they should all belong to the same collection/day/etc)
        var (str): Optional name of variable to bin. Use when bining a variable that is already present in the archive

    Attributes:
        file_list: list of strings (the pathnames of individual L2 files)
        lon_dd: 1D Np array containing longitude coordinates
        lat_dd: 1D Np array containing latitude coordinates
        flag_array: 1D np array containing flag values
        var_array: 1D np array containing variable to bin
        output_array: a 2D np array containing binned variable
        geo_dict: A dictionary used to write the output_array using rasterio

    Exemples:
        >>> import satmo

        >>> # Instantiate class using factory classmethod
        >>> bin_class = satmo.BasicBinMap.from_sensor_date('A', date = '2016-01-01', day = True, suite = 'OC',
                                                           data_root = '/home/ldutrieux/sandbox/satmo2_data',
                                                           var = 'chlor_a')
        >>> # Apply mask with default parameters
        >>> bin_class.apply_mask()

        >>> # Bin the data to a 2 km resolution grid in a chosen resolution and extent
        >>> bin_class.bin_to_grid(south = 3, north = 33, west = -122, east = -72,
                                  resolution = 2000, proj4string = "+proj=laea +lat_0=20 +lon_0=-100")

        >>> # Write grid with binned data to a georeferenced file
        >>> bin_class.to_file('/home/ldutrieux/sandbox/satmo2_data/aqua/L3m/DAY/2016/001/A2016001.L3m_DAY_CHL_chlor_a_2km.tif')
    """
    def __init__(self, file_list, var = None):
        self.file_list = file_list
        self.lon_dd = np.array([])
        self.lat_dd = np.array([])
        self.flag_array = np.array([])
        self.var_array = None
        self.output_array = None
        self.geo_dict = None
        for file in self.file_list:
            self.lon_dd = np.append(self.lon_dd, self._get_lon(file))
            self.lat_dd = np.append(self.lat_dd, self._get_lat(file))
            self.flag_array = np.append(self.flag_array, self._read_band(file, 'l2_flags'))
        self.flag_array = np.uint32(self.flag_array)
        if var is not None:
            var_array = np.array([])
            for file in file_list:
                var_array = np.append(var_array, self._read_band(file, var))
                self.var_array = var_array

    @classmethod
    def from_sensor_date(cls, sensor_code, date, day, suite, data_root, var = None):
        """Alternative class buider that builds automatically the right file list

        Args:
            sensor_code (str): Sensor code (e.g. 'A', 'T', 'V') of the files to query.
            date (str or datetime): Date of the data to find
            day (bool): Are we looking for day data
            suite (str): L2 suite of input files (e.g. OC, SST, SST4, SST3)
            data_root (str): Root of the data archive
            var (str): Optional name of variable to bin. Use when bining a variable that is already present in the archive
        """
        file_list = OC_file_finder(data_root, date, level = 'L2', suite = suite, sensor_code = sensor_code)
        file_list = [x for x in file_list if is_day(x) == day]
        if len(file_list) == 0:
            raise IOError('No L2 files found')
        bin_class = cls(file_list, var)
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
    def _read_band_all(self, var):
        """Utility to read a variable as a flattened numpy array from all files
            contained in self.file_list

        Args:
            var (str): Name of a variable present in all the netcdf files of
                self.file_list

        Return:
            np.array: A flattened numpy array
        """
        out = np.array([])
        for file in self.file_list:
            out = np.append(out, self._read_band(file, var))
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
            lat = src.groups['navigation_data'].variables['latitude'][:].flatten()
        return lat

    def set_variable(self, x):
        """Setter for variable to bin

        Args:
            x (np.array): A flattened numpy array that should match with the self.lon_dd
                self.lat_dd, self.flags_array
        """
        if x.shape != self.lat_dd.shape:
            raise ValueError('Dimension missmatch')
        self.var_array = x

    def apply_mask(self, bit_mask = 0x0669D73B):
        """Method to mask data using information from the flag array

        Args:
            bit_mask (int): The mask to use for selecting active flags from the flag array
                The array is coded bitwise so that the mask has to be built as a bit mask too.
                It's generally more convenient to use hexadecimal to define the mask, for example
                if you want to activate flags 0, 3 and 5, you can pass 0x29 (0010 1001).
                The mask defaults to 0x0669D73B, which is the defaults value for seadas l2bin.

        Details:
            Below the table of flag signification for modis, viirs and seawifs

            | Flag Name Modis/viirs | Flag Name Seawifs | Bit number |
            |=======================|===================|============|
            | ATMFAIL               | ATMFAIL           |          0 |
            | LAND                  | LAND              |          1 |
            | PRODWARN              | PRODWARN          |          2 |
            | HIGLINT               | HIGLINT           |          3 |
            | HILT                  | HILT              |          4 |
            | HISATZEN              | HISATZEN          |          5 |
            | COASTZ                | COASTZ            |          6 |
            | SPARE                 | SPARE             |          7 |
            | STRAYLIGHT            | STRAYLIGHT        |          8 |
            | CLDICE                | CLDICE            |          9 |
            | COCCOLITH             | COCCOLITH         |         10 |
            | TURBIDW               | TURBIDW           |         11 |
            | HISOLZEN              | HISOLZEN          |         12 |
            | SPARE                 | SPARE             |         13 |
            | LOWLW                 | LOWLW             |         14 |
            | CHLFAIL               | CHLFAIL           |         15 |
            | NAVWARN               | NAVWARN           |         16 |
            | ABSAER                | ABSAER            |         17 |
            | SPARE                 | SPARE             |         18 |
            | MAXAERITER            | MAXAERITER        |         19 |
            | MODGLINT              | MODGLINT          |         20 |
            | CHLWARN               | CHLWARN           |         21 |
            | ATMWARN               | ATMWARN           |         22 |
            | SPARE                 | SPARE             |         23 |
            | SEAICE                | SEAICE            |         24 |
            | NAVFAIL               | NAVFAIL           |         25 |
            | FILTER                | FILTER            |         26 |
            | SPARE                 | SPARE             |         27 |
            | BOWTIEDEL             | SPARE             |         28 |
            | HIPOL                 | HIPOL             |         29 |
            | PRODFAIL              | PRODFAIL          |         30 |
            | SPARE                 | SPARE             |         31 |

            Default l2bin mask values for:
                General: 0x669d73b (includes Chlorophyl algorithms, Rrs, etc)
                FLH: 0x679d73f
                PAR: 0x600000a
                SST: 0x1002
                NSST/SST4: 0x2


        """
        if self.var_array is None:
            raise ValueError('A variable needs to be set or selected before masking')
        # Create mask
        mask_array = np.bitwise_and(self.flag_array, np.array([bit_mask])) == 0
        # Apply mask to various arrays
        self.var_array = self.var_array[mask_array]
        self.lon_dd = self.lon_dd[mask_array]
        self.lat_dd = self.lat_dd[mask_array]

    def bin_to_grid(self, south, north, west, east, resolution, proj4string):
        """Method for binning data to a defined grid

        A grid is defined by its extent (north, south, east, west), resolution, and
            projection (proj4string).

        Args:
            south (float): Southern border of output extent (in DD)
            north (float): Northern border of output extent (in DD)
            west (float): Western border of output extent (in DD)
            east (float): Eastern border of output extent (in DD)
            resolution (float): Output resolution (in the unit of the output coordinate reference system)
            proj4string (str): Coordinate reference system of the output in proj4 format

        """
        p = Proj(proj4string)

        # Find output corner coordinates in bining grid CRS
        # Note that this does not account for the extent deformation induced by the projection
        top_left = p(west, north)
        bottom_right = p(east, south)

        # Define output array shape
        destination_shape = ( int( abs(top_left[1] - bottom_right[1]) / float(resolution)), int( abs(top_left[0] - bottom_right[0]) / float(resolution)) )
        # Define affine transform and the inverse transform
        aff = Affine(resolution, 0.0, top_left[0], 0.0, -resolution, top_left[1])
        ffa = ~aff

        # Convert the lat and lon arrays to projected coordinates
        lon_proj, lat_proj = p(self.lon_dd, self.lat_dd)

        # Convert projected coordinates to destination array indices
        destination_ids = ffa * (lon_proj, lat_proj)

        # Perform 2d data binning (to average all input coordinates falling withing the same outut pixel)
        # 1 Sum up within each bin
        dst_array, _, _ = np.histogram2d(destination_ids[1], destination_ids[0], bins=(range(0, destination_shape[0] + 1, 1), range(0, destination_shape[1] + 1, 1)), weights=self.var_array, normed=False)
        # Retrieve count per bin
        counts, _, _ = np.histogram2d(destination_ids[1], destination_ids[0], bins=(range(0, destination_shape[0] + 1, 1), range(0, destination_shape[1] + 1, 1)))
        # Compute average value per bin
        dst_array = dst_array / counts
        # Replace zeros by a more appropriate no data value (-1 since we are
        # writing to float and most values are between 0 and 1)
        dst_array[dst_array == 0] = -1
        dst_array = np.ma.masked_invalid(dst_array)
        # Write array to slot
        self.output_array = dst_array
        # Build geodict and write it to a slot of the object
        geo_dict = {'crs': CRS.from_string(proj4string),
                    'affine': aff,
                    'height': destination_shape[0],
                    'width': destination_shape[1],
                    'driver': u'GTiff',
                    'dtype': rasterio.float32,
                    'count': 1,
                    'compress':'lzw',
                    'nodata': -1}

        self.geo_dict = geo_dict

    def to_file(self, filename):
        """Writes a binned grid to a georeferenced tif file

        Args:
            filename (str): Name of a tif file to write the frid to

        """
        if self.output_array is None or self.geo_dict is None:
            raise ValueError('The class does not contain the binned array \
                             and/or the geo_dict, You probably have to run the \
                             bin_to_grid method')
        with rasterio.open(filename, 'w', **self.geo_dict) as dst:
            dst.write_band(1, self.output_array.astype(rasterio.float32))

    def to_scidb(self):
        pass



class L3mProcess(BasicBinMap):
    """Class to put the functions to compute, inherits from BasicBinMap so that
        computing a new variable from reflectance bands is an optional step before
        binning

    Example:
        >>> import satmo
        >>> import numpy as np

        >>> # Instantiate class using factory classmethod
        >>> bin_class = satmo.L3mProcess.from_sensor_date('A', date = '2016-01-01', day = True, suite = 'OC',
                                                           data_root = '/home/ldutrieux/sandbox/satmo2_data')

        >>> # Compute a new variable using the calc method
        >>> def add_bands(x, y):
        >>>     return np.add(x, y)

        >>> bin_class.calc(['Rrs_555', 'Rrs_645'], add_bands)

        >>> # Apply mask with default parameters
        >>> bin_class.apply_mask()

        >>> # Bin the data to a 2 km resolution grid in a chosen resolution and extent
        >>> bin_class.bin_to_grid(south = 3, north = 33, west = -122, east = -72,
                                  resolution = 2000, proj4string = "+proj=laea +lat_0=20 +lon_0=-100")

        >>> # Write grid with binned data to a georeferenced file
        >>> bin_class.to_file('/home/ldutrieux/sandbox/satmo2_data/aqua/L3m/DAY/2016/001/A2016001.L3m_DAY_CHL_chlor_a_2km.tif')
    """
    def __init__(self, file_list, var = None):
        super(L3mProcess, self).__init__(file_list, var)

    def calc(self, band_list, fun):
        """Generic band math method

        Applies an abitrary function to a set of arrays present in the netcdf
        file.

        Args:
            band_list (list): A list of bands/variables present in the file
                (e.g.: ['Rrs_555', 'Rrs_645'])
            fun (function): A function that takes len(band_list) arguments (all
            them must be numpy array of the same dimension) performs some
            element wise calculation on them and returns a single numpy array
            with the same dimension than each input array.
        """
        # Read the bands from band_list with a list comprehension
        array_list = [self._read_band_all(x) for x in band_list]
        # Pass the list of numpy arrays as *args to fun
        out_array = fun(*array_list)
        self.set_variable(out_array)
