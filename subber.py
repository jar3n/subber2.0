#!/usr/bin/env python3
"""
    Command line Interface and 
    Main file for the Subber Python Application

"""

# python modules
import sys
import argparse
import configparser
from os.path import dirname, abspath
from pathlib import Path
from inspect import getsourcefile
import webbrowser


# custom modules
from sublist import SubscriptionList


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
    return SubscriptionList(cp['key']['api key'])


def subscribe(handles:list[str], subs:SubscriptionList):
    """Add channel handles to local subscriptions

    Args:
        handles (list[str]): the youtube channel handles to track
        subs (SubscriptionList): the subscription list object
    """
    for handle in handles:
        subs.add_subscription(handle)

def unsubscribe(handles:list[str], subs:SubscriptionList):
    """Remove channel handles from local subscriptions

    Args:
        handles (list[str]): youtube channel handles
        subs (SubscriptionList): subscription list object 
    """
    for handle in handles:
        subs.remove_subscription(handle)

def set_update_frequency(args:list[str], subs:SubscriptionList):
    """Set how often to look for a new video from the given creator

    Args:
        args (list[str]): the youtube channel handle and update frequency arguments
        subs (SubscriptionList): 
    """

    handle = None
    up_freq = None
    for a in args.set_update_freq:
        if a.isdigit():
            up_freq = int(a)
        else:
            handle = a

    if up_freq is None:
        raise argparse.ArgumentError(argument=args.set_update_freq,
            message="No number was provided to set the update frequency for the sub.")

    subs.set_sub_update_freq(handle, up_freq)

def mark_as_watched(handles:list[str], subs:SubscriptionList):
    """Record that the latest videos from the given handles 
       have been watched

    Args:
        handles (list[str]): handles of the youtube channels 
        subs (SubscriptionList): subscription list object
    """
    for handle in handles:
        subs.set_sub_watched(handle)

def mark_as_not_interested(handles:list[str], subs:SubscriptionList):
    """Record that the latest videos from the given handles
       are not interesting

    Args:
        handles (list[str]): handles of youtube channels
        subs (SubscriptionList): Subscription list object
    """
    for handle in handles:
        subs.set_sub_not_interested(handle)

class VideoPlayerException(Exception):
    """Exception for problems with playing the video
        in a browser

    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"VideoPlayerException: {self.msg}"

def play_latest(handle:str, subs:SubscriptionList):
    """Open a browser window to the latest video
       of the given youtube creator

    Args:
        handle (str): handle of the youtube channel
        subs (SubscriptionList): subscription object list
    """


    sub = subs.get_sub(handle)
    if sub is not None:
        sub_latest_vid_link = sub.get_latest_video_link()
        webbrowser.open(sub_latest_vid_link)
    else:
        raise VideoPlayerException(f"Not subscribed to the handle {handle}")


def parse_arguments(parser:argparse.ArgumentParser, subs:SubscriptionList):
    """Parse the arguments given from the command line

    Args:
        parser (argparse.ArgumentParser): the command line argument parser
    """

    args = parser.parse_args()

    if args.list:
        subs.list_subs()

    if isinstance(args.subscribe, list):
        subscribe(args.subscribe, subs)

    if isinstance(args.unsubscribe, list):
        unsubscribe(args.unsubscribe, list)

    if args.set_update_freq:
        try:
            set_update_frequency(args.set_update_freq, subs)
        except argparse.ArgumentError as e:
            print(e.message)

    if isinstance(args.watched, list):
        mark_as_watched(args.watched, subs)

    if args.watched_all:
        subs.set_watched_all()

    if isinstance(args.not_interested, list):
        mark_as_not_interested(args.not_interested, subs)

    if args.play:
        try:
            play_latest(args.play[0], subs)
        except VideoPlayerException as e:
            print(e.msg)


def main():
    """
        Main function that intakes 
        command line arguments and parses it
        then calls the appropriate functions from
        SubscriptionsList to produce the results
    """
    subs = None
    try:
        subs = check_api_key()
    except FileNotFoundError:
        print("ERROR: cannot find the api_key file with you " +
        "youtube API key in it. Make sure the file is in the" +
        " same directory as the subber.py file.")
        return
    except configparser.MissingSectionHeaderError:
        print("ERROR: api key file not properly formatted."+
            " Make sure there is a line with \'[key]\' followed "+
            "by a line with \'api_key=YOUR_API_KEY\'")        
        return

    parser = argparse.ArgumentParser(
        description="A tool for tracking youtube subscriptions locally!")

    parser.add_argument('-l',
                        '--list',
                        action='store_true',
                        help='List subscriptions')

    parser.add_argument('-s',
                        '--subscribe', 
                        type=str,
                        nargs='*',
                        help="add one or more subscriptions",
                        metavar='<channel handle>')

    parser.add_argument('-u',
                        '--unsubscribe', 
                        type=str,
                        nargs='*',
                        help="remove one or more subscriptions",
                        metavar='<channel handle>')

    parser.add_argument('-f',
                        '--set_update_freq', 
                        nargs=2,
                        help="set the number of days to wait before " +
                        "checking if a channel has uploaded.",
                        metavar=('<channel handle>', '<days to wait>'))

    parser.add_argument("-w",
                        '--watched', 
                        type=str,
                        nargs='*',
                        help="set a channel's latest video to not " +
                        " appear in list because you watched it unless they upload a new video",
                        metavar='<channel handle>')

    parser.add_argument("-a",
                        "--watched_all",
                        action='store_true',
                        help="set all channels to watched.")

    parser.add_argument("-n",
                        '--not_interested', 
                        type=str,
                        nargs='*',
                        help="set a channel's latest video to not interested in watching.",
                        metavar='<channel handle>')

    parser.add_argument("-p",
                        "--play",
                        type=str,
                        nargs=1,
                        help="play the latest video from the given channel",
                        metavar="<channel handle>")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    parse_arguments(parser, subs)

if __name__ == "__main__":
    main()
