"""
    Youtube Subscription Module that interacts
    with the Youtube API to get information on
    a channel's activity mainly their channel name
    and the channel's latest upload.

"""

from datetime import datetime
import socket
import requests
import isodate

############################################
# Function for testing internet connection #
############################################

def is_connected():
    """
        Function to check if connected to the internet 

    Returns:
        bool: True if connected, False otherwise
    """
    try:
        sock = socket.create_connection(("www.google.com",80))
        if sock is not None:
            sock.close()
        return True
    except OSError:
        pass
    return False


#####################################
# Class for Subscription Exceptions #
#####################################

class SubException(Exception):
    """
       Exception class used for custom exceptions when 
       interacting with the Youtube API. Provides
       a code for ease of identification
    """
    def __init__(self, message, code=None):
        super().__init__(message)  # Call the base class constructor
        self.code = code  # Optional error code

    def __str__(self):
        if self.code is not None:
            return f"{self.args[0]} (Error Code: {self.code})"
        return self.args[0]

############################
# Class for a Subscription #
############################

class Sub:
    """Object for interfacing with Youtube API
       to get the information for tracking the 
       latest uploads of a youtube channel
    """
    def __init__(self, api_key, *args):
        # listing all the attributes of the sub here
        # some of these are dummy values
        self._api_key = api_key
        self._updated = False
        self._latest_upload_time = None
        self._latest_upload_duration = 0
        self._handle = None
        self._name = None
        self._id = None
        self._uploads_id = None
        self._latest_upload = None
        self._latest_video_url = None
        self._watched_latest = None
        self._not_interested = None
        self._update_freq = None

        # first things first: check if we are connected to the internet
        if not is_connected():
            raise SubException("Failed to connect to the internet, check connection.", 56)

        if len(args) > 2:
            raise SubException("Provided too many arguments for creating a subscription", 22)

        if len(args) < 1:
            raise SubException("Provided not enough arguments for creating a subscription", 18)

        if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], dict):
            self.import_json(args[0], args[1])

        elif isinstance(args[0], str):
            self.create_new_sub(args[0])

    def import_json(self, handle:str, data:dict):
        """Populate the sub attributes from 
           the given json data
           This is a helper for the constructor

        Args:
            handle (str): the youtube channel handle
            data (dict): the data associated with the channels entry in 
            the youtubechannels.json file
        """
        # json object
        # detected fill in
        # class attributes
        self._handle = handle
        self._url = data['url']
        self._name = data['name']
        self._latest_upload = data['latest upload']
        datetime_format = "%Y-%m-%dT%H:%M:%SZ"
        self._latest_upload_time = datetime.strptime(data['latest upload time'], datetime_format)
        self._latest_video_url = data['latest video url']
        self._id = data['id']
        self._uploads_id = data['uploads id']

        if 'update rate' in data:
            self._update_freq = int(data['update rate'])
        else:
            # default
            self._update_freq = 1

        if 'watched latest' in data:
            self._watched_latest = bool(data['watched latest'])
        else:
            self._watched_latest = False

        if 'not_interested' in data:
            self._not_interested = bool(data['not_interested'])
        else:
            self._not_interested = False

        if 'duration' in data:
            self._latest_upload_duration = data['duration']
        else:
            self._latest_upload_duration = 'Unknown'

        # do check in here to see if
        # we need to update
        # the latest video info
        # different update
        # need to decide how often to update
        # do not wait for the update
        # period to end if the channel was marked
        # not interested
        time_diff = datetime.now() - self._latest_upload_time
        if time_diff.days >= self._update_freq or self._not_interested:
            # check for new content if the
            # sub hasn't uploaded in
            # a few days
            self.update_time_of_latest_upload()

    def create_new_sub(self, handle:str):
        """Generate a new subscription based
           on the given handle.

           This is a helper for the constructor
           that gathers the information needed
           to track a channel's upload activity

        Args:
            handle (str): the handle for the 
            youtube channel
        """
        # detected string
        # could be a handle
        # need to validate it
        pos_sub_url = "https://www.youtube.com/@" + handle

        try:
            response = requests.get(pos_sub_url, allow_redirects=True, timeout=5)
        except requests.RequestException as e:
            raise SubException("handle does not exist", 2) from e

        if response.status_code == 404:
            msg = f"The handle, {handle}, does not exist. Check youtube for the correct handle"
            raise SubException(msg, 3)

        self._handle = handle
        self._url = pos_sub_url

        # Found that the handle does exist
        # now scrape the site code
        # for the channel id
        # because this is directly linked
        # to the handle rather than
        # using youtube api to find it
        # because their api is dumb
        # and does not have a feature
        # to directly get the channel id
        handle_site_scrape = response.text
        scrape_key_word = "youtube.com/channel/"
        start_index_of_id = handle_site_scrape.find(scrape_key_word) + len(scrape_key_word)
        end_index_of_id = start_index_of_id + handle_site_scrape[start_index_of_id:].find('"')
        self._id = handle_site_scrape[start_index_of_id:end_index_of_id]

        # now with the channel id
        # and upload id using neat trick of noticing the pattern)
        # it will be super easy to query the youtube api
        # for the channel fancy name

        try:
            details_info = "/channels?part=snippet,contentDetails&id=self._id"
            details_url = self.get_yt_api_req_url(details_info)

            details_response = requests.get(details_url, timeout=5)
            details_data = details_response.json()
            channel_details = details_data['items'][0]
            self._name = channel_details['snippet']['title']
            self._uploads_id = channel_details['contentDetails']['relatedPlaylists']['uploads']
        except requests.RequestException as e:
            msg = "Ran into an error with getting the channel's fancy name:"
            raise SubException(f"{msg} {e.strerror}",
                                e.errno) from e

        self.update_time_of_latest_upload()

        # defaults for sub attributes that
        # need to be set when created
        self._update_freq = 1
        self._watched_latest = False
        self._not_interested = False

    def make_json(self):
        """Generates a json object of the 
           the current youtube subscription used for
           storing the data

        Returns:
            dict: the json object representation of the sub object
        """
        return {
            'name': self._name,
            'url' : self._url,
            'id' : self._id,
            'uploads id' : self._uploads_id,
            'latest upload' : self._latest_upload,
            'latest upload time' : self._latest_upload_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            'latest video url' : self._latest_video_url,
            'duration' : self._latest_upload_duration,
            'update rate': self._update_freq,
            'watched latest': self._watched_latest,
            'not_interested':self._not_interested
        }

    def get_yt_api_req_url(self, info:str):
        """Get a url to use for making
           a request to the youtube api

        Args:
            info (str): the data that will be requested
            i.e. the part after the last '/' api url below
            https://www.googleapis.com/youtube/v3/

        Returns:
            str: the full url for the request
        """
        base_url = "https://www.googleapis.com/youtube/v3/"
        key_suffix = f"&key={self._api_key}"

        return base_url + info + key_suffix

    def latest_upload_time(self):
        """Gets the time that the latest video
           from the channel was uploaded

        Returns:
            datetime: the time that the channel uploaded
            their latest video
        """
        return self._latest_upload_time

    def __str__(self):
        if self._latest_upload_duration == 'Unknown':
            duration_str = self._latest_upload_duration
        else:
            duration_str = isodate.parse_duration(self._latest_upload_duration)

        sub_str = f"{self._name}'s ({self._handle}) latest video:\n"
        sub_str += f"\ttitle: {self._latest_upload}\n"
        sub_str += f"\turl: {self._latest_video_url}\n"
        sub_str += f"\tduration: {duration_str}"

        return sub_str

    @property
    def name(self):
        """Get the fancy name of the youtube channel

        Returns:
            str: the fancy name of the youtube channel
        """
        return self._name

    def update_time_of_latest_upload(self):
        """

        Raises:
            SubException: _description_
            SubException: _description_
            SubException: _description_
            SubException: _description_
            SubException: _description_
            SubException: _description_
            SubException: _description_
        """
        playlist_info = f"playlistItems?part=snippet&playlistId={self._uploads_id}&maxResults=1"
        playlist_url = self.get_yt_api_req_url(playlist_info)

        latest_vid_id = None
        # getting the latest upload from the channel
        try:
            playlist_response = requests.get(playlist_url, timeout=5).json()

            if 'items' not in playlist_response or not playlist_response['items']:
                raise SubException("Could not find latest video uploads from " + self._name, 7)

            latest_video = playlist_response['items'][0]['snippet']
            latest_upload_time = datetime.strptime(latest_video['publishedAt'],
                                                    "%Y-%m-%dT%H:%M:%SZ")
            # check if the latest video is different from
            # the currently stored video
            if self._latest_upload_time is None or latest_upload_time != self._latest_upload_time:
                self._latest_upload = latest_video['title']
                self._latest_upload_time = latest_upload_time
                latest_vid_id = latest_video['resourceId']['videoId']
                self._latest_video_url = f'https://www.youtube.com/watch?v={latest_vid_id}'


                # also set this to false because if a new video is out the user hasn't watched it
                self._watched_latest = False
                self._updated = True
                # set this to false because the user needs a
                # chance to determine if the new video is of interest
                self._not_interested = False

        except requests.urllib3.exceptions.MaxRetryError as e:
            raise SubException(e.reason, 7000) from e

        except requests.ConnectionError as e:
            raise SubException(e.strerror, e.errno) from e

        except requests.RequestException as e:
            raise SubException(e.strerror, e.errno) from e

        # getting the duration of the video
        if latest_vid_id is not None:
            duration_info = f"videos?part=contentDetails&id={latest_vid_id}&maxResults=1"
            duration_url = self.get_yt_api_req_url(duration_info)

            try:
                dur_resp = requests.get(duration_url, timeout=5).json()
                self._latest_upload_duration = dur_resp['items'][0]['contentDetails']['duration']

            except requests.urllib3.exceptions.MaxRetryError as e:
                raise SubException(e.reason, 45) from e

            except requests.ConnectionError as e:
                raise SubException(e.strerror, e.errno) from e

            except requests.RequestException as e:
                raise SubException(e.strerror, e.errno) from e

    @property
    def new_video(self):
        """Returns whether the channel
           has a new video

        Returns:
            bool: True if a new video was uploaded
        """
        return self._updated

    def change_update_frequency(self, new_update_freq):
        """Set a new update frequency for the subscription

        Args:
            new_update_freq (float): the amount of days to wait
            before checking if a channel has uploaded a new video
        """
        self._update_freq = new_update_freq

    @property
    def have_watched(self):
        """Returns whether the user has 
           watched the latest video from the channel

        Returns:
            bool: True if the latest video was watched
        """
        return self._watched_latest

    def just_watched(self):
        """Sets the watched attribute to 
           True because the user has watched the
           latest video of this channel
        """
        self._watched_latest = True

    def not_interested(self):
        """Sets the not interested attribute
           to True because the user marked the 
           latest video of the channel as not interesting
        """
        self._not_interested = True

    @property
    def is_not_interested(self):
        """Returns whether the latest 
           video of this channel was marked as not 
           interesting.

        Returns:
            bool: True if the video was 
            marked as not interesting by the user
        """
        return self._not_interested

    @property
    def latest_video_link(self):
        """Gets the url for the latest
           video from the channel

        Returns:
            str: url of the latest video
            uploaded by the channel
        """
        return self._latest_video_url

    @property
    def handle(self):
        """Gets the handle of the youtube channel

        Returns:
            str: the handle of the youtube channel
        """
        return self._handle
