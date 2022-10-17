import asyncio
import json
import pathlib
import traceback
from time import time
from typing import Optional

from addict import Dict
from aiohttp import ClientSession, ClientTimeout
from loguru import logger
from pydantic import HttpUrl
from stream_notifier.model import BaseModel, from_mapping
from stream_notifier.PushMethod import Push

from .base import CheckerBase
from .debug import DebugChecker
from .twitch import RequestInstance as TwitchChecker
from .twitter import TwitterChecker
from .youtube import RequestInstance as YoutubeChecker


class StreamCheckerConfig(BaseModel):
    type: from_mapping(
        {
            "twitch": TwitchChecker,
            "youtube": YoutubeChecker,
            "twitter": TwitterChecker,
            "debug": DebugChecker,
        }
    )
    report: list[str]
    push_contents: dict[str, str]
    interval: Optional[float]
    report_url: Optional[HttpUrl]
    report_interval: int = 45


class StreamChecker:
    def __init__(self, config, push: Push, cache_file: pathlib.Path):
        self.config = StreamCheckerConfig.parse_obj(config)
        self.instance: CheckerBase = self.config.type(config)
        self.push = push
        self.cache_file = cache_file
        self.last_reported_http = 0

    def get_cache(self):
        try:
            with self.cache_file.open() as f:
                data = json.load(f)
        except Exception:
            return {}

        return data

    def set_cache(self, info):
        # Remove internal attributes that starts with _
        dump = {key: value for key, value in info.items() if not key.startswith("_")}
        content = json.dumps(
            dump, default=lambda o: f"<<{type(o).__qualname__}>>", indent=2
        )
        self.cache_file.write_text(content)
        return content

    async def sleep(self):
        await asyncio.sleep(self.interval)

    @property
    def interval(self):
        return self.config.interval or self.instance.config.check_interval

    async def send_report(self, **kwargs):
        args = {"color": self.instance.config.color} | kwargs
        self.push.send_report(self.config.report, **args)

    async def send_report_http(self, text=None):
        if not self.config.report_url:
            return

        if time() - self.last_reported_http > self.config.report_interval:
            self.last_reported_http = time()
            timeout = ClientTimeout(total=10)
            async with ClientSession(timeout=timeout) as session:
                async with session.post(self.config.report_url, data=text) as response:
                    pass

    async def run_once(self):
        info = Dict(await self.instance.run_check())

        if not info:
            return

        last_notified = Dict(self.get_cache())
        await self.instance.process_result(info)
        cached_content = self.set_cache(info)
        summary = self.instance.summary(info)

        try:
            if not self.instance.verify_push(last_notified, info):
                return cached_content

        except ValueError as e:
            await self.send_report(
                title=f"Push notification cancelled!🚫",
                desc=f"Reason: {str(e)}",
                fields=summary,
            )
            return cached_content

        await self.send_report(
            title=f"Stream found for {self.config.type}", fields=summary
        )

        try:
            self.push.send_push(self.config.push_contents, **info)
        except Exception as e:
            await self.send_report(
                title="Notification Push failed!❌", desc=f"{type(e).__name__}: {str(e)}"
            )
            logger.exception(e)

        return cached_content

    async def run(self):
        await self.send_report(
            title=f"Stream Notifier Started",
            fields={
                "Active Push Destination": "\n".join(
                    f"{name}: {self.push.comments[name]}"
                    for name in self.config.push_contents
                ),
                "Active Report Destination": "\n".join(
                    f"{name}: {self.push.comments[name]}" for name in self.config.report
                ),
                "Type": self.config.type.__qualname__,
                "Check Interval": self.interval,
            },
        )

        report_tasks = set()

        while True:
            await self.sleep()
            try:
                info = await self.run_once()
                task = asyncio.create_task(self.send_report_http(info))
                report_tasks.add(task)
                task.add_done_callback(report_tasks.discard)
            except Exception:
                traceback.print_exc()
