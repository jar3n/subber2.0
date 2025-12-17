"""
    Simple module to store the function
    used to get the api key from the configuration file.
"""

import configparser
from os.path import dirname, abspath
from pathlib import Path
from inspect import getsourcefile

class APIKeyRequestException(Exception):
    """Class for capturing exceptions
       when requesting the Youtube API
       Key from the config file.
    """
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return f"Error trying to retrieve Youtube API Key:\n{self._msg}"

def check_api_key():
    """
        Helper function to check for the api key configuration file
    """
    api_key_file = Path(f"{dirname(abspath(getsourcefile(lambda:0)))}/api_key")
    if not api_key_file.is_file():
        raise FileNotFoundError()

    cp = configparser.ConfigParser()
    try:
        cp.read(str(api_key_file))
    except configparser.MissingSectionHeaderError as mshe:
        raise APIKeyRequestException(mshe.message) from mshe
    except FileNotFoundError as fnfe:
        raise APIKeyRequestException(fnfe.strerror) from fnfe

    # return a subscription list object initialized with the key
    return cp['key']['api key']
