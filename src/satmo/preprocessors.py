import subprocess
from jinja2 import Environment, PackageLoader
import os.path
import os
import bz2
import glob
import warnings
import string

from .utils import super_glob, parse_file_name, make_file_path, is_day
from .errors import SeadasError
from .global_variables import PRODUCT_SUITES



def bz2_unpack(source, destination, overwrite = False):
    """Unpacks data compressed with bz2
    
    Utility function to unpack bz2 compressed data
    The function only works if a single file is compressed

    Args:
        source (str): the filename of the archive
        destination (str): the destination directory, filename will be
        set automatically
        overwrite (bool): If false, check whether file already exists and returns its name

    Returns:
        str: The filename of the unpacked file
    """
    if not os.path.exists(destination):
        os.makedirs(destination)
    out_file = os.path.join(destination, os.path.splitext(os.path.basename(source))[0])
    if not overwrite and os.path.isfile(out_file):
        return out_file
    with open(out_file, 'wb') as dst, bz2.BZ2File(source, 'rb') as src:
        for data in iter(lambda : src.read(100 * 1024), b''):
            dst.write(data)
    return out_file


def bz2_compress(source, destination, compresslevel = 3, overwrite = False):
    """Unpacks data compressed with bz2
    
    Utility function to bz2 compress data

    Args:
        source (str): the filename to compress
        destination (str): the destination directory, filename will be
        set automatically
        compresslevel (int): Compression level
        overwrite (bool): If false, check whether file already exists and returns its name

    Returns:
        str: The filename of the bz2 compressed file
    """
    if not os.path.exists(destination):
        os.makedirs(destination)
    out_file = os.path.join(destination, os.path.basename(source)) + '.bz2'
    if not overwrite and os.path.isfile(out_file):
        return out_file
    with open(source, 'rb') as src, bz2.BZ2File(out_file, 'wb', compresslevel = compresslevel) as dst:
        for data in iter(lambda : src.read(100 * 1024), b''):
            dst.write(data)
    return out_file


# Make a class that holds all the information of a future L2 (binned) product

class l3map(object):

    template = Environment(loader=PackageLoader('satmo', 'templates')).get_template('l3bprocess.par')

    def __init__(self, input_dir, pattern = r'.*', output_basedir = None):
        self.input_dir = input_dir
        self.file_list = super_glob(input_dir, pattern)
        self.sensor = parse_file_name(self.file_list[0])['sensor']
        if output_basedir is None:
            output_basedir = string.replace(input_dir, make_file_path(self.file_list[0], add_file = False), '')
        self.output_dir = os.path.join(output_basedir, make_file_path(self.file_list[0], doy = False, level = 'L3b'))

    def execute(self, north, south, east, west, suite, day = True, binning_resolution = 1,\
        mapping_resolution = '1km', proj4 = '+proj=laea +lat_0=18 +lon_0=-97', overwrite = False):
        # Day or night only filter
        file_list_sub = [x for x in self.file_list if is_day(x) is day]
        # Extract files if they need extraction
        ext = os.path.splitext(file_list_sub[0])[1]
        if ext == '.bz2':
            file_list_sub = [bz2_unpack(x, self.input_dir) for x in file_list_sub]
        # Create output dir if it doesn't exist
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Create variables for templating and command run 
        overwrite_int = int(overwrite)
        prod_list = PRODUCT_SUITES[suite][self.sensor]
        # Par file templating 
        par = self.template.render(binning_resolution = binning_resolution,
                                   overwrite_int = overwrite_int,
                                   prod_list = prod_list,
                                   file_list = file_list_sub)
        # par filename creation + writing to output directory
        par_file = os.path.join(self.output_dir, '%s_l3bprocess.par' % self.sensor)
        with open(par_file, "wb") as dst:
            dst.write(par)
        # Build multilevel processing arguments list
        arg_list_0 = ['multilevel_processor.py', par_file, '--use_existing', '--output_dir=%s' % self.output_dir]
        status0 = subprocess.call(arg_list_0) # --use_existing --output_dir=  (--overwrite - also in par file)
        if status0 != 0:
            raise SeadasError('Multilevel processor exited with %d during processing to L2bin' % status)
        # Prepare l3mapgen command and run it
        bin_file = 
        out_file = 
        # l3mapgen ifile=T2016292.L3b_DAY_OC ofile=T2016292.L3B_DAY_RRS_laea.nc 
        # resolution=1km south=26 north=40 west=-155 east=-140 projection="+proj=laea +lat_0=33 +lon_0=-147"
        return output_file

    def clean(self):
        pass


