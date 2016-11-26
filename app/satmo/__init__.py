from .download import download_robust, download_to_tree, download_file
from .preprocessors import bz2_unpack
from .query import make_download_url, query_from_extent
from .utils import make_file_path, parse_file_name, super_glob

# Global variable that contains sensor information
SENSOR_CODES = {'A': 'aqua',
                'T': 'terra',
                'S': 'seawifs',
                'V': 'viirs',
                'O': 'octs',
                'C': 'czcs',
                'M': 'meris',
                'H': 'hico'}