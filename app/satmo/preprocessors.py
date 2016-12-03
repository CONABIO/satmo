import subprocess
from jinja2 import Environment, FileSystemLoader
import os.path
import os
import bz2
import glob

from .utils import super_glob, parse_file_name



def bz2_unpack(source, destination):
    """Unpacks data compressed with bz2
    
    Utility function to unpack bz2 compressed data
    The function only works if a single file is compressed

    Args:
        source (str): the filename of the archive
        destination (str): the destination directory, filename will be
        set automatically

    Returns:
        str: The filename of the unpacked file
    """
    if not os.path.exists(destination):
        os.makedirs(destination)
    out_file = os.path.join(destination, os.path.splitext(os.path.basename(source))[0])
    with open(out_file, 'wb') as dst, bz2.BZ2File(source, 'rb') as src:
        for data in iter(lambda : src.read(100 * 1024), b''):
            dst.write(data)
    return out_file


def bz2_compress(source, destination, compresslevel = 3):
    """Unpacks data compressed with bz2
    
    Utility function to bz2 compress data

    Args:
        source (str): the filename to compress
        destination (str): the destination directory, filename will be
        set automatically
        compresslevel (int): Compression level

    Returns:
        str: The filename of the bz2 compressed file
    """
    if not os.path.exists(destination):
        os.makedirs(destination)
    out_file = os.path.join(destination, os.path.basename(source)) + '.bz2'
    with open(source, 'rb') as src, bz2.BZ2File(out_file, 'wb', compresslevel = compresslevel) as dst:
        for data in iter(lambda : src.read(100 * 1024), b''):
            dst.write(data)
    return out_file


# Make a class that holds all the information of a future L2 (binned) product

class l2Process(object):
    def __init__(self, input_dir, template_dir):
        self.input_dir = input_dir
        self.template_dir = template_dir
    def get_file_list(self, pattern = r'*.(bz2|nc)$'):
        self.infile_list = super_glob(self.input_dir, pattern)
    def make_parfile(self):
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template('multilevel-processor-template.par')
        par_file = template.render(infiles = infiles_string)
    def execute(self):
        status = subprocess.call(['multilevel_processor.py', 'modis_SR.par'])
        # Status should be zero if command completed successfully
    def clean(self):
        pass



class extractJob(object):
    """Class sensor independent L1A data extraction

    Works with modis, viirs, seawifs. Works by calling l1aextract_%sensor via
    multilevel_processor.py. All the processing happens in the same directory
 
    Args:
        input_dir (str): location of the files to extract, ideally the directory should
        not contain any other files, otherwise there is a risk they get deleted
    TODO: Add a mechanism to check whether the extraction has already been performed
    """
    template = Environment(loader=PackageLoader('satmo', 'templates')).get_template('extract.par')

    def __init__(self, input_dir):
        self.input_dir = input_dir
        self.file_list = glob.glob(os.path.join(input_dir, '*L1A*'))
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

    def extract(self, north, south, east, west):
        """Data extraction method

        Used for its side effect of extracting the L1A file to the specified extent

        Args:
            north (float): north latitude of bounding box in DD
            south (float): south latitude of bounding box in DD
            west (float): west longitude of bounding box in DD
            east (float): east longitude of bounding box in DD

        Return:
            Status returned by multilevel_processor.py (0: fine, 1: error) 
        """
        ext = os.path.splitext(self.file_list[0])[1]
        if ext == '.bz2':
            self.file_list = [bz2_unpack(x, self.input_dir) for x in self.file_list]
        infile_string = ','.join(self.file_list)
        # FIll template
        par = self.template.render(infile_string = infile_string,
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
        return status

    def compress(self):
        """Compress the extracted files present in the directory with bz2
        """
        subfiles_list = super_glob(os.path.join(self.input_dir, '.*\.sub$'))
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
            pattern = r'.*[\.sub$|\.sub\.bz2$]'
        else:
            # Match sub.bz2 only
            pattern = r'.*\.sub\.bz2$'
        keep_list = super_glob(self.input_dir, pattern)
        delete_list = list(set(full_list).difference(keep_list))
        [os.remove(x) for x in delete_list]
        return keep_list