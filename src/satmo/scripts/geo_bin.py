#!/usr/bin/env python
import argparse

import netCDF4 as nc
import numpy as np
from pyproj import Proj
from affine import Affine
import rasterio
from rasterio.crs import CRS

from glob import glob
from math import floor


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
    # Make bool array
    mask = np.bitwise_and(np.uint32(flag_array), np.array([bit_mask])) == 0
    var = var[mask]
    lat_dd = lat_dd[mask]
    lon_dd = lon_dd[mask]

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
def main(file_list, variable, bit_mask, south, north, west, east, resolution, proj4string, filename, plot = False, vmax = 10):
    bit_mask = int(bit_mask, 16)
    array = bin_map_numpy(file_list, variable, bit_mask, south, north, west, east, resolution, proj4string, filename)
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
              'geo_bin.py -infiles A2016007*.L2_LAC_OC.nc -var chlor_a -bit 0x0669D73B -north 33 -south 3 -west -122 -east -72 '
              '-res 2000 -proj "+proj=laea +lat_0=18 +lon_0=-100" -filename A2016007.L3m_DAY_CHL_chlor_a_2km.tif\n\n'
              '# If you have matplotlib installed, you can visualized the file created\n'
              'geo_bin.py -infiles A2016007*.L2_LAC_OC.nc -var chlor_a -bit 0x0669D73B -north 33 -south 3 -west -122 -east -72 '
              '-res 2000 -proj "+proj=laea +lat_0=18 +lon_0=-100" -filename A2016007.L3m_DAY_CHL_chlor_a_2km.tif --plot\n\n'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument('-infiles', '--file_list', nargs='+',
                        help = 'Input L2 files')

    parser.add_argument('-var', '--variable',
                        required = True,
                        help = 'L3m variable')
    parser.add_argument('-bit', '--bit_mask',
                        required = True,
                        type = str,
                        help = 'Bit maskused for invalid data filtering expressed in hex form (e.g.: 0xC1 if you want to mask bits 0, 6 and 7 (1100 0001))')
    
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