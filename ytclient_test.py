# Unit Testing for the youtube client class
# so I don't have a headache of integration hell 
# or at least I reduce it a little bit

import configparser
from os.path import dirname, abspath
from pathlib import Path
from inspect import getsourcefile
from datetime import datetime
import pytest

from ytclient import YouTubeClient, YoutubeException


# ---------- Set up stuff ----------

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
    except configparser.MissingSectionHeaderError as e:
        raise e

    # return a subscription list object initialized with the key
    return cp['key']['api key']


_API_KEY = check_api_key()
Client = YouTubeClient(_API_KEY)

# API url endpoint
API_URL = "https://www.googleapis.com/youtube/v3/"

# I made a channel for running these tests
# here are the details
# channel name: Dummy Channel for Testing
DUMMY_CHAN_DISP_NAME = "Dummy Channel for Testing"
# handle: dummychannelfortesting
DUMMY_CHAN_HANDLE = "dummychannelfortesting"
# channel id: UCfJKSQTe4XNp53aSZgrSnww
DUMMY_CHAN_ID = "UCfJKSQTe4XNp53aSZgrSnww"
# uploads id: NEED TO GET
DUMMY_CHAN_UPLOADS_ID = "UUfJKSQTe4XNp53aSZgrSnww"
# video id for the only video on the channel: FXYMafSThKs
DUMMY_CHAN_VID_ID = "FXYMafSThKs"
DUMMY_CHAN_VID_DUR = "PT9S"
DUMMY_CHAN_VID_NAME = "Ollie Over Phone"
DUMMY_CHAN_VID_PUB_DATE = datetime.strptime("2025-12-16T23:20:45Z", "%Y-%m-%dT%H:%M:%SZ")
DUMMY_CHAN_VID_URL = f"https://www.youtube.com/watch?v={DUMMY_CHAN_VID_ID}"

# ---------- Tests ----------

def test_create_api_url():
    """Testing if the url created
	is what is exptected
	The test here is simple
	and uses the request url for
	getting the channel uploads id"""

    uploads_id = "q34234dsfqe3t4" # not a real uploads id
    suffix = f"playlistItems?part=snippet&playlistId={uploads_id}&maxResults=1"
    full_url = API_URL + suffix + f"&key={_API_KEY}"
    assert full_url == Client.create_api_url(suffix)

def test_verify_handle():
    """Testing the verify channel handle
	function can confirm 
    """
    assert isinstance(Client.verify_handle(DUMMY_CHAN_HANDLE), str) is True

def test_verify_handle_fail():
    """Test the function raises an exception
    if the given handle is not linked
    to a channel
    """
    with pytest.raises(YoutubeException) as execinfo:
        Client.verify_handle("jamesrenglander")

    assert " is not linked to any channel" in str(execinfo)

def test_get_channel_id():
    """Testing getting the channel id
	for a channel using the dummy channel
	"""
    assert DUMMY_CHAN_ID == Client.get_channel_id(DUMMY_CHAN_HANDLE)

def test_get_channel_details():
    """Testing getting the channel's
	   display name and uploads id
	"""
    resps_disp_name, resp_ups_id = Client.get_channel_details(DUMMY_CHAN_ID)

    assert resp_ups_id == DUMMY_CHAN_UPLOADS_ID and resps_disp_name == DUMMY_CHAN_DISP_NAME

def test_get_duration():
    """Testing getting the duration 
       of a video from the video id
    """
    assert DUMMY_CHAN_VID_DUR == Client.get_duration(DUMMY_CHAN_VID_ID)

def test_get_latest_upload():
    """Test getting the latest
       upload from the dummy channel
    """
    title, pub_date, url, dur = Client.get_latest_upload(DUMMY_CHAN_UPLOADS_ID)

    assert title == DUMMY_CHAN_VID_NAME
    assert pub_date == DUMMY_CHAN_VID_PUB_DATE
    assert url == DUMMY_CHAN_VID_URL
    assert dur == DUMMY_CHAN_VID_DUR
