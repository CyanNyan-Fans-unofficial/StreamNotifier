#!/usr/bin/python3

import time
import traceback
import argparse
import pathlib
import json
from typing import Callable

from loguru import logger

from PushMethod import verify_methods, report_closure
from .youtube_api_client import build_client, YoutubeClient, LiveBroadcast
from .discord_report import report_closure


ROOT = pathlib.Path(__file__).parent.absolute()
TOKEN_PATH = ROOT.joinpath("token.json")
LOCAL_TESTING = False
INTERVAL = 10


class Notified:
    def __init__(self):
        self.file = args.cache
        self.last_notified = self.file.read_text("utf8") if self.file.exists() else ""

        self.file.touch(exist_ok=True)

    def write(self, new_id):
        self.last_notified = new_id
        self.file.write_text(new_id, "utf8")

    def __contains__(self, item):
        return item in self.last_notified


def callback_notify_closure(notify_callbacks):
    test = args.test

    if test:
        logger.warning("Test mode enabled, will not push to platforms")

    def inner(channel_object: LiveBroadcast):
        logger.info("Notifier callback started for stream {}", channel_object)
        for callback in notify_callbacks:

            if test:
                logger.info("Test mod, skipping {}", type(callback).__name__)
                continue
            else:
                logger.info("Pushing for {}", type(callback).__name__)

            try:
                callback.send(channel_object)
            except Exception:
                traceback.print_exc()

    return inner


def start_checking(client: YoutubeClient, callback: Callable, interval, report: Callable):
    notified = Notified()

    logger.info("Started polling for streams, interval: {}", interval)

    last_err = ""

    while True:
        try:
            active = client.get_active_user_broadcasts(max_results=1)

        except Exception as err:
            msg = str(err)

            if last_err == msg:
                logger.critical("Previous Exception still in effect")
            else:
                last_err = msg
                traceback.print_exc(limit=4)
                report(title="Youtube Notifier Down", desc=traceback.format_exc(limit=4))

        else:
            if last_err:
                last_err = ""
                report(title="Youtube Notifier Up", desc="Last exception cleared")

            if active and active[0].id not in notified:
                # gotcha! there's active stream
                stream = active[0]

                logger.debug("Found Active stream: {}", stream)

                report(title="Stream Found", desc="Private Streams will not be pushed.", fields={
                    "Started": stream.actual_start_time,
                    "Title": stream.title,
                    "Privacy": stream.privacy_status,
                    "link": stream.link,
                    "Live": stream.life_cycle_status
                })
                # write in cache and notify if not private
                notified.write(stream.id)

                if stream.privacy_status != "private":
                    callback(stream)

        time.sleep(interval)


def main(config):

    # read config meow
    client_secret = config["client_secret"]

    report = report_closure(config, discord_embed_color='ff0000')

    client = build_client(client_secret=client_secret, token_dir=TOKEN_PATH, console=not LOCAL_TESTING)

    logger.info("Application successfully authorized.")

    callback_list = list(verify_methods(config))
    names = tuple(x.__class__.__name__ for x in callback_list)

    logger.info("Verified {}", ", ".join(names))

    callback_unified = callback_notify_closure(callback_list)

    report(title="Notifier Started", fields={
        "Active Push Destination": "\n".join(names)
    })

    start_checking(client, callback_unified, INTERVAL, report)


if __name__ == "__main__":

    # parsing start =================================

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        "--path",
        metavar="CONFIG_PATH",
        type=pathlib.Path,
        default=ROOT.joinpath("configuration.json"),
        help="Path to configuration json file. Default path is 'configuration.json' adjacent to this script",
    )
    parser.add_argument(
        "-c",
        "--cache",
        metavar="CACHE_PATH",
        type=pathlib.Path,
        default=ROOT.joinpath("cache.json"),
        help="Path where cache file will be. Default path is 'cache' adjacent to this script",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        default=False,
        help="Enable test mode, this does not actually push to platforms.",
    )
    args = parser.parse_args()

    # parsing end ===================================

    config = json.loads(args.path.read_text(encoding="utf8"))
    main(config)
