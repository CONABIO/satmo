import os
from glob import glob
import subprocess
import random

import numpy as np
import numpy.ma as ma

import netCDF4 as nc
import rasterio
from rasterio.crs import CRS
from pyproj import Proj
from affine import Affine

from .geo import geo_dict_from_nc, get_raster_meta
from .utils import (filename_parser, file_finder, is_day,
                    filename_builder, to_km)
from .visualization import make_preview
from .errors import SeadasError
from .global_variables import (L3_SUITE_FROM_VAR, QUAL_ARRAY_NAME_FROM_SUITE,
                               STANDARD_L3_SUITES, FLAGS)

def nc2tif(file, proj4string = None):
    """Generate geotiff from L3m netcdf array

    Reads an existing array from a netcdf file and writes it
    with georeference as tiff

    Args:
        file (str): Path to the netcdf file containing the desired array
        proj4string (str): Coordinate reference system (optional, see geo_dict_from_nc)

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
    var = filename_parser(file)['variable']
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
        self.compositing_function = None
    def mean(self):
        self.composed_array = np.nanmean(ma.array(self.array_list), axis=0)
        self.compositing_function = 'mean'
    def median(self):
        self.composed_array = np.nanmedian(ma.array(self.array_list), axis=0)
        self.compositing_function = 'median'
    def max(self):
        self.composed_array = np.nanmax(ma.array(self.array_list), axis=0)
        self.compositing_function = 'max'
    def min(self):
        self.composed_array = np.nanmin(ma.array(self.array_list), axis=0)
        self.compositing_function = 'min'

# Compose time 

class FileComposer(Composer):
    """Class to compose multiple raster files into one (with methods inherited
    from the Composer class), and write the output to a file


    Typically designed to produce composites from L3m files.
    Can be used with single band geoTiff or single band netcdf files

    Examples:
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

        The 'masked' part has been removed when input is a geotiff (most
        likely produced by the binning function), rasterio reads cells flagged as
        nodata as np.nan in a geotiff by default.

        Args:
            file (str): Input file name
        """
        _, ext = os.path.splitext(file)
        if ext == '.nc':
            var = filename_parser(file)['variable']
            # Read array
            with nc.Dataset(file) as src:
                array = src.variables[var][:]
        else:
            with rasterio.open(file) as src:
                array = src.read(1)
        return array

    # TODO: Test function below
    def _read_compositing_meta(self, file):
        """Read the COMPOSITING_META tag of the input files

        Because input of the compositing method may be composites too, the idea
        enable propagation of these compositing metadata.

        Args:
            file (str): Input file name
        """
        try:
            with rasterio.open(file) as src:
                composite_meta = src.tags(ns='COMPOSITING_META')
        except:
            composite_meta = {}
        return composite_meta

    def __init__(self, *args):
        """Instantiate FileComposer class

        Args:
            *args: Filenames pointing to raster files
        """
        self.file_list = args
        self.meta = get_raster_meta(args[0])
        # Get compositing metadata contained in input files, if there are none
        # it returns an empty dictionary
        self.compositing_meta = {key: self._read_compositing_meta(key) for key in\
                                 self.file_list if\
                                 self._read_compositing_meta(key)}
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
            dst.update_tags(ns='COMPOSITING_META',
                            compositing_function=self.compositing_function,
                            input_files=[os.path.basename(x) for x in self.file_list],
                           input_meta=self.compositing_meta)
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
        qual_array (str): Name of the quality array (named qual_prod in l2bin documentation)
            Used in a later filtering step by the apply_mask method. Mostly used for sst and nsst products.
            Defaults to None.
        var (str): Optional name of variable to bin. Use when binning a variable that is already present in the archive

    Attributes:
        file_list (list): list of strings (the pathnames of individual L2 files)
        lon_dd (np.array): 1D Np array containing longitude coordinates
        lat_dd (np.array): 1D Np array containing latitude coordinates
        flag_array (np.array): 1D np array containing flag values
        qual_array (np.array): 1D np array containing pixel quality information (higher values
            mean lower quality)
        var_array (np.array): 1D np array containing variable to bin
        output_array (np.array): a 2D np array containing binned variable
        geo_dict (dict): A dictionary used to write the output_array using rasterio

    Examples:
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
    def __init__(self, file_list, qual_array = None, var = None):
        self.file_list = file_list
        self.lon_dd = np.array([])
        self.lat_dd = np.array([])
        self.flag_array = np.array([])
        self.qual_array = np.array([])
        self.var_array = None
        self.output_array = None
        self.geo_dict = None
        for file in self.file_list:
            self.lon_dd = np.append(self.lon_dd, self._get_lon(file))
            self.lat_dd = np.append(self.lat_dd, self._get_lat(file))
            self.flag_array = np.append(self.flag_array, self._read_band(file, 'l2_flags'))
            # Read using the same logic the qual_array if its name is given
            if qual_array is not None:
                self.qual_array = np.append(self.qual_array, self._read_band(file, qual_array))
        self.flag_array = np.uint32(self.flag_array)
        if var is not None:
            var_array = np.array([])
            for file in file_list:
                var_array = np.append(var_array, self._read_band(file, var))
                self.var_array = var_array

    @classmethod
    def from_sensor_date(cls, sensor_code, date, day, suite, data_root,
                         qual_array = None, var = None):
        """Alternative class buider that builds automatically the right file list

        Args:
            sensor_code (str): Sensor code (e.g. 'A', 'T', 'V') of the files to query.
            date (str or datetime): Date of the data to find
            day (bool): Are we looking for day data
            suite (str): L2 suite of input files (e.g. OC, SST, SST4, SST3)
            data_root (str): Root of the data archive
            qual_array (str): Name of the quality array (named qual_prod in l2bin documentation)
                Used in a later filtering step by the apply_mask method. Mostly used for sst and nsst products.
                Defaults to None.
            var (str): Optional name of variable to bin. Use when binning a variable that is already present in the archive
        """
        file_list = file_finder(data_root, date, level = 'L2', suite = suite, sensor_code = sensor_code)
        file_list = [x for x in file_list if is_day(x) == day]
        if len(file_list) == 0:
            raise IOError('No L2 files found')
        bin_class = cls(file_list, qual_array, var)
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
        """Utility to read a variable as a flattened numpy array from all files contained in self.file_list

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

    def apply_mask(self, bit_mask = 0x0669D73B, max_qual = 2):
        """Method to mask data using information from the flag array. And optionally the mask array (named qual_prod in l2bin documentation)

        Args:
            bit_mask (int): The mask to use for selecting active flags from the flag array
                The array is coded bitwise so that the mask has to be built as a bit mask too.
                It's generally more convenient to use hexadecimal to define the mask, for example
                if you want to activate flags 0, 3 and 5, you can pass 0x29 (0010 1001).
                The mask defaults to 0x0669D73B, which is the defaults value for seadas l2bin.
            max_qual (int): Maximum quality value of the qual array. Any value higher than
                this value will be used to filter out data. Defaults to 2.
                0, 1, 2 correspond to best, good, acceptable. Any value higher than that is bad
                Only applies if qual_array is not None during the class instantiation.

        Below the table of flag signification for modis, viirs and seawifs

        +-------------------------+---------------------+--------------+
        | Flag Name Modis/viirs   | Flag Name Seawifs   | Bit number   |
        +=========================+=====================+==============+
        | ATMFAIL                 | ATMFAIL             | 0            |
        +-------------------------+---------------------+--------------+
        | LAND                    | LAND                | 1            |
        +-------------------------+---------------------+--------------+
        | PRODWARN                | PRODWARN            | 2            |
        +-------------------------+---------------------+--------------+
        | HIGLINT                 | HIGLINT             | 3            |
        +-------------------------+---------------------+--------------+
        | HILT                    | HILT                | 4            |
        +-------------------------+---------------------+--------------+
        | HISATZEN                | HISATZEN            | 5            |
        +-------------------------+---------------------+--------------+
        | COASTZ                  | COASTZ              | 6            |
        +-------------------------+---------------------+--------------+
        | SPARE                   | SPARE               | 7            |
        +-------------------------+---------------------+--------------+
        | STRAYLIGHT              | STRAYLIGHT          | 8            |
        +-------------------------+---------------------+--------------+
        | CLDICE                  | CLDICE              | 9            |
        +-------------------------+---------------------+--------------+
        | COCCOLITH               | COCCOLITH           | 10           |
        +-------------------------+---------------------+--------------+
        | TURBIDW                 | TURBIDW             | 11           |
        +-------------------------+---------------------+--------------+
        | HISOLZEN                | HISOLZEN            | 12           |
        +-------------------------+---------------------+--------------+
        | SPARE                   | SPARE               | 13           |
        +-------------------------+---------------------+--------------+
        | LOWLW                   | LOWLW               | 14           |
        +-------------------------+---------------------+--------------+
        | CHLFAIL                 | CHLFAIL             | 15           |
        +-------------------------+---------------------+--------------+
        | NAVWARN                 | NAVWARN             | 16           |
        +-------------------------+---------------------+--------------+
        | ABSAER                  | ABSAER              | 17           |
        +-------------------------+---------------------+--------------+
        | SPARE                   | SPARE               | 18           |
        +-------------------------+---------------------+--------------+
        | MAXAERITER              | MAXAERITER          | 19           |
        +-------------------------+---------------------+--------------+
        | MODGLINT                | MODGLINT            | 20           |
        +-------------------------+---------------------+--------------+
        | CHLWARN                 | CHLWARN             | 21           |
        +-------------------------+---------------------+--------------+
        | ATMWARN                 | ATMWARN             | 22           |
        +-------------------------+---------------------+--------------+
        | SPARE                   | SPARE               | 23           |
        +-------------------------+---------------------+--------------+
        | SEAICE                  | SEAICE              | 24           |
        +-------------------------+---------------------+--------------+
        | NAVFAIL                 | NAVFAIL             | 25           |
        +-------------------------+---------------------+--------------+
        | FILTER                  | FILTER              | 26           |
        +-------------------------+---------------------+--------------+
        | SPARE                   | SPARE               | 27           |
        +-------------------------+---------------------+--------------+
        | BOWTIEDEL               | SPARE               | 28           |
        +-------------------------+---------------------+--------------+
        | HIPOL                   | HIPOL               | 29           |
        +-------------------------+---------------------+--------------+
        | PRODFAIL                | PRODFAIL            | 30           |
        +-------------------------+---------------------+--------------+
        | SPARE                   | SPARE               | 31           |
        +-------------------------+---------------------+--------------+

        Default l2bin mask values for:

            +----------------------------------------------------+------------+
            | suite                                              | mask value |
            +====================================================+============+
            | General (includes Chlorophyl algorithms, Rrs, etc) | 0x669d73b  |
            +----------------------------------------------------+------------+
            | FLH                                                | 0x679d73f  |
            +----------------------------------------------------+------------+
            | PAR                                                | 0x600000a  |
            +----------------------------------------------------+------------+
            | SST                                                | 0x1002     |
            +----------------------------------------------------+------------+
            | NSST/SST4                                          | 0x2        |
            +----------------------------------------------------+------------+


        """
        if self.var_array is None:
            raise ValueError('A variable needs to be set or selected before masking')
        # Create mask
        mask_array = np.bitwise_and(self.flag_array, np.array([bit_mask])) == 0
        # if qual_array exists, create another mask and combine it with mask_array (&)
        if self.qual_array.size:
            qual_mask = self.qual_array <= max_qual
            mask_array = mask_array & qual_mask
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
    """Class to put the functions to compute

    inherits from BasicBinMap so that computing a new variable from reflectance bands is an optional step before
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

        >>> # Write grid with binned data to a geo-referenced file
        >>> bin_class.to_file('/home/ldutrieux/sandbox/satmo2_data/aqua/L3m/DAY/2016/001/A2016001.L3m_DAY_CHL_chlor_a_2km.tif')
    """
    def __init__(self, file_list, qual_array = None, var = None):
        super(L3mProcess, self).__init__(file_list, qual_array, var)

    def calc(self, band_list, fun):
        """Generic band math method

        Applies an arbitrary function to a set of arrays present in the netcdf
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

def l2bin(file_list, L3b_suite, var_list = None, resolution = 1, night = False,
          filename = None, data_root = None, overwrite = False, flags = None):
    """Run l2bin for a list of L2 files

    This is a simple no filter python wrapper around the seadas l2bin utility.

    Args:
        file_list (list): list of L2 files (full paths)
        L3b_suite (str): Product suite to bin (see global variable STANDARD_L3_SUITES
            for corresponding variables)
        var_list (list): Optional list of variables to include in the produced L3b file.
            If None (default but not recommended), a list of standard variables is
            retrieved from the global variable (STANDARD_L3_SUITES)
        resolution (int or str): See resolve argument in l2bin doc
        night (bool): Is that night products
        filename (str): Optional full path of output filename (L3b). If not provided, a
            filename is automatically generated.
        data_root (str): Root of the data archive. Mandatory if filename is not provided
            ignored otherwise
        overwrite (bool): Overwrite file if already exists? Defaults to False
        flags (list): A list of flags to mask invalid data (e.g. ['CLDICE', 'LAND', 'HIGLINT'])
            If None (default), a default list of flag for the L3 suite is fetched from
            the global variable FLAGS

    Returns:
        str: The output filename

    Raises:
        satmo.SeadasError: if the seadas command exists with status 1

    Examples:
        >>> import satmo, glob

        >>> infiles = glob.glob('/home/ldutrieux/sandbox/satmo2_data/aqua/L2/2016/001/*L2*nc')
        >>> satmo.OC_l2bin(infiles, 'CHL', data_root = '/home/ldutrieux/sandbox/satmo2_data')
    """
    input_meta = filename_parser(file_list[0])
    # Generate filename if it hasn't been provided
    if filename is None:
        if data_root is None:
            raise ValueError('data_root argument must be provided if filename is left empty (None)')
        filename = filename_builder(level = 'L3b', full_path = True,
                                       data_root = data_root, suite = L3b_suite,
                                       filename = file_list[0], composite='DAY')
    if flags is None:
        flags = FLAGS[L3b_suite]
    if not (os.path.isfile(filename) and not overwrite):
        L3b_dir = os.path.dirname(filename)
        # Create directory if not already exists
        if not os.path.exists(L3b_dir):
            os.makedirs(L3b_dir)
        # Create text file with input L2 files
        file_list_file = os.path.join(L3b_dir, 'L2_file_list_%d%03d_%d' % \
                                     (input_meta['year'], input_meta['doy'], random.randint(1,9999)))
        with open(file_list_file, 'w') as dst:
            for item in file_list:
                dst.write(item + '\n')
        # Get the standards products from the global variable
        if var_list is None:
            var_list = STANDARD_L3_SUITES[L3b_suite][input_meta['sensor']]
        # BUild l3b command
        l2bin_arg_list = ['l2bin',
                          'l3bprod=%s' % ','.join(var_list),
                          'infile=%s' % file_list_file,
                          'resolve=' + str(resolution),
                          'ofile=%s' % filename,
                          'flaguse=%s' % ','.join(flags),
                          'night=%d' % int(night),
                          'prodtype=regional']
        qual_array = QUAL_ARRAY_NAME_FROM_SUITE[L3b_suite]
        if qual_array is not None:
            l2bin_arg_list.append('qual_prod=%s' % qual_array)
        # Execute command
        with open(os.devnull, 'w') as FNULL:
            # Run cli
            status = subprocess.call(l2bin_arg_list, stdout=FNULL, stderr=subprocess.STDOUT)
        if status == 1:
            raise SeadasError('l2bin exited with status 1')
    return filename

def l3mapgen(x, variable, south, north, west, east, filename = None,
             resolution = 1000, proj = None, data_root = None, composite = 'DAY',
             overwrite = False):
    """Run l3mapgen from a l3b file

    Args:
        x (str): Path to input L3b file
        variable (str): variable to warp (should exist in the L3b file) (e.g.: sst, chlor_a, Rrs_555, ...)
        south (int or float): south latitude of mapped file extent
        north (int or float): north latitude of mapped file extent
        west (int or float): west longitude of mapped file extent
        east (int or float): east longitude of mapped file extent
        filename (str): Optional full path of output filename (L3m). If not provided, a
            filename is automatically generated.
        resolution (int): MApping resolution in meters. Defaults to 1000
        proj (str): Optional proj4 string. If None (default), a lambert Azimutal Equal Area projection (laea), centered
            on the provided extent is used.
        data_root (str): Root of the data archive. Mandatory if filename is not provided
            ignored otherwise
        composite (str): Compositing period (DAY, 8DAY, MON). Used for building output filename
            Defaults to DAY
        overwrite (bool): Overwrite file if already exists? Defaults to False

    Returns:
        str: The output filename

    Raises:
        satmo.SeadasError: if the seadas command exists with status 1
    """
    # l3mapgen ifile=T2016292.L3b_DAY_OC ofile=T2016292.L3B_DAY_RRS_laea.tif resolution=1km south=26 north=40 west=-155 east=-140 projection="+proj=laea +lat_0=33 +lon_0=-147"
    input_meta = filename_parser(x)
    resolution = '%dm' % resolution
    # build file if it doesn't yet exist
    if filename is None:
        if data_root is None:
            raise ValueError('data_root argument must be provided if filename is left empty (None)')
        filename = filename_builder(level = 'L3m', full_path = True,
                                    data_root = data_root, filename = x, composite = composite,
                                    variable = variable, resolution = to_km(resolution))
    if not (os.path.isfile(filename) and not overwrite):
        # Handle projection options
        if proj is None:
            proj = 'smi'
        # Create directory if not already exists
        L3m_dir = os.path.dirname(filename)
        if not os.path.exists(L3m_dir):
            os.makedirs(L3m_dir)
        # filename, composite, variable, resolution, (nc)
        l3map_arg_list = ['l3mapgen',
                          'ifile=%s' % x,
                          'ofile=%s' % filename,
                          'resolution=%s' % resolution,
                          'south=%.1f' % south,
                          'north=%.1f' % north,
                          'west=%.1f' % west,
                          'east=%.1f' % east,
                          'product=%s' % variable,
                          'interp=area',
                          'apply_pal=0', # Otherwise color map is applied which implies generating a byte image only
                          'oformat=tiff',
                          'projection="%s"' % proj]
        with open(os.devnull, 'w') as FNULL:
            # Run cli
            status = subprocess.call(l3map_arg_list, stdout=FNULL, stderr=subprocess.STDOUT)
        if status == 1:
            raise SeadasError('l3mapgen exited with status 1 for input file %s' % x)
        # Update dataset nodata value using rasterio
        with rasterio.open(filename, 'r+') as src:
            src.nodata = -32767
    return filename

def make_time_composite(date_list, var, suite, resolution, composite,
                        data_root, sensor_code='X', fun='mean', filename=None,
                        overwrite=False, preview=True):
    """Make a time composite (L3m) from daily L3m data

    Args:
        date_list (list): A list of the dates to include in the composite
        var (str): L3m variable to composite
        suite (str): L3m suite
        resolution (str): Resolution of data to compose (e.g.: '2km')
        composite (str): Type/name of generated composite (e.g.: '8DAY', '16DAY'). Used
            for automatic output filename generation.
        data_root (str): Root of the data archive
        sensor_code (str): Sensor to composite (defaults to 'X', which
            corresponds to daily (cross sensors) composites.
        fun (str): compositing function, defaults to mean
        filename (str): Optional output filename. Auto generated if not provided
        overwrite (bool): Should output file be overwritten if it already
            exists.
        preview (bool): Should a png preview be automatically generated

    Returns:
        str: The filename of the produced file.
        In case no file is produced (because no input files were found, the function exits without return value.
        When automatically generated the date of the composite corresponds to the first day of the composite.

    Examples:
        >>> import datetime
        >>> import satmo

        >>> begin = datetime.datetime(2016, 01, 01)
        >>> date_list = [begin + datetime.timedelta(days=x) for x in range(0, 16)]
        >>> satmo.make_time_composite(date_list, 'chlor_a', 'CHL', '2km',
                                      '16DAY',
                                      '/home/ldutrieux/sandbox/satmo2_data',
                                      overwrite=True)
    """
    # Search for the list of files
    file_list = []
    for date in date_list:
        file_query = file_finder(data_root=data_root, date=date, level='L3m', suite=suite,
                                    sensor_code=sensor_code, resolution=resolution,
                                    variable=var, composite='DAY')
        if file_query:
            file_list.append(file_query[0])
    # Exit if list of files is empty
    if not file_list:
        return
    # COmpose files
    compose_class = FileComposer(*file_list)
    # Run the compositing method using string provided in fun= argument
    func = getattr(compose_class, fun)
    func()
    # Generate filename if not provided
    if filename is None:
        filename = filename_builder(level='L3m', full_path=True,
                                       data_root=data_root, date=min(date_list),
                                       sensor_code=sensor_code,
                                       suite=suite,
                                       composite=composite, variable=var,
                                       resolution=resolution)
    # Write to file (if overwrite conditions are met)
    if not (os.path.isfile(filename) and not overwrite):
        # Create directory if not already exists
        out_dir = os.path.dirname(filename)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        compose_class.to_file(filename)
        if preview:
            make_preview(filename)
    return filename



def l2_append(x, bands, formula, short_name, long_name, standard_name,
              valid_min, valid_max):
    """Compute a new array and append it to an existing OBPG L2 file

    This function can be called by passing a nested dict of the global variable
    BAND_MATH_FUNCTIONS as kwargs. Example l2_append(x, **BAND_MATH_FUNCTIONS['afai'][sensor])

    Args:
        x (str): Input L2 file in netCDF format
        bands (list): List of strings corresponding to the names of the
            netCDF dataset variables used to compute the new array. They must
            be provided in the same order than used in the formula argument
        formula (func): The function used to compute the new variable. Each argument
            must be an array, and len(args) must equal len(input_bands)
        short_name (str): Short name for the newly create dataset (used as netCDF
            variable name)
        long_name (str): Name of the newly create dataset
        standard_name (str): Name of the newly create dataset
        valid_min (float): Valid minimum value
        valid_max (float): Valid maximum value

    Returns:
        The function is used for its side effect of appending a new variable to an existing netCDF file.
    """
    with nc.Dataset(x, 'a') as src:
        geo = src['geophysical_data']
        newVar = geo.createVariable(short_name, 'f4', ('number_of_lines', 'pixels_per_line'),
                                    fill_value=geo[bands[0]]._FillValue)
        newVar.long_name = long_name
        newVar.standard_name = standard_name
        newVar.valid_min = valid_min
        newVar.valid_max = valid_max
        newVar[:] = formula(*[geo[x][:] for x in bands])


def l2mapgen(x, north, south, west, east, prod, flags, data_root, filename=None,
             width=5000, outmode='tiff', threshold=0, overwrite=False):
    """Wrapper for l2mapgen seadas command line utility

    Args:
        x (str): Input file name
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        prod (str): Product to map (e.g.: 'chlor_a')
        flags (list): List of flags to apply (see global variable FLAGS)
        data_root (str): Root of the data archive
        width (int): Width in pixels of the output image
        outmode (str): See seadas l2mapgen doc
        threshold (float): Minimum percentage of the filled pixels
        overwrite (bool): Overwrite existing files? Return ValueError if file exists
            and overwrite is set to False (default)

    Examples:
        >>> import satmo
        >>> from satmo.global_variables import FLAGS, L3_SUITE_FROM_VAR

        >>> x = '/media/ldutrieux/LoicCONAext/satmo/aqua/L2/2015/077/A2015077191500.L2_LAC_AFAI.nc'
        >>> data_root = '/media/ldutrieux/LoicCONAext/satmo/'

        >>> satmo.l2mapgen(x=x, data_root=data_root, south=3, north=33, west=-122, east=-72,
                           prod='afai', flags = FLAGS['AFAI'])

    Returns:
        str: The output filename
    """
    # Generate automatic filename if not provided
    if filename is None:
        if is_day(x):
            dn = 'day'
        else:
            dn = 'night'
        filename = filename_builder(level='L2m', filename=x, suite=L3_SUITE_FROM_VAR[dn][prod],
                                       variable=prod, full_path=True, data_root=data_root)
    if os.path.isfile(filename) and not overwrite:
        raise ValueError('Error while running l2mapgen on %s; file exists and overwrite set to False' % filename)

    # Create output dir in case it does not exist
    out_dir = os.path.dirname(filename)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Prepare inputs
    cli_args = ['l2mapgen',
                'ifile=%s' % x,
                'ofile=%s' % filename,
                'prod=%s' % prod,
                'flaguse=%s' % ','.join(flags),
                'south=%f' % south,
                'north=%f' % north,
                'west=%f' % west,
                'east=%f' % east,
                'mask=true',
                'width=%d' % width,
                'apply_pal=0',
                'threshold=%f' % threshold,
                'outmode=%s' % outmode]

    # l2mapgen is very verbose, therefore redirect output to devnull
    with open(os.devnull, 'w') as FNULL:
        # Run cli
        status = subprocess.call(cli_args, stdout=FNULL, stderr=subprocess.STDOUT)
        # l2mapgen ifile=A2015077191500.L2_LAC_AFAI.nc ofile=A2015077191500.L2m_afai.tif prod=afai south=3 north=33 west=-122 east=-72 flaguse=LAND,HIGLINT,CLDICE mask=true width=5000 outmode=tiff

    # Check status (return error in case )
    if status != 0:
        raise SeadasError('l2mapgen exited with status %d during L2 mapping' % status)

    # Update dataset nodata value using rasterio
    with rasterio.open(filename, 'r+') as src:
        src.nodata = -32767

    return filename

def l3bin(file_list, north, south, west, east, filename, overwrite=False):
    """Simple wrapper for seadas l3bin

    Used for temporal compositing

    Args:
        file_list (list): List of input L3b files
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        filename (str): Optional output filename
        overwrite (bool): Overwrite existing files?

    Return:
        str: The output filename. Mostly used for its side effects of generating
            a L3b temporal composite file.
    """
    output_meta = filename_parser(filename)
    if not (os.path.isfile(filename) and not overwrite):
        L3b_dir = os.path.dirname(filename)
        # Create directory if not already exists
        if not os.path.exists(L3b_dir):
            os.makedirs(L3b_dir)
        # Create text file with input L2 files
        file_list_file = os.path.join(L3b_dir, 'L3b_file_list_%s_%d%03d_%d' % \
                                     (output_meta['composite'], output_meta['year'],
                                      output_meta['doy'], random.randint(1,9999)))
        with open(file_list_file, 'w') as dst:
            for item in file_list:
                dst.write(item + '\n')
        cli_args = ['l3bin',
                    'in=%s' % file_list_file,
                    'loneast=%f' % east,
                    'lonwest=%f' % west,
                    'latnorth=%f' % north,
                    'latsouth=%f' % south,
                    'out=%s' % filename]
        with open(os.devnull, 'w') as FNULL:
            # Run cli
            status = subprocess.call(cli_args, stdout=FNULL, stderr=subprocess.STDOUT)
        if status != 0:
            raise SeadasError('l3bin exited with status %d during temporal binning' % status)
    else:
        raise ValueError('File exists, set overwrite to True for overwriting file')
    return filename

def l3bin_wrapper(sensor_codes, date_list, suite_list, south, north, west, east, composite,
                  overwrite=False):
    """Wrapper to run l3bin without having to name explicitly input or output files

    Args:
        sensor_codes (list): List of sensor codes to include (e.g.: ['A', 'T', 'V']
        date_list (list): List of dates
        suite_list (list): List of L3 suites to include
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        composite (str): Composite type (8DAY, MON)
        overwrite (bool): Overwrite existing files?

    Returns:
        list: List of L3b files generated. Mostly used for its side effect of generating
        temporally composited L3b files from daily L3b files.
    """
    out_list = []
    for sensor_code in sensor_codes:
        for suite in suite_list:
            file_list = []
            for date in date_list:
                file = file_finder(data_root=data_root, date=date, level='L3b',
                                   suite=suite, sensor_code=sensor_code,
                                   composite=composite)
                if file:
                    file_list.append(file[0])
            filename = filename_builder(level='L3b', full_path=True,
                                           data_root=data_root, date=min(date_list),
                                           sensor_code=sensor_code, suite=suite,
                                           composite=composite)
            try:
                out_file = l3bin(file_list=file_list, north=north, south=south, west=west,
                                 east=east, filename=filename, overwrite=overwrite)
                out_list.append(out_file)
            except Exception as e:
                pprint('l3bin: %s could not be produced. %s' % (filename, e))
    return out_list


