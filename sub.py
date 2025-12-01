"""
    Youtube Subscription Module that interacts
    with the Youtube API to get information on
    a channel's activity mainly their channel name
    and the channel's latest upload.

"""

import requests
import socket
from datetime import datetime
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
    def __init__(self, api_key, *args):
        self._api_key = api_key
        self._api_base_url = "https://www.googleapis.com/youtube/v3"
        self._updated = False
        self._latest_upload_time = None
        self._latest_upload_duration = 0

        # first things first: check if we are connected to the internet
        if not is_connected():
            raise SubException("Failed to connect to the internet, check connection.", 56)

        if len(args) > 2:
            raise SubException("Provided too many arguments for creating a subscription", 22)
        elif len(args) < 1:
            raise SubException("Provided not enough arguments for creating a subscription", 18)
        else:
            if len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], dict):
                # json object 
                # detected fill in 
                # class attributes

                self._handle = args[0]
                self._url = args[1]['url']
                self._name = args[1]['name']
                self._latest_upload = args[1]['latest upload']
                self._latest_upload_time = datetime.strptime(args[1]['latest upload time'], "%Y-%m-%dT%H:%M:%SZ")
                self._latest_video_url = args[1]['latest video url']
                self._id = args[1]['id']
                self._uploads_id = args[1]['uploads id']

                if 'update rate' in args[1]:
                    self._update_freq = int(args[1]['update rate'])
                else:
                    # default 
                    self._update_freq = 1
                
                if 'watched latest' in args[1]:
                    self._watched_latest = bool(args[1]['watched latest'])
                else:
                    self._watched_latest = False
                
                if 'not_interested' in  args[1]:
                    self._not_interested = bool(args[1]['not_interested'])
                else:
                    self._not_interested = False
                
                if 'duration' in args[1]:
                    self._latest_upload_duration = args[1]['duration']
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


            elif isinstance(args[0], str):
                # detected string 
                # could be a handle
                # need to validate it
                base_url = "https://www.youtube.com/@"
                pos_sub_url = base_url + args[0]

                try:
                    response = requests.get(pos_sub_url, allow_redirects=True)
                except requests.RequestException:
                    raise SubException("handle does not exist", 2)

                if response.status_code == 404:
                    raise SubException(f"The handle, {args[0]}, does not exist. Please check youtube for the correct handle.", 3)

                self._handle = args[0]
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
                    details_url = f"{self._api_base_url}/channels?part=snippet,contentDetails&id={self._id}&key={self._api_key}"
                    details_response = requests.get(details_url)
                    details_data = details_response.json()
                    self._name = details_data['items'][0]['snippet']['title']
                    self._uploads_id = details_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                except requests.RequestException as e:
                    raise SubException(f"Ran into an error with getting the channel's fancy name: {e.strerror}", e.errno)

                self.update_time_of_latest_upload()

                # defaults for sub attributes that 
                # need to be set when created
                self._update_freq = 1
                self._watched_latest = False
                self._not_interested = False
                
    def make_json(self):
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
    
    def get_latest_upload_time(self):
        return self._latest_upload_time
    
    def __str__(self):
        if self._latest_upload_duration == 'Unknown':
            duration_str = self._latest_upload_duration
        else:
            duration_str = isodate.parse_duration(self._latest_upload_duration)
        return f"{self._name}'s ({self._handle}) latest video:\n  title: {self._latest_upload}\n  url: {self._latest_video_url}\n  duration: {duration_str}"
    
    def get_name(self):
        return self._name
    
    def update_time_of_latest_upload(self):
        playlist_url = f'{self._api_base_url}/playlistItems?part=snippet&playlistId={self._uploads_id}&maxResults=1&key={self._api_key}'
        latest_vid_id = None
        # getting the latest upload from the channel
        try:
            playlist_response = requests.get(playlist_url).json()
            
            if 'items' not in playlist_response or not playlist_response['items']:
                raise SubException("Could not find latest video uploads from " + self._name, 7)
            

            latest_video = playlist_response['items'][0]['snippet']
            latest_upload_time = datetime.strptime(latest_video['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
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
                # set this to false because the user needs a chance to determine if the new video is of interest
                self._not_interested = False
        
        except requests.urllib3.exceptions.MaxRetryError as e:
            raise SubException(e.strerror, e.errno)
        
        except requests.ConnectionError as e:
            raise SubException(e.strerror, e.errno)

        except requests.RequestException as e:
            raise SubException(e.strerror, e.errno)
        
        # getting the duration of the video
        if latest_vid_id is not None:
            duration_url = f'{self._api_base_url}/videos?part=contentDetails&id={latest_vid_id}&maxResults=1&key={self._api_key}'
            try: 
                duration_response = requests.get(duration_url).json()
                self._latest_upload_duration = duration_response['items'][0]['contentDetails']['duration']

            except requests.urllib3.exceptions.MaxRetryError as e:
                raise SubException(e.strerror, e.errno)
        
            except requests.ConnectionError as e:
                raise SubException(e.strerror, e.errno)

            except requests.RequestException as e:
                raise SubException(e.strerror, e.errno)      
    
    def new_video(self):
        return self._updated
    
    def change_update_frequency(self, new_update_freq):
        self._update_freq = new_update_freq
    
    def have_watched(self):
        return self._watched_latest
    
    def just_watched(self):
        self._watched_latest = True
    
    def not_interested(self):
        self._not_interested = True
    
    def is_not_interested(self):
        return self._not_interested
    
    def latest_video_link(self):
        return self._latest_video_url
    
    @property
    def handle(self):
        return self._handle
    
