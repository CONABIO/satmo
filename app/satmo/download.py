import requests
import os.path
import os
from .utils import parse_file_name

def download_file(url, write_dir):
    """Generic file download function

    Downloads a file from a URL, and write it to a user defined location

    Args:
        url (str): download url
        write_dir: Host directory to which the data will be written

    Returns:
        str: The filename of the downloaded data
    """
    local_filename = os.path.join(write_dir, url.split('/')[-1])
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return local_filename


def download_to_tree(url, base_dir):
    """Download an ocean product file and automatically write it to the right location

    The idea is that the function immediatly knows where to write the file
    by parsing the filename (present in url)

    Args:
        url (str): download url
        base_dir (str): root of the archive tree on the host

    Details:
        Directories where data are downloaded do not need to exist before running the function

    Returns:
        str: The filename of the downloaded file
    """
    file_meta = parse_file_name(url)
    # use following
    write_dir = os.path.join(base_dir, file_meta['sensor'], file_meta['level'],\
                             str(file_meta['year']), str(file_meta['doy']))
    # Create directory if it doesn't exist yet
    if not os.path.exists(write_dir):
        os.makedirs(write_dir)
    file_path = download_file(url, write_dir)
    return file_path
