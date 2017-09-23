import subprocess
from jinja2 import Environment, PackageLoader
import os.path
import os
import shutil
import bz2
import glob
import warnings
import string
import random
import re

from .utils import (OC_filename_parser,
                    is_day, OC_filename_builder, to_km,
                    OC_viirs_geo_filename_builder, randomword)
from .errors import SeadasError
from .global_variables import STANDARD_L3_SUITES



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

def getanc(x):
    """Wrapper for the getanc.py seadas utility

    Args:
        x (str): filename of a L1 file

    Returns:
        str: The path to the generated (and moved) .anc text file
    """
    arg_list = ['getanc.py', x]
    with open(os.devnull, 'w') as FNULL:
        subprocess.call(arg_list, stdout=FNULL, stderr=subprocess.STDOUT)
    # Locate anc file generated
    wd = os.getcwd()
    dirname, filename = os.path.split(x)
    anc_file_src = os.path.join(wd, '%s.anc' % filename)
    anc_file_dst = '%s.anc' % x
    shutil.move(anc_file_src, anc_file_dst)
    return anc_file_dst

def l2gen(x, var_list, suite, data_root, get_anc=True):
    """Wrapper to run seadas l2gen on L1A data

    Run l2gen for modis and viirs data. All intermediary files are automatically
    generated in the case of MODIS; if input is a viirs L1A file, there must be a
    corresponging GEO file in the same folder.

    Args:
        x (str): Path to input L1A file
        var_list (list): List of strings representing the variables to process
        suite (str): Output L2 suite name
        data_root (str): Root of the local data archive
        get_anc (bool): Download ancillary data for improved atmospheric correction.
            Defaults to True.

    Returns:
        str: file name of the generated L2 file
    """
    ext = os.path.splitext(x)[1]
    input_dir = os.path.dirname(x)
    output_filename = OC_filename_builder(level='L2', filename=x,
                                          suite=suite, full_path=True,
                                          data_root=data_root)
    output_dir = os.path.dirname(output_filename)
    # The delete switch determines whether or not an uncompressed file must be
    # deleted or not. viirs do not come as bz2 compressed files so this does not apply
    # for them
    delete = False
    input_meta = OC_filename_parser(x)
    if ext == '.bz2':
        x = bz2_unpack(x, input_dir)
        delete = True
    # Get ancillary data if option set to True
    if get_anc:
        anc = getanc(x)
    # Create L2 output dir if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Split in two different paths (modis --> multilevel_processor, viirs --> l2gen)
    if input_meta['sensor'] == 'viirs':
        geo_file = OC_viirs_geo_filename_builder(x)
        cli_elements = ['l2gen',
                        'ifile=%s' % x,
                        'geofile=%s' % geo_file,
                        'ofile=%s' % output_filename,
                        'l2prod=%s' % ','.join(var_list)]
        if get_anc:
            cli_elements.append('par=%s' % anc)
        # l2gen is very verbose, therefore redirect output to devnull
        with open(os.devnull, 'w') as FNULL:
            status = subprocess.call(cli_elements, stdout=FNULL, stderr=subprocess.STDOUT)
        if status != 0:
            raise SeadasError('l2gen processor exited with status %d during viirs L2 processing' % status)
    elif input_meta['sensor'] in ['aqua', 'terra']:
        # modis L2 processing is done via modis_GEO.py + modis_L1B.py + l2gen
        dirname, basename = os.path.split(x)
        geo_file = os.path.join(dirname, '%s%s' % (basename[:15], 'GEO'))
        l1b_file = os.path.join(dirname, '%s%s' % (basename[:15], 'L1B_LAC'))
        # Run modis_GEO.py
        geo_cli = ['modis_GEO.py',
                   x,
                   '--output=%s' % geo_file]
        with open(os.devnull, 'w') as FNULL:
            status = subprocess.call(geo_cli, stdout=FNULL, stderr=subprocess.STDOUT)
        if status != 0:
            raise SeadasError('modis_GEO.py exited with status %d during modis L2 processing' % status)
        # Run modis_L1B.py
        l1b_cli = ['modis_L1B.py',
                   '--okm=%s' % l1b_file,
                   x,
                   geo_file]
        status = subprocess.call(l1b_cli)
        if status != 0:
            raise SeadasError('modis_L1B.py exited with status %d during modis L2 processing' % status)
        # Run l2gen
        cli_elements = ['l2gen',
                        'ifile=%s' % l1b_file,
                        'geofile=%s' % geo_file,
                        'ofile=%s' % output_filename,
                        'l2prod=%s' % ','.join(var_list)]
        if get_anc:
            cli_elements.append('par=%s' % anc)
        # l2gen is very verbose, therefore redirect output to devnull
        with open(os.devnull, 'w') as FNULL:
            status = subprocess.call(cli_elements, stdout=FNULL, stderr=subprocess.STDOUT)
        if status != 0:
            raise SeadasError('l2gen processor exited with status %d during modis L2 processing' % status)
        # Prepare list of intermediary files generated and delete them
        del_files = [os.path.join(dirname, '%s%s' % (basename[:15], 'L1B_QKM')),
                     os.path.join(dirname, '%s%s' % (basename[:15], 'L1B_HKM')),
                     l1b_file,
                     geo_file]
        [os.remove(y) for y in del_files]
    if delete:
        os.remove(x)
    return output_filename

