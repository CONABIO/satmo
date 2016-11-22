import requests

import os.path
import os
import time
import warnings
from pprint import pprint

from .utils import parse_file_name, make_file_path
from .errors import HttpResourceNotAvailable

def download_file(url, write_dir):
    """Generic file download function

    Downloads a file from a URL, and write it to a user defined location

    Args:
        url (str): download url
        write_dir (str): Host directory to which the data will be written

    Details:
        The function will raise a ConnectionError (via requests) if a connection cannot be established
        with the server (e.g.: network is down) and an HttpResourceNotAvailable if the file appear not to
        exist on the server

    Returns:
        str: The filename of the downloaded data
    """
    local_filename = os.path.join(write_dir, url.split('/')[-1])
    # Test that file is present on remote
    r0 = requests.head(url)
    if r0.status_code == 404:
        raise HttpResourceNotAvailable
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return local_filename


def download_to_tree(url, base_dir, overwrite = False, check_integrity = False):
    """Download an ocean product file and automatically write it to the right location

    The idea is that the function immediatly knows where to write the file
    by parsing the filename (present in url)

    Args:
        url (str): download url
        base_dir (str): root of the archive tree on the host
        overwrite (bool): Should the file be overwritten if already existing on local host
        check_integrity (bool): Only makes sense if overwrite is set to False (when updating the archive)

    Details:
        Directories where data are downloaded do not need to exist before running the function
        Similarly to download_file, the function will raise a ConnectionError (via requests) if a connection
        cannot be established with the server (e.g.: network is down) and an HttpResourceNotAvailable
        if the file appear not to exist on the server. It might be worth re-trying when catching requests.ConnectionError,
        going to the next file is probably the best way if catching a HttpResourceNotAvailable

    Returns:
        str: The filename of the downloaded file
    """
    write_dir = os.path.join(base_dir, make_file_path(url, add_file = False))
    if not overwrite:
        file_path = os.path.join(write_dir, url.split('/')[-1])
        if os.path.isfile(file_path): # The file exists
            if check_integrity:
                h = requests.head(url)
                if h.status_code == 404:
                    raise HttpResourceNotAvailable
                if os.path.getsize(file_path) == int(h.headers['Content-Length']): # file size matches
                    return file_path
            else:
                return file_path
    # Create directory if it doesn't exist yet
    if not os.path.exists(write_dir):
        os.makedirs(write_dir)
    file_path = download_file(url, write_dir)
    return file_path


def download_robust(url, base_dir, n_retries = 5, pause_retries = 10, overwrite = False, check_integrity = False):
    """Robust download of a list of urls
    
    Handles connection errors, optionally check for existing files and integrity
    Suitable for real time use and for updating an archive without overwritting existing data

    Args:
        url (str): Download url
        base_dir (str): root of the archive tree on the host
        n_retries (int): Number of retries when the download fails because of a ConnectionError
        pause_retries (int): Duration (in seconds) between retries
        overwrite (bool): Should existing files on the host be overwritten
        check_integrity (bool): Only makes sense if overwrite is set to False (when updating the archive)

    Returns:
        Boolean, True when successful, False otherwise

    TODO: About the overwrite option: how to handle when a file is updated by NASA on the server (reprocessed)
    The filename would be different so the data wouldn't be recognized as existing unless it's mached against
    the metadata produced by parse_file_name()
    """
    n = 1
    while n <= n_retries:
        try:
            file_path = download_to_tree(url, base_dir, overwrite = overwrite, check_integrity = check_integrity)
            return True
        except requests.ConnectionError:
            n += 1
            time.sleep(pause_retries)
        except HttpResourceNotAvailable:
            warnings.warn(url + ' not downloaded. Not found on server')
            return False
        except:
            warnings.warn(url + ' not downloaded. Unknown reason')
            return False
    warnings.warn(url + ' not downloaded. Max retries reached')
    return False