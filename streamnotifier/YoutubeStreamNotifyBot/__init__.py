#!/usr/bin/python3

import json
import traceback
import pathlib
import asyncio
from typing import Callable

from loguru import logger

from streamnotifier.PushMethod import report_closure, callback_notify_closure
from .youtube_api_client import build_client, YoutubeClient


ROOT = pathlib.Path(__file__).parent.absolute()
INTERVAL = 10


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

        self.file.write_text(json.dumps(new_info,
            default=lambda o: f"<<{type(o).__qualname__}>>"), "utf8")

    def __contains__(self, info):
        return info.id == self.last_notified.get('id')

    def verify_push(self, info):
        if info.title == self.last_notified.get('title'):
            raise ValueError('YouTube stream title did not change!')

        if info.privacy_status == 'private':
            raise ValueError('Stream is private!')

    def extra_attributes(self, info):
        extra_attr = {}

        if info.description:
            description = info.description.strip().split('\n')
            extra_attr['description_first_line'] = description[0]

        return extra_attr

async def start_checking(client: YoutubeClient, callback: Callable, interval, report: Callable, cache_file: pathlib.Path):
    notified = Notified(cache_file)

    logger.info("Started polling for streams, interval: {}", interval)

    last_err = ""
    err_count = 0
    err_report_threshold = 5

    while True:
        await asyncio.sleep(interval)

        try:
            active = client.get_active_user_broadcasts(max_results=1)

        except Exception as err:
            msg = str(err)

            err_count += 1
            if last_err == msg:
                logger.critical("Previous Exception still in effect")
            else:
                last_err = msg
                traceback.print_exc(limit=4)

            if err_count == err_report_threshold:
                report(title="Youtube Notifier Down", desc=traceback.format_exc(limit=4))

        else:
            if err_count >= err_report_threshold:
                last_err = ""
                report(title="Youtube Notifier Up", desc="Last exception cleared")

            err_count = 0

            if active and active[0] not in notified:
                # gotcha! there's active stream
                stream = active[0]

                logger.debug("Found Active stream: {}", stream)

                report(title="YouTube Stream Found", desc="Private Streams will not be pushed.", fields={
                    "Started": stream.actual_start_time,
                    "Title": stream.title,
                    "Privacy": stream.privacy_status,
                    "link": stream.link,
                    "Live": stream.life_cycle_status
                })

                # write in cache and notify if not private
                try:
                    notified.verify_push(stream)
                except ValueError as e:
                    report(title='Push notification cancelled!🚫', desc=f'Reason: {str(e)}')
                else:
                    callback(**stream.as_dict(), **notified.extra_attributes(stream))
                finally:
                    notified.write(stream.as_dict())


async def main(config, notify_callbacks: dict, cache_path: str, test_mode=False):
    # read config meow
    client_secret = config["client_secret"]
    push_contents = config['push contents']
    token = config.get('token')

    report_list = config.get('report', [])
    report = report_closure((notify_callbacks[x] for x in report_list if x in notify_callbacks), color='ff0000')

    client = build_client(client_secret=client_secret, token=token)

    logger.info("Application successfully authorized.")

    push_callbacks = {name: notify_callbacks[name] for name in notify_callbacks.keys() & push_contents.keys()}
    callback_unified = callback_notify_closure(push_callbacks, push_contents, test_mode)
    names = (f'{callback.__class__.__name__}: {name}' for name, callback in push_callbacks.items())

    report(title="YouTube Notifier Started", fields={
        "Active Push Destination": "\n".join(names)
    })

    await start_checking(client, callback_unified, INTERVAL, report, pathlib.Path(cache_path))
