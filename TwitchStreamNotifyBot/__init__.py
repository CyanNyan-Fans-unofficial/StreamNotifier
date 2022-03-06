#!/usr/bin/python3

import traceback
import pathlib
import asyncio
from typing import Callable

from loguru import logger

from PushMethod import report_closure, callback_notify_closure
from .twitch_api_client import TwitchClient

ROOT = pathlib.Path(__file__).parent.absolute()
USE_GET_STREAM = True
INTERVAL = 2


class Notified:
    def __init__(self, cache_file: pathlib.Path):
        self.file = cache_file
        self.last_notified = self.file.read_text("utf8") if self.file.exists() else ""

        self.file.touch(exist_ok=True)

    def write(self, new_time):
        self.last_notified = new_time
        self.file.write_text(new_time, "utf8")

    def __contains__(self, item):
        return item in self.last_notified


class RequestInstance:
    def __init__(self, client: TwitchClient, channel_name: str, callback: Callable, report: Callable, cache_file: pathlib.Path):
        self.notified = Notified(cache_file)
        self.client = client
        self.channel_name = channel_name
        self.callback = callback
        self.report = report

    async def start_checking(self):

        user = self.client.get_user(self.channel_name)

        # self.report(title="Notifier Started", desc="Debugging info", fields={
        #     "Target": user.login,
        #     "Created": user.created_at,
        #     "Type": user.type,
        #     "View Count": user.view_count,
        #     "email": user.email
        # })

        logger.info("Found user: {}", user)
        last_err = ""

        # logger.info("Started listening using GET_STREAM.")

        logger.info("Started polling for streams, interval: {}", INTERVAL)

        while True:

            try:
                output = self.client.get_stream(user.id, log=False)

            except Exception as err:
                msg = str(err)

                if last_err == msg:
                    logger.critical("Previous Exception still in effect")
                else:
                    last_err = msg
                    traceback.print_exc(limit=4)
                    self.report(title="Twitch Notifier Down", desc=traceback.format_exc(limit=4))

            else:
                if last_err:
                    last_err = ""
                    self.report(title="Twitch Notifier Up", desc="Last exception cleared")

                if output and output.type == "live" and output.started_at not in self.notified:
                    logger.info("Found an active live stream for channel {}", self.channel_name)
                    self.report(title="Stream Found", fields={
                        "Started": output.started_at,
                        "Title": output.title,
                        "Type": output.type,
                        "Content": output.game_name,
                        "Delay": output.delay,
                        "Live": output.is_live
                    })

                    self.notified.write(output.started_at)
                    self.callback(**output.as_dict(), link=f"https://twitch.tv/{self.channel_name}")

            await asyncio.sleep(INTERVAL)

        # else:
        #     while True:
        #         output = self.client.search_channel(user.login)
        #
        #         if output.is_live and output.started_at not in self.notified:
        #             logger.info("Found an active live stream for channel {}", self.channel_name)
        #
        #             self.notified.write(output.started_at)
        #             self.callback(f"https://twitch.tv/{self.channel_name}", output)
        #
        #         time.sleep(2)


async def main(config, notify_callbacks: dict, cache_path: str, test_mode=False):
    cache_path = cache_path

    channel_name = config["channel name"]
    client_id = config["polling api"]["twitch app id"]
    client_secret = config["polling api"]["twitch app secret"]
    push_contents = config['push contents']

    report_list = config.get('report', [])
    report = report_closure((notify_callbacks[x] for x in report_list if x in notify_callbacks), color='a364fe')

    client = TwitchClient(client_id, client_secret)

    logger.info("Target Channel: {}", channel_name)

    push_callbacks = {name: notify_callbacks[name] for name in notify_callbacks.keys() & push_contents.keys()}
    callback_unified = callback_notify_closure(push_callbacks, push_contents, test_mode)
    names = (f'{callback.__class__.__name__}: {name}' for name, callback in push_callbacks.items())

    req_instance = RequestInstance(client, channel_name, callback_unified, report, pathlib.Path(cache_path))

    report(title="Twitch Notifier Started", fields={
        "Target": channel_name,
        "Active Push Destination": "\n".join(names)
    })

    await req_instance.start_checking()
