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

def main():
    """
        Main function that intakes 
        command line arguments and parses it
        then calls the appropriate functions from
        SubscriptionsList to produce the results
    """

    # first checking for api key file
    api_key_file = Path(f"{dirname(abspath(getsourcefile(lambda:0)))}/api_key")
    if not api_key_file.is_file():
        print("ERROR: cannot find the api_key file with you youtube API key in it." +
              " Make sure the file is in the same directory as the subber.py file.")
        return

    cp = configparser.ConfigParser()
    try:
        cp.read(str(api_key_file))
    except configparser.MissingSectionHeaderError:
        print("ERROR: api key file not properly formatted." +
                " Make sure there is a line with \'[key]\' followed by a " + 
                " line with \'api_key=YOUR_API_KEY\'")
        return
    api_key = cp['key']['api key']

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

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    subs = SubscriptionList(api_key)

    if args.list:
        subs.list_subs()

    if isinstance(args.subscribe, list):
        for handle in args.subscribe:
            subs.add_subscription(handle)

    if isinstance(args.unsubscribe, list):
        for handle in args.unsubscribe:
            subs.remove_subscription(handle)

    if args.set_update_freq:

        up_freq = -1
        handle = ""

        # determine the order which the arguments were given
        if args.set_update_freq[0].isdigit():
            up_freq = int(args.set_update_freq[0])
            handle = args.set_update_freq[1]
            subs.set_sub_update_freq(handle, up_freq)

        elif args.set_update_freq[1].isdigit():
            up_freq = int(args.set_update_freq[1])
            handle = args.set_update_freq[0]
            subs.set_sub_update_freq(handle, up_freq)

        else:
            print("No number was provided to set the update frequency for the sub.")


    if isinstance(args.watched, list):
        for handle in args.watched:
            subs.set_sub_watched(handle)

    if args.watched_all:
        subs.set_watched_all()

    if isinstance(args.not_interested, list):
        for handle in args.not_interested:
            subs.set_sub_not_interested(handle)

    if args.play:
        # Desire is to have a way to provide youtube
        # videos without going to youtube website
        # but youtube does not want that
        # instead this command simply
        # opens the youtube video url
        # which is still a nice convenience
        sub = subs.get_sub(args.play[0])
        if sub is not None:
            sub_latest = sub.latest_video_link()
            webbrowser.open(sub_latest)

if __name__ == "__main__":
    main()
