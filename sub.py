"""
    This module is for a JSON wrapper class
    called Sub which provides more readable
    functions and properties used for accessing
    data from a subscription in the stored 
    json data created for tracking the youtube 
    subscriptions.
"""
from datetime import datetime
from typing import Any, Dict
import isodate


class Sub:
    """Lightweight JSON wrapper for a YouTube subscription."""

    _DT_FMT = "%Y-%m-%dT%H:%M:%SZ"

    def __init__(self, handle: str, data: Dict[str, Any]):
        self._handle = handle
        self._data = data

    # ---------- core ----------

    @property
    def handle(self) -> str:
        """Get the Youtube Channel Handle

        Returns:
            str: the channel handle
        """
        return self._handle

    @property
    def name(self) -> str:
        """Get the Display Name for the Channel

        Returns:
            str: the channel display name
        """
        return self._data["name"]

    @property
    def latest_upload_time(self) -> datetime:
        """Get the upload time of 
           the latest video from the channel

        Returns:
            datetime: the date and time of the 
            latest upload
        """
        return datetime.strptime(
            self._data["latest upload time"], self._DT_FMT
        )

    @property
    def update_frequency(self) -> int:
        """Get the update frequency of the 
           channel which is the amount 
           of days to wait after the latest 
           video upload of the channel to check 
           for a new video

        Returns:
            int: the update frequency
        """
        return int(self._data.get("update rate", 1))

    @property
    def watched(self) -> bool:
        """Get whether the latest video 
           was marked as watched by the 
           user

        Returns:
            bool: True if the latest video of this 
            channel was watched
        """
        return bool(self._data.get("watched latest", False))

    @property
    def not_interested(self) -> bool:
        """Get whether the latest video 
           from the channel was marked as
           not interesting by the user

           Marking a video as not interesting
           means the update frequency is ignored
           and the next time the channel is checked
           is the next time they request to list 
           the latest from the subscriptions

        Returns:
            bool: True if the latest video of the 
            channel is marked as not interested
        """
        return bool(self._data.get("not_interested", False))

    # ---------- state helpers ----------

    def should_refresh(self, now: datetime) -> bool:
        """Determine whether the channel should be checked
           for new content 

        Args:
            now (datetime): the current time

        Returns:
            bool: True if the latest video is older
            than the update frequency or if the latest 
            was marked as not interesting
        """
        if self.not_interested:
            return True
        return (now - self.latest_upload_time).days >= self.update_frequency

    def mark_watched(self) -> None:
        """Record that the user has 
           watched the latest video from the channel
        """
        self._data["watched latest"] = True

    def mark_not_interested(self) -> None:
        """Record that the user has indicated 
           the latest video from the channel 
           is not interesting
        """
        self._data["not_interested"] = True

    def apply_update(
        self,
        title: str,
        published_at: datetime,
        video_url: str,
        duration: str,
    ) -> None:
        """Update the video related data 
           for the channel based on the given information
        """
        self._data.update(
            {
                "latest upload": title,
                "latest upload time": published_at.strftime(self._DT_FMT),
                "latest video url": video_url,
                "duration": duration,
                "watched latest": False,
                "not_interested": False,
            }
        )

    # ---------- display ----------

    def __str__(self) -> str:
        duration = self._data.get("duration", "Unknown")
        if duration != "Unknown":
            duration = isodate.parse_duration(duration)

        return (
            f"{self.name}'s ({self.handle}) latest video:\n"
            f"\ttitle: {self._data['latest upload']}\n"
            f"\turl: {self._data['latest video url']}\n"
            f"\tduration: {duration}"
        )
