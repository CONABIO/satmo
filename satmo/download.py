import requests

import os.path
import os
import time
import warnings
import contextlib
from pprint import pprint

from .utils import path_builder
from .errors import HttpResourceNotAvailable

def download_file(url, write_dir, overwrite = False, check_integrity = False, timeout = 15):
    """Generic file download function

    Downloads a file from a URL, and write it to a user defined location.
    The function will raise a ConnectionError (via requests) if a connection cannot be established
    with the server (e.g.: network is down) and an HttpResourceNotAvailable if the file appear not to
    exist on the server

    Args:
        url (str): download url
        write_dir (str): Host directory to which the data will be written
        overwrite (bool): Should the file be overwritten if already existing on local host
        check_integrity (bool): Only makes sense if overwrite is set to False (when updating the archive)
        timeout (float): How long to wait (in seconds) for the server to send data before giving up and 
            raising a requests.ConnectionError

    Returns:
        str: The filename of the downloaded data
    """
    local_filename = os.path.join(write_dir, url.split('/')[-1])
    file_exists = os.path.isfile(local_filename)
    if file_exists and not overwrite and not check_integrity:
        # No need to even send a request, end function
        return None
    # Test that file is present on remote
    r0 = requests.head(url)
    if r0.status_code == 404:
        raise HttpResourceNotAvailable
    if not overwrite and file_exists and check_integrity:
        # FIle integrity checking
        if os.path.getsize(local_filename) == int(r0.headers['Content-Length']): # file size matches
            return None
    # Create directory if it doesn't exist yet
    if not os.path.exists(write_dir):
        os.makedirs(write_dir)
    # Download file
    with contextlib.closing(requests.get(url, stream=True, timeout = timeout)) as r1:
        with open(local_filename, 'wb') as f:
            for chunk in r1.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    return local_filename



def download_to_tree(url, base_dir, overwrite = False, check_integrity = False):
    """Download an ocean product file and automatically write it to the right location

    The idea is that the function immediately knows where to write the file
    by parsing the filename (present in url)
    Directories where data are downloaded do not need to exist before running the function
    Similarly to download_file, the function will raise a ConnectionError (via requests) if a connection
    cannot be established with the server (e.g.: network is down) and an HttpResourceNotAvailable
    if the file appear not to exist on the server. It might be worth re-trying when catching requests.ConnectionError,
    going to the next file is probably the best way if catching a HttpResourceNotAvailable

    Args:
        url (str): download url
        base_dir (str): root of the archive tree on the host
        overwrite (bool): Should the file be overwritten if already existing on local host
        check_integrity (bool): Only makes sense if overwrite is set to False (when updating the archive)

    Returns:
        str: The filename of the downloaded file
    """
    write_dir = path_builder(url, data_root=base_dir, add_file = False)
    file_path = download_file(url, write_dir, overwrite = overwrite, check_integrity = check_integrity)
    return file_path


def download_robust(url, base_dir, n_retries = 5, pause_retries = 10, overwrite = False, check_integrity = False):
    """Robust download of a list of urls

    Handles connection errors, optionally check for existing files and integrity
    Suitable for real time use and for updating an archive without overwriting existing data

    Args:
        url (str): Download url
        base_dir (str): root of the archive tree on the host
        n_retries (int): Number of retries when the download fails because of a ConnectionError
        pause_retries (int): Duration (in seconds) between retries
        overwrite (bool): Should existing files on the host be overwritten
        check_integrity (bool): Only makes sense if overwrite is set to False (when updating the archive)

    Returns:
        Boolean, True when successful, False otherwise
    """
    n = 1
    while n <= n_retries:
        try:
            file_path = download_to_tree(url, base_dir, overwrite = overwrite, check_integrity = check_integrity)
            return file_path
        except requests.ConnectionError:
            n += 1
            overwrite = True # In case file has been partly downloaded 
            time.sleep(pause_retries)
        except HttpResourceNotAvailable:
            warnings.warn(url + ' not downloaded. Not found on server')
            return None
        except Exception as e:
            warnings.warn(url + ' not downloaded. Unknown reason')
            return None
    warnings.warn(url + ' not downloaded. Max retries reached')
    return None
