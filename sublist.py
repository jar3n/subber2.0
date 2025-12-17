"""
    Youtube Channel Subscription List
    Module responsible for managing the 
    subscriptions and saving them to the local file 
    for tracking. This file also updates the list
    and is backend for displaying the list

"""
import sys
import json
from os import mkdir
from os.path import dirname, exists, join, abspath
from datetime import datetime
import multiprocessing as mp
from multiprocessing import Manager, Queue
from queue import Empty
from concurrent.futures import ProcessPoolExecutor
from enum import Enum

# custom modules
from sub import Sub
from ytclient import YouTubeClient, YouTubeException

#############################################################
# Class for getting the Subscriptions List and Modifying it #
#############################################################

class SubscriptionList:
    """
        Manages the list of channels
        that are being tracked in the file
    """
    class QueueLabels(Enum):
        """
            Labels for subs to identify
            the ones to list 
        """
        FAILED = -1
        UPDATED = 1
        NORMAL = 0
        IGNORE = -2

    def __init__(self, api_key):

        # get the api key to use for youtube api requests
        self._api_key = api_key

        # set up the file path
        if getattr(sys, 'frozen,', False):
            executable_path = dirname(sys.executable)
        else:
            executable_path = dirname(abspath(__file__))
            local_dir = join(executable_path, 'localstuff')
            channel_file_path = join(local_dir, "youtubechannels.json")
        if not exists(local_dir):
            mkdir(local_dir)

        if not exists(channel_file_path):
            with open(channel_file_path,'w',encoding='utf-8') as file:
                file.write('{\n"subscriptions" : {}\n}')

        self._file_path = channel_file_path
        # load the data
        # from the file
        with open(self._file_path, 'r', encoding='utf-8') as file:
            self._subs_json = json.load(file)

        self._no_subs = self._subs_json["subscriptions"] == {}
        self._subs = self._subs_json["subscriptions"]
        if self._no_subs:
            self._sub_count = 0
        else:
            self._sub_count = len(list(self._subs))

        # init the youtube client
        self._client = YouTubeClient(self._api_key)

        # set up the multiprocessing
        # this determines how to create subprocesses
        mp.set_start_method('fork')

    def store_list(self):
        """
            Store the list of json objects to the file
        """
        with open(self._file_path, 'w', encoding='utf-8') as file:
            self._subs_json["subscriptions"] = self._subs
            json.dump(self._subs_json, file, ensure_ascii=False, indent=4)

    def is_subbed(self, handle):
        """
            Check if there is a handle in the list that matches 
            the given handle
        Args:
            handle (string): the youtube channel handle to check for 
            in the list

        Returns:
            bool: returns True if the handle is in the list 
            and False otherwise.
        """
        handles = list(self._subs.keys())
        return handle in handles

    def add_subscription(self, handle:str):
        """
            Adds a entry to the json list with data from 
            the given handle to track their latest updates.
        Args:
            handle (str): the handle to add to the list to track
            for latest uploads

        Raises:
            e: a Sub exception error depends on whether there is an internet connection
            or the handle is not associated with a youtube channel
        """

        if not self.is_subbed(handle):
            try:
                # info to get
                # channel id
                # uploads id
                # url
                # name
                channel_id = self._client.get_channel_id(handle)
                uploads_id, channel_name = self._client.get_channel_details(channel_id)
                channel_url = self._client.get_channel_url(handle)

                sub_data = {
                    "name": channel_name,
                    "url": channel_url,
                    "id" : channel_id,
                    "uploads id": uploads_id
                    }

                new_sub = Sub(handle, sub_data)

                self.update_sub_json(new_sub)
                print(f"Subscribed to {new_sub.name}")
            except YouTubeException as e:
                raise e
        else:
            sub = Sub(handle, self._subs[handle])
            print(f"You are already subscribed to {sub.name}")

    def remove_subscription(self, handle:str):
        """
            Removes a subscription frol the file 
            and stops tracking it
        Args:
            handle (string): handle to remove from subscriptions
        """

        if self.is_subbed(handle):
            unsub = Sub(handle, self._subs.pop(handle))
            self.store_list()
            print(f"Unsubscribed from {unsub.name}")
        else:
            print(f"You were never subscribed to {handle}")

    def check_sub(self, sub_json_key:str, sub_json_value:str, queue:Queue):
        """
           Thread safe function for checking the status 
           of a channel and adding it to the shared queue
           with a label indicating whether the channel
           failed to update, updated, or to ignore it 
           because it has no updates

        Args:
            sub_json_key (string): the handle which is also the key 
            for the channel json object stored in the file
            sub_json_value (string): the set of attributes tied to
            the channel handle such as latest video and last upload time, etc.
            queue (): _description_
        """
        sub = Sub(sub_json_key, sub_json_value)

        try:
            # check if sub needs refresh
            if sub.should_refresh(datetime.now):
                title, pub_date, url, dur = self._client.get_latest_upload(sub.uploads_id)
                # check if the latest is different from the latest
                # stored in file
                # its possible if the video was marked as not interesting
                if sub.latest_upload_time != pub_date:
                    # this means the latest is different from
                    # the video stored in the file
                    sub.apply_update(title, pub_date, url, dur)

                    queue.put([sub, SubscriptionList.QueueLabels.UPDATED])
                else:
                    # if the latest video is the same as the stored video
                    # then the sub was not updated so its normal
                    queue.put([sub, SubscriptionList.QueueLabels.NORMAL])
            elif sub.watched or sub.not_interested:
                # if should not refresh and watched or not interesting
                # then ignore it so it does not display in the list
                queue.put([sub, SubscriptionList.QueueLabels.IGNORE])
            else:
                queue.put([sub, SubscriptionList.QueueLabels.NORMAL])

        except YouTubeException as yte:
            queue.put([sub, SubscriptionList.QueueLabels.FAILED, yte])

    def update_sub_json(self, sub:Sub):
        """
            Helper function that updates
            the json object stored in the file
            for the given sub

        Args:
            sub (Sub): subscription object with updated
            information to store in file
        """

        self._subs[sub.handle] = sub.data
        self.store_list()

    def display_sub_list(self, categorized_uploads:dict, failed_sub_checks:list):
        """display the subscriptions latest content to the terminal

        Args:
            categorized_uploads (dict): a dictionary
            with the latest uploads of the subscribed youtube channels
            failed_sub_checks (list): a list of the channels
            who failed when they were checked
        """
        num_cats_with_no_vids = 0
        for key,item in categorized_uploads.items():
            if item["len"] > 0:
                item["uploads"].sort(key=
                lambda sub: sub.latest_upload_time(), reverse=True)
                print("----------------------------")
                print(f"Uploads that happened {key} ({item['len']}):")
                print("----------------------------\n")
                for sub in item["uploads"]:
                    print(sub)
                    print("\n")
            else:
                num_cats_with_no_vids += 1

        if num_cats_with_no_vids == len(list(categorized_uploads.keys())):
            print("You have seen the all latest content from the" +
                    "channels you have subscribed to that could be checked.")

        if len(failed_sub_checks) == 0:
            print("All of your subscriptions were successfully checked.")
        else:
            print("The following channels were not successfully checked.")
            for channel in failed_sub_checks:
                print(f" - {channel}")

    def list_subs(self):
        """
            List the subscriptions with their
            latest videos if they have not been watched or
            marked as not interesting. Also update
            all the subscriptions to see if ones have new
            videos.
        """
        if self._no_subs:
            print("There are no subscriptions")
        else:
            # imagine splitting it up based
            # on recent upload
            # section on uploading today
            # section on uploading within the week
            # section on not uploaded in a long time
            categorized_uploads = {
                "today":{
                    "uploads":[],
                    "len": 0
                },
                "this week":{
                    "uploads":[],
                    "len": 0
                },
                "a while ago":{
                    "uploads":[],
                    "len": 0
                }
            }

            # do some multiprocessing to
            # process the subs asynchronously
            with Manager() as mpm:
                sub_queue = mpm.Queue()
                handles = list(self._subs_json["subscriptions"].keys())
                channel_data = list(self._subs_json["subscriptions"].values())
                failed_sub_checks = []

                with ProcessPoolExecutor(max_workers=mp.cpu_count()) as pool_exe:
                    for i in range(self._sub_count):
                        pool_exe.submit(self.check_sub,
                                        handles[i],
                                        channel_data[i],
                                        sub_queue)

                    completed = 0
                    while completed < self._sub_count:
                        try:
                            # got an item from the queue
                            proc_result = sub_queue.get(timeout=0.5)

                            completed += 1
                            if proc_result[1] == SubscriptionList.QueueLabels.UPDATED or \
                                proc_result[1] == SubscriptionList.QueueLabels.NORMAL:
                                # this means the sub can be added to the display lists
                                # first if updated then update the json

                                if proc_result[1] == SubscriptionList.QueueLabels.UPDATED:
                                    self.update_sub_json(proc_result[0])

                                # now determine the list to add the
                                # sub to

                                time_diff = datetime.now() - proc_result[0].latest_upload_time
                                if time_diff.days <= 0:
                                    categorized_uploads["today"]["uploads"].append(proc_result[0])
                                    categorized_uploads["today"]["len"] += 1

                                elif time_diff.days <= 7:
                                    categorized_uploads["this week"]["uploads"].append(
                                        proc_result[0]
                                        )
                                    categorized_uploads["this week"]["len"] += 1

                                else:
                                    categorized_uploads["a while ago"]["uploads"].append(
                                        proc_result[0]
                                        )
                                    categorized_uploads["a while ago"]["len"] += 1

                            elif proc_result[1] == SubscriptionList.QueueLabels.FAILED:
                                # this means it failed
                                # so add it to the list
                                failed_sub_checks.append(proc_result[0])

                        except Empty:
                            # no item was retreived so continue checking
                            pass

            self.display_sub_list(categorized_uploads, failed_sub_checks)

    def set_sub_update_freq(self, handle:str, new_update_freq:float):
        """
            Set the period of time between checks for new 
            uploads to the channel

        Args:
            handle (string): the channel to set the update frequency
            new_update_freq (float): number of days between upload checks
        """

        if self.is_subbed(handle):
            # get the sub and change its update freq
            sub = Sub(handle, self._subs[handle])
            sub.set_update_frequency(new_update_freq)

            # add the new json to the list and store it
            self.update_sub_json(sub)
            print(f"Set the update frequency for {sub.name} to {new_update_freq} days.")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")

    def set_sub_watched(self, handle:str):
        """
            Set a channel to watched because
            their latest video was watched

        Args:
            handle (string): handle of channel to mark
            as watched latest
        """

        if self.is_subbed(handle):
            # get the sub and set the latest
            # has been watched
            sub = Sub(handle, self._subs[handle])
            sub.mark_watched()

            # save the update
            self.update_sub_json(sub)
            print(f"Marked that you watched the latest from {sub.name}")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")

    def set_sub_not_interested(self, handle:str):
        """
            Mark the latest video from a subscription 
            as not interested 

        Args:
            handle (string): handle of the channel that 
            is going to be marked as not interested
        """
        if self.is_subbed(handle):
            sub = Sub(handle, self._subs[handle])
            sub.mark_not_interested()

            self.update_sub_json(sub)
            print(f"Marked that you are not interested in the latest from {sub.name}")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")


    def set_watched_all(self):
        """
            Set all the channels to watched 
            meaning the latest videos 
            from all the channels have been watched
        """
        for handle, sub_data in self._subs:
            sub = Sub(handle, sub_data)
            sub.mark_watched()
            self._subs[sub.handle] = sub.data

        self.store_list()
        print("You watched all the latest videos!!")

    def get_sub(self, handle:str):
        """
            Retrieve a subscription from the list
            and return it as a Sub object

        Args:
            handle (string): handle of the desired subscription

        Returns:
            Sub: the subscription object with associated properties
        """
        if not self.is_subbed(handle):
            return None

        return Sub(handle, self._subs[handle])
