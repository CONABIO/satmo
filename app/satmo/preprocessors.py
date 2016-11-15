import subprocess
from jinja2 import Environment, FileSystemLoader
import os.path
import os
import bz2
import glob



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




# Make a class that holds all the information of a future L2 (binned) product

class l2Process(object):
    def __init__(self, input_dir, template_dir):
        self.input_dir = input_dir
        self.template_dir = template_dir
    def get_file_list(self, pattern = '*.gz2'):
        self.infile_list = glob.glob(os.path.join(self.input_dir, pattern))
    def make_parfile(self):
        env = Environment(loader=FileSystemLoader(self.template_dir))
               template = env.get_template('multilevel-processor-template.par')
               par_file = template.render(infiles = infiles_string)
    def execute(self):
        status = subprocess.call(['multilevel_processor.py', 'modis_SR.par'])
        # Status should be zero if command completed successfully
    def clean(self):



