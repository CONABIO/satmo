import subprocess
import jinja2
import os.path
import os

# Make a class that holds all the information of a 

class l2gen(object):
    def __init__(self):
        pass
    def make_parfile(self):
        env = Environment(loader=PackageLoader('satmo', 'templates'))
               template = env.get_template('default.html')
               html_out = template.render(infiles = self.infiles_string)
    def execute(self):
        status = subprocess.call(['multilevel_processor.py', 'modis_SR.par'])
        # Status should be zero if command completed successfully
    def clean(self):


def bz2_unpack(source, destination):
    """Unpacks data compressed with bz2

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





