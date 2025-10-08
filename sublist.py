
# python modules
import os, sys, json
from datetime import datetime

# custom modules
from sub import SubException, Sub

#############################################################
# Class for getting the Subscriptions List and Modifying it #
#############################################################

class SubscriptionList:
    def __init__(self, api_key):

        # get the api key to use for youtube api requests
        self._api_key = api_key

        # set up the file path
        if getattr(sys, 'frozen,', False):
            executable_path = os.path.dirname(sys.executable)
        else:
            executable_path = os.path.dirname(os.path.abspath(__file__))
            local_dir = os.path.join(executable_path, 'localstuff')
            channel_file_path = os.path.join(local_dir, "youtubechannels.json")
        
        if not os.path.exists(local_dir):
            os.mkdir(local_dir)

        if not os.path.exists(channel_file_path):
            with open(channel_file_path, 'w') as file:
                file.write('{\n"subscriptions" : {}\n}')

        self._file_path = channel_file_path
        
        # load the data
        # from the file
        with open(self._file_path, 'r') as file:
            self._subs_json = json.load(file)
        
        self._no_subs = self._subs_json["subscriptions"] == {}
        
    
    def store_list(self):
        # this function is called 
        # for storing the subs to
        # the file 
        # after any update is made
        with open(self._file_path, 'w') as file:
            json.dump(self._subs_json, file, ensure_ascii=False, indent=4)

    def is_subbed(self, handle):
        # check if the handle is
        handles = list(self._subs_json["subscriptions"].keys())
        return handle in handles

    def add_subscription(self, handle:str):
        # add a sub to this list
        # and call another function
        # to save the list to a file

        if not self.is_subbed(handle):
            try:
                new_sub = Sub(self._api_key, handle)
                self._subs_json["subscriptions"][handle] = new_sub.make_json()
                # update with the new 
                # sub just added
                self.store_list()
                print(f"Subscribed to {self._subs_json["subscriptions"][handle]['name']}")
            except SubException as e:
                if e.code == 3:
                    print(f"Failed to verify the handle, make sure {handle} is correct.")
                elif e.code == 7:
                    print(f"Could not subscribe to {handle} because failed to get their latest uploads. Not sure why (blame phillipdefraco)")
                elif e.code == 56:
                    print("Detected no internet connection, check your connection and try again")
                else:
                    raise e
            
        else:
            print(f"You are already subscribed to {self._subs_json["subscriptions"][handle]['name']}")

    
    def remove_subscription(self, handle):
        # remove a sub from this list 
        # and call the store list function
        # to update the file
        if self.is_subbed(handle):
            unsub = self._subs_json["subscriptions"].pop(handle)
            self.store_list()
            print(f"Unsubscribed from {unsub['name']}")
        else:
            print(f"You were never subscribed to {handle}")

    def list_subs(self):
        if self._no_subs:
            print("There are no subscriptions")
        else:
            # imagine splitting it up based
            # on recent upload
            # section on uploading today
            # section on uploading within the week
            # section on not uploaded in a long time
            today_uploads = []
            this_week_uploads = []
            long_ago_uploads = []
            
            # this will list in order of handle
            latest_possible_time = datetime.now()
            errored = False
            for sub_json_key, sub_json_value in self._subs_json["subscriptions"].items():  
                
                sub = None
                try:
                    sub = Sub(self._api_key, sub_json_key, sub_json_value)
                except SubException as e:
                    if e.code == 56:
                        # cannot connect to internet 
                        # so report message
                        # and break from for loop
                        print("Detected no internet connection, check your connection and try again")
                        errored = True
                        break
                    else:
                        # show exception because there is another error
                        # to address
                        raise e

                if sub.new_video():
                    # this means
                    # a new video was uploaded
                    # so update the json
                    self._subs_json["subscriptions"][sub._handle] = sub.make_json()
                    self.store_list()
                elif sub.have_watched() or sub.is_not_interested():
                    # if the user already
                    # watched the latest video from this sub
                    # and there is not a new video
                    # detected
                    # then do not list this channel
                    # which saves time and condenses what is displayed
                    # also do not show if the user is not interested
                    continue

                u_time = sub.get_latest_upload_time()

                u_time_diff = latest_possible_time - u_time
                if u_time_diff.days <= 0:
                    today_uploads.append(sub)
                elif u_time_diff.days <= 7:
                    this_week_uploads.append(sub)
                else:
                    long_ago_uploads.append(sub)
            
            # sort the uploads and print them
            if len(today_uploads) > 0: 
                today_uploads.sort(key= lambda sub: sub.get_latest_upload_time(), reverse=True)
                print("----------------------------")
                print("Uploads that happened today:")
                print("----------------------------\n")
                for up in today_uploads:
                    print(f" {up}\n")

            if len(this_week_uploads) > 0: 
                this_week_uploads.sort(key= lambda sub: sub.get_latest_upload_time(), reverse=True) 
                print("\n----------------------------")
                print("Uploads that happened this week:")
                print("----------------------------\n")
                for up in this_week_uploads:
                    print(f" {up}\n")
            
            if len(long_ago_uploads) > 0: 
                long_ago_uploads.sort(key= lambda sub: sub.get_latest_upload_time(), reverse=True)
                print("\n----------------------------")
                print("Uploads that happened a while ago:")
                print("----------------------------\n")
                for up in long_ago_uploads:
                    print(f" {up}\n")
            
            if not errored and len(long_ago_uploads) == 0 and len(today_uploads) == 0 and len(this_week_uploads) == 0:
                print("You have seen the all latest content from the channels you have subscribed to.")
    
    def set_sub_update_freq(self, handle, new_update_freq):

        if self.is_subbed(handle):
            # get the sub and change its update freq
            sub = Sub(self._api_key, handle, self._subs_json["subscriptions"][handle])
            sub.change_update_frequency(new_update_freq)

            # add the new json to the list and store it
            self._subs_json["subscriptions"][handle] = sub.make_json()
            self.store_list()
            print(f"Set the update frequency for {sub.get_name()} to {new_update_freq} days.")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")
    
    def set_sub_watched(self, handle):
        if self.is_subbed(handle):
            # get the sub and set the latest
            # has been watched
            sub = Sub(self._api_key, handle, self._subs_json["subscriptions"][handle])
            sub.just_watched()

            # save the update
            self._subs_json["subscriptions"][handle] = sub.make_json()
            self.store_list()
            print(f"Marked that you watched the latest from {sub.get_name()}")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")
    
    def set_sub_not_interested(self, handle):
        if self.is_subbed(handle):
            sub = Sub(self._api_key, handle, self._subs_json["subscriptions"][handle])
            sub.not_interested()

            self._subs_json["subscriptions"][handle] = sub.make_json()
            self.store_list()
            print(f"Marked that you are not interested in the latest from {sub.get_name()}")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")


    def set_watched_all(self):
        for sub_json in self._subs_json["subscriptions"]:
            # the double sub_json works because
            # the handle is the string containing the rest of the pertinent
            # channel info
            sub = Sub(self._api_key, sub_json, sub_json)
            sub.just_watched()
            self._subs_json["subscriptions"][sub._handle] = sub.make_json()

        self.store_list()
        print(f"You watched all the latest videos!!")

    
        
