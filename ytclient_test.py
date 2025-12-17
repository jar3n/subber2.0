"""
    This module runs unit tests for the Youtube Client Class.
    THis ensure that the class functions as expected and 
    retrieves the information needed for each video and 
    subscription.

"""

# Unit Testing for the youtube client class
# so I don't have a headache of integration hell
# or at least I reduce it a little bit


from datetime import datetime
import pytest

from ytclient import YouTubeClient, YoutubeException
from api_key_utils import check_api_key

# ---------- Set up stuff ----------

_API_KEY = check_api_key()
CLIENT = YouTubeClient(_API_KEY)

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
    assert full_url == CLIENT.create_api_url(suffix)

def test_verify_handle():
    """Testing the verify channel handle
	function can confirm 
    """
    assert isinstance(CLIENT.verify_handle(DUMMY_CHAN_HANDLE), str) is True

def test_verify_handle_fail():
    """Test the function raises an exception
    if the given handle is not linked
    to a channel
    """
    with pytest.raises(YoutubeException) as execinfo:
        CLIENT.verify_handle("jamesrenglander")

    assert " is not linked to any channel" in str(execinfo)

def test_get_channel_id():
    """Testing getting the channel id
	for a channel using the dummy channel
	"""
    assert DUMMY_CHAN_ID == CLIENT.get_channel_id(DUMMY_CHAN_HANDLE)

def test_get_channel_details():
    """Testing getting the channel's
	   display name and uploads id
	"""
    resps_disp_name, resp_ups_id = CLIENT.get_channel_details(DUMMY_CHAN_ID)

    assert resp_ups_id == DUMMY_CHAN_UPLOADS_ID and resps_disp_name == DUMMY_CHAN_DISP_NAME

def test_get_duration():
    """Testing getting the duration 
       of a video from the video id
    """
    assert DUMMY_CHAN_VID_DUR == CLIENT.get_duration(DUMMY_CHAN_VID_ID)

def test_get_latest_upload():
    """Test getting the latest
       upload from the dummy channel
    """
    title, pub_date, url, dur = CLIENT.get_latest_upload(DUMMY_CHAN_UPLOADS_ID)

    assert title == DUMMY_CHAN_VID_NAME
    assert pub_date == DUMMY_CHAN_VID_PUB_DATE
    assert url == DUMMY_CHAN_VID_URL
    assert dur == DUMMY_CHAN_VID_DUR
