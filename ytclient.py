"""
    This module holds the Youtube Client Class.
    The class is responsible for interfacing between 
    the local subscriptions manager and the Youtube API.
    It is responsible for acquiring all the necessary info
    for tracking subscriptions locally. 

"""
from datetime import datetime
import requests

class YouTubeException(Exception):
    """Exception Class for Errors
       with getting the data from the 
       Youtube API
    """
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return f"Youtube API Error: {self._msg}"


class YouTubeClient:
    """
        This class interfaces with the 
        Youtube API to get data on the
        latest uploads from channels
    """
    _DT_FMT = "%Y-%m-%dT%H:%M:%SZ"
    _API_ENDPT = "https://www.googleapis.com/youtube/v3/"

    def __init__(self, api_key: str):
        self._key = api_key
        self._session = requests.Session()

    def make_get_request(self, url:str, timeout:int, is_json:bool) -> requests.models.Response:
        """Calls the requests session https get request
           with excedption handling

        Args:
            url (str): the webpage url to make the 
            get request to
            timeout (int): the amount of seconds to wait for 
            response before triggering an exception.
            is_json (bool): a boolean indicating the
            response is in the json format or not. True
            means the response is in json format.

        Returns:
            Response: The response object returned from the
            session.get() function
        """

        try:
            if is_json:
                resp = self._session.get(url, timeout=timeout).json()
            else:
                resp = self._session.get(url, timeout=timeout)

            return resp
        except requests.exceptions.ConnectionError as e:
            raise YouTubeException("Failed to connect to the internet.") from e

    def create_api_url(self, suffix:str) -> str:
        """Combine the given suffix data
           with the api key and the 
           api endpoint for convenince

        Args:
            suffix (str): _description_

        Returns:
            str: full api request url
        """
        return f"{self._API_ENDPT}{suffix}&key={self._key}"

    def get_latest_upload(self, uploads_id: str):
        """Retrieve the latest video 
           from the channel

        Args:
            uploads_id (str): the alphanumeric 
            id of the uploads playlist assigned 
            to the channel. Check the youtube API
            for the details on this.


        Returns:
            tuple: set containing the 
            details of the latest video from the
            channel. Indexes below:
            0: Title of the Video
            1: Upload Time
            2: URL
            3: Video Length
        """
        playlist_url = self.create_api_url(
            f"playlistItems?part=snippet&playlistId={uploads_id}&maxResults=1"
            )

        data = self.make_get_request(playlist_url, timeout=5, is_json=True)
        snippet = data["items"][0]["snippet"]

        video_id = snippet["resourceId"]["videoId"]
        published = datetime.strptime(
            snippet["publishedAt"], self._DT_FMT
        )

        duration = self.get_duration(video_id)

        return (
            snippet["title"],
            published,
            f"https://www.youtube.com/watch?v={video_id}",
            duration,
        )

    def get_duration(self, video_id: str) -> str:
        """Retrieve the length of a video

        Args:
            video_id (str): the alphanumeric 
            id string assigned to a video by youtube

        Returns:
            str: 
        """
        url = self.create_api_url(
            f"videos?part=contentDetails&id={video_id}&maxResults=1"
        )

        data = self.make_get_request(url, timeout=5, is_json=True)
        return data["items"][0]["contentDetails"]["duration"]

    def get_channel_url(self, handle:str):
        """Get the channel page url 
           

        Args:
            handle (str): the handle of the channel
        """
        return f"http://www.youtube.com/@{handle}"

    def verify_handle(self, handle:str):
        """Verify the given handle
           is attached to a youtube channel

        Args:
            handle (str): the youtube channel handle
            which is found on channel pages under the
            display name with an '@' in front of it
        
        Returns:
            the html as a string to use
            for scraping for the channel's id
        """
        handle_url = self.get_channel_url(handle)

        response = self.make_get_request(handle_url, timeout=5, is_json=False)

        if response.status_code == 404:
            raise YouTubeException(f"{handle} is not linked to any channel, check the spelling.")

        # return the html of the
        # page so it can be scraped
        # for the channel id
        return response.text

    def get_channel_id(self, handle:str) -> str:
        """Get the channel id for the 
           given handle 

        Args:
            handle (str): the handle of the
            channel 
        Returns:
            str: the alphanumeric id assigned
            to the channel with the given handle and 
            is used for getting details about the 
            channel
        """
        try:
            response = self.verify_handle(handle)

            # scrape the text from the response
            # for the channel id instead of
            # requesting it from the API

            scrape_key_phrase = "youtube.com/channel/"
            start_index_of_id = response.find(scrape_key_phrase) + len(scrape_key_phrase)
            end_of_index_of_id = start_index_of_id + response[start_index_of_id:].find('"')
            return response[start_index_of_id:end_of_index_of_id]

        except YouTubeException as e:
            raise e
        except requests.RequestException as e:
            raise YouTubeException(e.strerror) from e

    def get_channel_details(self, channel_id:str) -> tuple:
        """Get the upload id assigned to the
           channel and the channel's display name

        Args:
            channel_id (str): the alphanumeric 
            id assigned to the channel 

        Returns:
            tuple: a set containing details 
            used for the channel. Indexes below:
            0: display name 
            1: channel uploads playlist id
        """
        try:
            channel_details_url = self.create_api_url(
                f"channels?part=snippet,contentDetails&id={channel_id}"
            )
            resp_data = self.make_get_request(channel_details_url, timeout=5, is_json=True)
            return (
                resp_data['items'][0]['snippet']['title'],
                resp_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            )
        except YouTubeException as e:
            raise e
        except requests.RequestException as e:
            raise YouTubeException(e.strerror) from e
