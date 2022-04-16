#!/usr/bin/python3

import traceback
import pathlib
import asyncio
import json
from typing import Callable

from loguru import logger

from PushMethod import report_closure, callback_notify_closure
from .twitch_api_client import TwitchClient

USE_GET_STREAM = True
INTERVAL = 2


class Notified:
    def __init__(self, cache_file: pathlib.Path):
        self.file = cache_file

        try:
            self.last_notified = json.loads(self.file.read_text("utf8"))
        except Exception:
            logger.warning('Failed to load last notified data!')
            traceback.print_exc(limit=4)
            self.last_notified = {}

        self.file.touch(exist_ok=True)

    def write(self, new_info):
        self.last_notified = new_info
        self.file.write_text(json.dumps(new_info), "utf8")

    def __contains__(self, info):
        return info.started_at == self.last_notified.get('started_at')

    def verify_push(self, info):
        if info.title == self.last_notified.get('title'):
            raise ValueError('Twitch stream title did not change!')


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
        err_count = 0
        err_report_threshold = 5

        # logger.info("Started listening using GET_STREAM.")

        logger.info("Started polling for streams, interval: {}", INTERVAL)

        while True:
            await asyncio.sleep(INTERVAL)

            try:
                output = self.client.get_stream(user.id, log=False)

            except Exception as err:
                msg = str(err)

                err_count += 1
                if last_err == msg:
                    logger.critical("Previous Exception still in effect")
                else:
                    last_err = msg
                    traceback.print_exc(limit=4)

                if err_count == err_report_threshold:
                    self.report(title="Twitch Notifier Down", desc=traceback.format_exc(limit=4))

            else:
                if err_count >= err_report_threshold:
                    last_err = ""
                    self.report(title="Twitch Notifier Up", desc="Last exception cleared")

                err_count = 0

                if output and output.type == "live" and output not in self.notified:
                    logger.info("Found an active live stream for channel {}", self.channel_name)
                    self.report(title="Twitch Stream Found", fields={
                        "Started": output.started_at,
                        "Title": output.title,
                        "Type": output.type,
                        "Content": output.game_name,
                        "Delay": output.delay,
                        "Live": output.is_live
                    })

                    try:
                        self.notified.verify_push(output)
                    except ValueError as e:
                        self.report(title='Push notification cancelled!🚫', desc=f'Reason: {str(e)}')
                    else:
                        self.callback(**output.as_dict(), link=f"https://twitch.tv/{self.channel_name}")
                    finally:
                        self.notified.write(output.as_dict())

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