class extractJob(object):
    """Class sensor independent L1A data extraction

    Works with modis, viirs, seawifs. Works by calling l1aextract_%sensor via
    multilevel_processor.py. All the processing happens in the same directory
 
    Args:
        input_dir (str): location of the files to extract, ideally the directory should
        not contain any other files, otherwise there is a risk they get deleted
        pattern (str): regex pattern to match input files
    """
    template = Environment(loader=PackageLoader('satmo', 'templates')).get_template('extract.par')

    def __init__(self, input_dir, pattern = r'.*L1A.*\.(nc|bz2)$'):
        self.input_dir = input_dir
        self.file_list_full = glob.glob(os.path.join(input_dir, '*L1A*'))
        self.file_list = super_glob(input_dir, pattern)
        self.has_subs = any(['.sub' in x for x in self.file_list_full])
        # Check for consitency of the input list by checking that all files have the same extension
        ext = os.path.splitext(self.file_list[0])[1]
        if not all(os.path.splitext(x)[1] == ext for x in self.file_list):
            raise ValueError('Input filenames are inconsistent')
        meta = parse_file_name(self.file_list[0])
        if (meta['sensor'] == 'aqua') or (meta['sensor'] == 'terra'):
            self.sensor = 'modis'
        elif meta['sensor'] in ['seawifs', 'viirs']:
            self.sensor = meta['sensor']
        else:
            raise ValueError('Cannot extract data for this sensor')

    def extract(self, north, south, east, west, overwrite = False):
        """Data extraction method

        Used for its side effect of extracting the L1A file to the specified extent

        Args:
            north (float): north latitude of bounding box in DD
            south (float): south latitude of bounding box in DD
            west (float): west longitude of bounding box in DD
            east (float): east longitude of bounding box in DD
            overwrite (bool): Should existing .sub files be overwritten. Usefull
            to differentiate archive updating vs re-processing.

        Details:
            It is safe to apply a buffer (larger extent, e.g. 2 extra degrees on each side) around
            the area ordered with query_from_extent (query module).

        Return:
            Status returned by multilevel_processor.py (0: fine, 1: error) 
        """
        if not overwrite and self.has_subs:
            warnings.warn('Files in %s have already been extracted. Set overwrite to True to overwrite them.' % self.input_dir)
            return 0
        ext = os.path.splitext(self.file_list[0])[1]
        if ext == '.bz2':
            self.file_list = [bz2_unpack(x, self.input_dir) for x in self.file_list]
        par = self.template.render(file_list = self.file_list,
                                   north = north,
                                   south = south,
                                   east = east,
                                   west = west,
                                   sensor = self.sensor)
        # Write generated par file to disk
        par_file = os.path.join(self.input_dir, '%s_extract.par' % self.sensor)
        with open(par_file, "wb") as dst:
            dst.write(par)
        # Run multilevel_processor.py
        status = subprocess.call(['multilevel_processor.py', '--use_existing', par_file, '--output_dir=' + self.input_dir])
        if status != 0:
            raise SeadasError('Multilevel processor exited with %d during extraction' % status)
        return status

    def compress(self):
        """Compress the extracted files present in the directory with bz2
        """
        subfiles_list = super_glob(self.input_dir, '.*\.sub$')
        compressed_list = [bz2_compress(x, self.input_dir) for x in subfiles_list]
        return compressed_list

    def clean(self, keep_uncompressed = False):
        """Remove unwanted files

        Args:
            keep_uncompressed (bool): Should uncompressed files (input to seadas processors)
            be kept?
        """
        full_list = glob.glob(os.path.join(self.input_dir, '*'))
        if keep_uncompressed:
            # Match sub and sub.bz2
            pattern = r'.*(\.sub$|\.sub\.bz2$)'
        else:
            # Match sub.bz2 only
            pattern = r'.*\.sub\.bz2$'
        keep_list = super_glob(self.input_dir, pattern)
        delete_list = list(set(full_list).difference(keep_list))
        [os.remove(x) for x in delete_list]
        return keep_list