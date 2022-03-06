#!/usr/bin/python3

from time import time
import traceback
import pathlib
import asyncio
from typing import Callable

from loguru import logger

from PushMethod import report_closure, callback_notify_closure
from .youtube_api_client import build_client, YoutubeClient


ROOT = pathlib.Path(__file__).parent.absolute()
TOKEN_PATH = ROOT.joinpath("token.json")
LOCAL_TESTING = False
INTERVAL = 10


class Notified:
    def __init__(self, cache_file: pathlib.Path):
        self.file = cache_file
        self.last_notified = self.file.read_text("utf8") if self.file.exists() else ""

        self.file.touch(exist_ok=True)

    def write(self, new_id):
        self.last_notified = new_id
        self.file.write_text(new_id, "utf8")

    def __contains__(self, item):
        return item in self.last_notified


async def start_checking(client: YoutubeClient, callback: Callable, interval, report: Callable, cache_file: pathlib.Path):
    notified = Notified(cache_file)

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
                    callback(**stream.as_dict())

        await asyncio.sleep(interval)


async def main(config, notify_callbacks: dict, cache_path: str, test_mode=False):
    # read config meow
    client_secret = config["client_secret"]
    push_contents = config['push contents']

    report_list = config.get('report', [])
    report = report_closure((notify_callbacks[x] for x in report_list if x in notify_callbacks), color='ff0000')

    client = build_client(client_secret=client_secret, token_dir=TOKEN_PATH, console=not LOCAL_TESTING)

    logger.info("Application successfully authorized.")

    push_callbacks = {name: notify_callbacks[name] for name in notify_callbacks.keys() & push_contents.keys()}
    callback_unified = callback_notify_closure(push_callbacks, push_contents, test_mode)
    names = (f'{callback.__class__.__name__}: {name}' for name, callback in push_callbacks.items())

    report(title="YouTube Notifier Started", fields={
        "Active Push Destination": "\n".join(names)
    })

    await start_checking(client, callback_unified, INTERVAL, report, pathlib.Path(cache_path))
