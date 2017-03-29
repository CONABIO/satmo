class HttpResourceNotAvailable(Exception):
    """ Custom exception for http resource availability """
    pass

class SeadasError(Exception):
    """Custom exception for when seadas does not exit with status 0"""
    pass
