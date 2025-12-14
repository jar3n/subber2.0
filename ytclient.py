# youtube_client.py
from datetime import datetime
import requests

class YoutubeException(Exception):
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

        data = self._session.get(playlist_url, timeout=5).json()
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

        data = self._session.get(url, timeout=5).json()
        return data["items"][0]["contentDetails"]["duration"]

    def verify_handle(self, handle:str):
        """Verify the given handle
           is attached to a youtube channel

        Args:
            handle (str): the youtube channel handle
            which is found on channel pages under the
            display name with an '@' in front of it
        """
        handle_url = f"http://www.youtube.com/@{handle}"

        response = self._session.get(handle_url, timeout=5)

        if response.status_code == 404:
            raise YoutubeException(f"{handle} is not linked to any channel, check the spelling.")

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

        except YoutubeException as e:
            raise e
        except requests.RequestException as e:
            raise YoutubeException(e.strerror) from e

    def get_channel_details(self, channel_id:str) -> tuple:
        """Get the upload id assigned to the
           channel 

        Args:
            channel_id (str): the alphanumeric 
            id assigned to the channel 

        Returns:
            tuple: a set containing details 
            used for the channel. Indexes below:
            0: uploads id
            1: channel display name
        """
        try:
            channel_details_url = self.create_api_url(
                f"channels?part=snippet,contentDetails&id={channel_id}"
            )
            resp = self._session.get(channel_details_url)
            resp_data = resp.json()
            return (
                resp_data['items'][0]['snippet']['title'],
                resp_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            )
        except YoutubeException as e:
            raise e
        except requests.RequestException as e:
            raise YoutubeException(e.strerror) from e
