#!/usr/bin/env python3
"""
    Command line Interface and 
    Main file for the Subber Python Application

"""

# python modules
import sys
import argparse
import webbrowser

# custom modules
from api_key_utils import check_api_key, APIKeyRequestException
from sublist import SubscriptionList


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
    for a in args:
        if a.isdigit():
            up_freq = int(a)
        else:
            handle = a

    if up_freq is None:
        raise argparse.ArgumentError(argument='args.set_update_freq',
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
        webbrowser.open(sub.latest_video_url)
    else:
        raise VideoPlayerException(f"Not subscribed to the handle {handle}")

def get_information_on_subs(handles:list[str], subs:SubscriptionList):
    """List the detailed information about the given
       list of youtube channels given by the handles

    Args:
        handles (list[str]): a list of youtube
        channel handles to information about
        subs (SubscriptionList): subscription list manager object
    """
    for handle in handles:
        sub = subs.get_sub(handle)
        if sub is not None:
            print(sub.detailed_info)
        else:
            print(f"You are not subscribed to a channel with the handle: {handle}")
        print("") # adds new line


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
        unsubscribe(args.unsubscribe, subs)

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
    
    if isinstance(args.info, list):
        get_information_on_subs(args.info, subs)


def main():
    """
        Main function that intakes 
        command line arguments and parses it
        then calls the appropriate functions from
        SubscriptionsList to produce the results
    """
    subs = None
    try:
        subs = SubscriptionList(check_api_key())
    except APIKeyRequestException as e:
        print(e)
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
    
    parser.add_argument("-i",
                        "--info",
                        type=str,
                        nargs='*',
                        help="Get the information for the given channel or channels",
                        metavar="<channel handle(s)>")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    parse_arguments(parser, subs)

if __name__ == "__main__":
    main()
