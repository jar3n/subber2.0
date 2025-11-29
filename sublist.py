
# python modules
import os, sys, json
from datetime import datetime
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

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
        
        if self._no_subs:
            self._sub_count = 0
        else:
            self._sub_count = len(list(self._subs_json["subscriptions"]))

        # set up the multiprocessing
        # this determines how to create subprocesses 
        mp.set_start_method('fork')

        # 'enum' values for this class
        # to use with the sub checking
        self.FAILED = -1
        self.UPDATED = 1
        self.NORMAL = 0
        self.IGNORE = -2

        
    
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
                self.update_sub_json(new_sub)
                print(f"Subscribed to {new_sub.get_name()}")
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

    def check_sub(self, sub_json_key, sub_json_value, queue):
        # checks the sub status 
        # and sees if a new video has been uploaded
        # usefull for parallelizing the 
        # list subs function
        # determines whether or not the sub
        # to add to queue
        
        # debug print string
        # print(f"Checking sub: {sub_json_key}")
    

        sub = None
        errored = False
        try:
            sub = Sub(self._api_key, sub_json_key, sub_json_value)

        except:
            # raise flag to add the sub to the error queue
            errored = True
        
        # print(f"Checking sub statuses for {sub.get_name()}:")
        # print(f"has watched: {sub.have_watched()}")
        # print(f"not interested: {sub.is_not_interested()}")
        
        if errored:
            # add the sub to the error queue
            # or really just the sub channel name
            # safest bet is to use the json key
            # in future refactor the sub class
            # to not throw exceptions in the constructor
            queue.put([sub_json_key, self.FAILED])
        elif sub.new_video():
            # put the sub in the new video queue if
            # a new video was uploaded since last check
            queue.put([sub, self.UPDATED])
        elif sub.have_watched() or sub.is_not_interested():
            # here because the number of processes
            # equals number of subs 
            # so ignore all subs in this category
            # print(f"Marking {sub.get_name()} as ignored")
            queue.put([sub, self.IGNORE])
        else:
            # print(f"Marking sub as normal {sub.get_name()}")
            queue.put([sub, self.NORMAL])
            
    def update_sub_json(self, sub):
        # function for updating the json for a sub 
        # when it changes
        self._subs_json["subscriptions"][sub._handle] = sub.make_json()
        self.store_list()

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
            
            # use this for later
            latest_possible_time = datetime.now()

            # do some multiprocessing to 
            # process the subs  asynchronously
            with mp.Manager() as mpm:
                sub_queue = mpm.Queue()
                handles = list(self._subs_json["subscriptions"].keys())
                channel_data = list(self._subs_json["subscriptions"].values())
                failed_sub_checks = []

                with ProcessPoolExecutor(max_workers=mp.cpu_count()) as pool_exe:
                    sub_procs = [pool_exe.submit(self.check_sub, handles[i], channel_data[i], sub_queue) for i in range(self._sub_count)]
                
                    completed = 0
                    while completed < self._sub_count:
                        try:
                            # got an item from the queue
                            proc_result = sub_queue.get(timeout=0.5)

                            # debug print to keep just in case
                            # print(f"got result for {proc_result[0]._handle}, Completed = {completed+1}/{self._sub_count}")
                            completed += 1
                            if proc_result[1] == self.UPDATED or proc_result[1] == self.NORMAL:
                                # this means the sub can be added to the display lists
                                # first if updated then update the json
                                sub = proc_result[0]
                                if proc_result[1] == self.UPDATED:
                                    self.update_sub_json(sub)
                                
                                # now determine the list to add the 
                                # sub to
                                u_time = sub.get_latest_upload_time()

                                u_time_diff = latest_possible_time - u_time
                                if u_time_diff.days <= 0:
                                    today_uploads.append(sub)
                                elif u_time_diff.days <= 7:
                                    this_week_uploads.append(sub)
                                else:
                                    long_ago_uploads.append(sub)
                            elif proc_result[1] == self.FAILED:
                                # this means it failed
                                # so add it to the list
                                failed_sub_checks.append(sub)

                        except Exception:
                            # no item was retreived so continue checking
                            pass

                        
            # print("Completed sub checks")

            # sort the uploads and print them
            if len(today_uploads) > 0: 
                today_uploads.sort(key= lambda sub: sub.get_latest_upload_time(), reverse=True)
                print("----------------------------")
                print(f"Uploads that happened today ({len(today_uploads)}):")
                print("----------------------------\n")
                for up in today_uploads:
                    print(f" {up}\n")

            if len(this_week_uploads) > 0: 
                this_week_uploads.sort(key= lambda sub: sub.get_latest_upload_time(), reverse=True) 
                print("\n----------------------------")
                print(f"Uploads that happened this week ({len(this_week_uploads)}):")
                print("----------------------------\n")
                for up in this_week_uploads:
                    print(f" {up}\n")
            
            if len(long_ago_uploads) > 0: 
                long_ago_uploads.sort(key= lambda sub: sub.get_latest_upload_time(), reverse=True)
                print("\n----------------------------")
                print(f"Uploads that happened a while ago ({len(long_ago_uploads)}):")
                print("----------------------------\n")
                for up in long_ago_uploads:
                    print(f" {up}\n")

            if len(long_ago_uploads) == 0 and len(today_uploads) == 0 and len(this_week_uploads) == 0:
                print("You have seen the all latest content from the channels you have subscribed to that could be checked.")
            
            if len(failed_sub_checks) == 0:
                print("All of your subscriptions were successfully checked.")
            else:
                print("The following channels were not successfully checked.")
                for channel in failed_sub_checks:
                    print(f" - {channel}")
            
    
    def set_sub_update_freq(self, handle, new_update_freq):

        if self.is_subbed(handle):
            # get the sub and change its update freq
            sub = Sub(self._api_key, handle, self._subs_json["subscriptions"][handle])
            sub.change_update_frequency(new_update_freq)

            # add the new json to the list and store it
            self.update_sub_json(sub)
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
            self.update_sub_json(sub)
            print(f"Marked that you watched the latest from {sub.get_name()}")
        else:
            print(f"You are not subbed to a channel with the handle {handle}")
    
    def set_sub_not_interested(self, handle):
        if self.is_subbed(handle):
            sub = Sub(self._api_key, handle, self._subs_json["subscriptions"][handle])
            sub.not_interested()

            self.update_sub_json(sub)
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

    def get_sub(self, handle):
        return Sub(self._api_key, handle, self._subs_json["subscriptions"][handle])