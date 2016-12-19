import subprocess
from jinja2 import Environment, PackageLoader
import os.path
import os
import bz2
import glob
import warnings
import string
import random
import re

from .utils import super_glob, parse_file_name, make_file_path, make_file_name, is_day
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
    """Class for data processing from L1A to L3map
    """

    template = Environment(loader=PackageLoader('satmo', 'templates')).get_template('l2process.par')

    def __init__(self, input_dir, L2_output_basedir = None, L3_output_basedir = None):
        """Instantiate l3map class

        Args:
            input_dir (str): Directory where L1A files are located
            L2_output_basedir (str): Base directory where L2 files (intermediate products) should be stored.
            Only the base, the rest of the path will be generated automatically. Defaults to None, in which case
            the base dir is set to be the same as input_dir
            L3_output_basedir (str): Base directory where L3m files should be stored. If set to None (default),
            L2_output_basedir is used.
        """
        self.input_dir = input_dir
        full_list = glob.glob(os.path.join(input_dir, '*'))
        if any([re.search(r'\d{13}\.L1A_.*\.sub$', x) for x in full_list]):
            # Contained already unpacked and spatially extracted files
            self.file_list = super_glob(input_dir, r'\d{13}\.L1A_.*\.sub$')
        elif any([re.search(r'\d{13}\.L1A_.*\.sub\.bz2$', x) for x in full_list]):
            # Contained spatially extracted, not unpacked
            self.file_list = super_glob(input_dir, r'\d{13}\.L1A_.*\.sub\.bz2$')
        elif any([re.search(r'\d{13}\.L1A_.*(?<!\.bz2)$', x) for x in full_list]):
            # Contains L1A data that do not end with bz2
            self.file_list = super_glob(input_dir, r'\d{13}\.L1A_.*(?<!\.bz2)$')
        else:
            self.file_list = super_glob(input_dir, r'\d{13}\.L1A_.*')
        self.sensor = parse_file_name(self.file_list[0])['sensor']
        if L2_output_basedir is None:
            L2_output_basedir = string.replace(input_dir, make_file_path(self.file_list[0], add_file = False), '')
        if L3_output_basedir is None:
            L3_output_basedir = L2_output_basedir
        self.L2_output_dir = os.path.join(L2_output_basedir, make_file_path(self.file_list[0], doy = True, level = 'L2'))
        self.L3_output_dir = os.path.join(L3_output_basedir, make_file_path(self.file_list[0], doy = False, level = 'L3m'))

    def execute(self, north, south, east, west, suites = ['RRS', 'SST', 'SST4', 'PAR'], day = True, binning_resolution = 1,\
        mapping_resolution = '1000m', proj4 = '+proj=laea +lat_0=18 +lon_0=-97', overwrite = False):
        """Processes data from L1A to L3m level

        Args:
            north (float): north latitude of mapped file extent
            south (float): south latitude of mapped file extent
            west (float): west longitude of mapped file extent
            east (float): east longitude of mapped file extent
            suite (list): List of strings indicating the product suites to process.
            defaults to ['RRS', 'SST', 'SST4', 'PAR']. Use ['NSST'] if day is set to False
            day (bool): Process day or night data. Defaults to True. Enables filtering of input files and
            appropriate l2bin night argument. suite argument should be adapted accordingly if day is set to False.
            binning_resolution (int or str): Spatial binning resolution in km. Defaults to 1, use 'H' for 500 m
            mapping_resolution (str): Resolution of output L3m file. Defaults to '1000m'
            proj4 (str): proj4 string, see list of valid projections in l3mapgen doc.
            Defaults to '+proj=laea +lat_0=18 +lon_0=-97'
            overwrite (bool): Should existing L2 files be overwritten? Defaults to False.

        Returns:
            List of L3m files created
        """
        # Day or night only filter
        file_list_sub = [x for x in self.file_list if is_day(x) is day]
        # Extract files if they need extraction
        ext = os.path.splitext(file_list_sub[0])[1]
        if ext == '.bz2':
            file_list_sub = [bz2_unpack(x, self.input_dir) for x in file_list_sub]
        # Create L2 output dir if it doesn't exist
        if not os.path.exists(self.L2_output_dir):
            os.makedirs(self.L2_output_dir)
        # Create variables for templating and command run
        prod_list = []
        for suite in suites:
            prod_list += PRODUCT_SUITES[suite][self.sensor]
        # Par file templating 
        par = self.template.render(overwrite = overwrite,
                                   prod_list = prod_list,
                                   file_list = file_list_sub)
        # par filename creation + writing to output directory
        par_file = os.path.join(self.L2_output_dir, '%s_l2process.par' % self.sensor)
        with open(par_file, "wb") as dst:
            dst.write(par)
        # Build multilevel processing arguments list
        arg_list_0 = ['multilevel_processor.py',
                      par_file,
                      '--use_existing',
                      '--output_dir=%s' % self.L2_output_dir]
        status_0 = subprocess.call(arg_list_0)
        if status_0 != 0:
            raise SeadasError('Multilevel processor exited with %d during processing to L2' % status_0)
        # Prepare l2bin command and run it
        L2_file_list = glob.glob(os.path.join(self.L2_output_dir, '*L2*'))
        L2_file_list = [x for x in L2_file_list if is_day(x) is day]
        # Create L3bin output dir if it doesn't exist
        if not os.path.exists(self.L3_output_dir):
            os.makedirs(self.L3_output_dir)
        # Write L2 file list to text file to use as input
        L2_0_meta = parse_file_name(L2_file_list[0])
        # Make unique filename
        L2_file_list_file = os.path.join(self.L3_output_dir, 'L2_file_list_%d%03d_%d' % \
                                        (L2_0_meta['year'], L2_0_meta['doy'], random.randint(1,9999)))
        with open(L2_file_list_file, 'w') as dst:
            for item in L2_file_list:
                dst.write(item + '\n')
        l2b_l3m_status_list = []
        output_file_list = []
        for suite in suites:
            # l2bin
            ofile = os.path.join(self.L3_output_dir, make_file_name(L2_file_list[0], 'L3b', suite))
            if not os.path.isfile(ofile) or overwrite:
                l3bprod = PRODUCT_SUITES[suite][self.sensor]
                l2bin_arg_list = ['l2bin',
                                  'l3bprod=%s' % ','.join(l3bprod),
                                  'infile=%s' % L2_file_list_file,
                                  'resolve=' + str(binning_resolution),
                                  'ofile=%s' % ofile,
                                  'night=%d' % int(not day)]
                status_1 = subprocess.call(l2bin_arg_list)
                l2b_l3m_status_list.append(status_1)
            # l3mapgen
            ifile = ofile
            ofile = os.path.join(self.L3_output_dir, make_file_name(ifile, 'L3m', suite))
            if not os.path.isfile(ofile) or overwrite:
                l3map_arg_list = ['l3mapgen',
                                  'ifile=%s' % ifile,
                                  'ofile=%s' % ofile,
                                  'resolution=%s' % mapping_resolution,
                                  'south=%d' % south,
                                  'north=%d' % north,
                                  'west=%d' % west,
                                  'east=%d' % east,
                                  'projection=%s' % proj4]
                status_2 = subprocess.call(l3map_arg_list)
                l2b_l3m_status_list.append(status_2)
            output_file_list.append(ofile)
        if 1 in l2b_l3m_status_list:
            raise SeadasError('l2bin or l3mapgen exited with status 1')
        # l3mapgen ifile=T2016292.L3b_DAY_OC ofile=T2016292.L3B_DAY_RRS_laea.nc 
        # resolution=1km south=26 north=40 west=-155 east=-140 projection="+proj=laea +lat_0=33 +lon_0=-147"
        return output_file_list

    def clean(self, keep_uncompressed = False):
        """Remove intermediary files generated during processing

        Namely deletes on disk L1B, GEO and (optionally) uncompressed L1A files

        Args:
            keep_uncompressed (bool): Should uncompressed L1A files. Defaults to False (keep L1A archives only)

        Returns:
            Nothing. Used for its side effect of deleting files on disk
        """
        L1_rm_list = glob.glob(os.path.join(self.input_dir, '*'))
        # Automatically remove compressed L1A files from the list
        L1_rm_list = [x for x in L1_rm_list if not x.endswith('.bz2')]
        if keep_uncompressed:
            L1_rm_list = [x for x in L1_rm_list if not 'L1A_' in x]
        [os.remove(x) for x in L1_rm_list]
        L2_rm_list = glob.glob(os.path.join(self.L2_output_dir, '*'))
        # Remove L2 files from the rm list
        L2_rm_list = [x for x in L2_rm_list if not parse_file_name(x, raiseError = False)['level'] == 'L2']
        [os.remove(x) for x in L2_rm_list]
        # TODO: this could cause problem if processing of other output (e.g. night files)
        # is happening at the same moment
        


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

    def compress(self, overwrite = False):
        """Compress the extracted files present in the directory with bz2

        Args:
            overwrite (bool): Should existing bz2 files be overwritten
        """
        subfiles_list = super_glob(self.input_dir, '.*L1A_.*\.sub$')
        compressed_list = [bz2_compress(x, self.input_dir, overwrite = overwrite) for x in subfiles_list]
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