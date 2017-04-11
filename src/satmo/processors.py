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
        processed new variables from reflectance layers present in the L2 file, extract and existing
        one, mask the invalid observations and bin the resulting clean variable to a regular grid.
    
    Args:
        

    Attributes:
        

    """
    def __init__(self, sensor, date, collection):
        pass

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
        processor = cls(file_list)
        return processor

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

    def _get_coords(self, file):
        """Internal function to retrieve geolocation arrays from a L2 file

        Args:
            file (str): File name to read the variable from
            
        Returns:
            Tuple: tuple of two numpy arrays representing flattened long and lat arrays
        """
        with nc.Dataset(file) as src:
            lon = src.groups['navigation_data'].variables['longitude'][:].flatten()
            lat = src.groups['navigation_data'].variables['latitude'][:].flatten()
        return (lon, lat)
    
class Process(BasicBinMap):
    """Class to put the functions to compute, inherits from BasicBinMap so that
        computing a new variable from reflectance bands is an optional step before
        binning
    """
    pass

def bin_map_numpy(file_list, variable, bit_mask, south, north, west, east, resolution, proj4string, filename):
    """Performs binning and mapping of a list of level 2 Ocean color files

    Attempt to reproduce the behaviour of seadas l2bin + l3mapgen

    Args:
        file_list (list): List of input (level 2) file names
        variable (str): Geophysical variable to process (Must be contained in the files under the 'geophysical_data' group)
        bit_mask (int): Bit mask, most preferably expressed in hex form (e.g.: 0xC1 if you want to mask bits 0, 6 and 7 (1100 0001))
        south (float): Southern border of output extent (in DD)
        north (float): Northern border of output extent (in DD)
        west (float): Western border of output extent (in DD)
        east (float): Eastern border of output extent (in DD)
        resolution (float): Output resolution (in the unit of the output coordinate reference system)
        proj4string (str): Coordinate reference system of the output in proj4 format
        filename (str): Output filename (only tif is supported at the moment)

    Return:
        np.array: The array with binned values
    """
    lon_dd = np.array([])
    lat_dd = np.array([])
    var = np.array([])
    flag_array = np.array([])

    # Ingest all the L2 data their coordinates in a flattened form
    for file in file_list:
        with nc.Dataset(file) as src:
            lon_dd = np.append(lon_dd, src.groups['navigation_data'].variables['longitude'][:].flatten())
            lat_dd = np.append(lat_dd, src.groups['navigation_data'].variables['latitude'][:].flatten())
            var = np.append(var, src.groups['geophysical_data'].variables[variable][:].flatten())
            flag_array = np.append(flag_array, src.groups['geophysical_data'].variables['l2_flags'][:].flatten())

    # Flag masking
    var = var[np.bitwise_and(flag_array, np.array([bit_mask])) == 0]

    # Instantiate proj object
    p = Proj(proj4string)

    # Find output corners coordinates in output CRS
    # TODO: This does not account for the extent deformation induced by the projection
    top_left = p(west, north)
    bottom_right = p(east, south)

    # Define output array shape (nrow, ncol)
    destination_shape = ( int( abs(top_left[1] - bottom_right[1]) / float(resolution)), int( abs(top_left[0] - bottom_right[0]) / float(resolution)) )

    # Define affine transform and the inverse transform
    aff = Affine(resolution, 0.0, top_left[0], 0.0, -resolution, top_left[1])
    ffa = ~aff

    # Convert the lat and lon arrays to projected coordinates
    lon_proj, lat_proj = p(lon_dd, lat_dd)

    # Convert projected coordinates to destination array indices
    destination_ids = ffa * (lon_proj, lat_proj)

    # Perform 2d data binning (to average all input coordinates falling withing the same outut pixel)
    # 1 Sum up within each bin
    dst_array, _, _ = np.histogram2d(destination_ids[1], destination_ids[0], bins=(range(0, destination_shape[0] + 1, 1), range(0, destination_shape[1] + 1, 1)), weights=var, normed=False)
    # Retrieve count per bin
    counts, _, _ = np.histogram2d(destination_ids[1], destination_ids[0], bins=(range(0, destination_shape[0] + 1, 1), range(0, destination_shape[1] + 1, 1)))
    # Compute average value per bin
    dst_array = dst_array / counts
    dst_array = np.ma.masked_invalid(dst_array)

    # Prepare output file metadata
    geo_dict = {'crs': CRS.from_string(proj4string),
                'affine': aff,
                'height': destination_shape[0],
                'width': destination_shape[1],
                'driver': u'GTiff',
                'dtype': rasterio.float32, # TODO: Better control datatype
                'count': 1,
                'nodata': 0}

    # write array to file
    with rasterio.open(filename, 'w', **geo_dict) as dst:
        dst.write_band(1, dst_array.astype(rasterio.float32))

    return dst_array



# Function to pass to argparse
def main(file_list, variable, south, north, west, east, resolution, proj4string, filename, plot = False, vmax = 10):
    array = bin_map_numpy(file_list, variable, south, north, west, east, resolution, proj4string, filename)
    if plot:
        import matplotlib.pyplot as plt
        from matplotlib.colors import LogNorm

        plt.imshow(array, interpolation = "none", norm=LogNorm(vmax = vmax), cmap = 'jet')
        plt.colorbar()
        plt.show()


if __name__ == '__main__':
    epilog = ('Experimental CLI to bin L2 ocean data using numpy\n\n'
              '------------\n'
              'Example usage:\n'
              '------------\n\n'
              '# Download some test data (around Mexico)\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007174000.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007174500.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007191500.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007192000.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007192500.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007205500.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007210000.L2_LAC_OC.nc\n'
              'wget https://oceandata.sci.gsfc.nasa.gov/cgi/getfile/A2016007210500.L2_LAC_OC.nc\n\n'
              '# Generate binned file in Lambert Azimuthal Equal Area at 2 km resolution\n'
              './geo_bin.py -infiles A2016007*.L2_LAC_OC.nc -var chlor_a -north 33 -south 3 -west -122 -east -72'
              '-res 2000 -proj "+proj=laea +lat_0=18 +lon_0=-100" -filename A2016007.L3m_DAY_CHL_chlor_a_2km.tif\n\n'
              '# If you have matplotlib installed, you can visualized the file created\n'
              './geo_bin.py -infiles A2016007*.L2_LAC_OC.nc -var chlor_a -north 33 -south 3 -west -122 -east -72'
              '-res 2000 -proj "+proj=laea +lat_0=18 +lon_0=-100" -filename A2016007.L3m_DAY_CHL_chlor_a_2km.tif --plot\n\n'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-infiles', '--file_list', nargs='+',
                        help = 'Input L2 files')

    parser.add_argument('-var', '--variable',
                        required = True,
                        help = 'L3m variable')
    
    parser.add_argument('-north', '--north',
                        type = float,
                        required = True,
                        help = 'Northern boundary in DD')

    parser.add_argument('-south', '--south',
                        type = float,
                        required = True,
                        help = 'Southern boundary in DD')

    parser.add_argument('-east', '--east',
                        type = float,
                        required = True,
                        help = 'Eastern most boundary in DD')
    
    parser.add_argument('-west', '--west',
                        type = float,
                        required = True,
                        help = 'Western most boundary in DD')  

    parser.add_argument('-res', '--resolution',
                        type = float,
                        required = True,
                        help = 'Output resolution in CRS unit')

    parser.add_argument('-proj', '--proj4string',
                        required = True,
                        help = 'Output CRS in proj4 format (Quotted)')

    parser.add_argument('-filename', '--filename',
                        required = True,
                        help = 'Output (tif) filename')


    parser.add_argument('--plot', action='store_true',
                        help = 'plot the output with matplotlib')
    parser.set_defaults(plot=False)

    parser.add_argument('-vmax', '--vmax',
                        help = 'if --plot, maximum value used for color scaling')
    parser.set_defaults(vmax=10)

    parsed_args = parser.parse_args()

    main(**vars(parsed_args))
