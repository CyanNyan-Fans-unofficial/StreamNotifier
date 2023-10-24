import asyncio
import json
import pathlib
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
from .twitch import TwitchChecker
from .twitter import TwitterChecker
from .youtube import YoutubeChecker

_stream_checkers = {
    "twitch": TwitchChecker,
    "youtube": YoutubeChecker,
    "twitter": TwitterChecker,
    "debug": DebugChecker,
}


class StreamCheckerGeneralConfig(BaseModel):
    type: from_mapping(_stream_checkers)
    report: list[str]
    push_contents: dict[str, str]
    interval: Optional[float] = None
    report_url: Optional[HttpUrl] = None
    report_interval: int = 20


class StreamChecker:
    def __init__(self, config, push: Push, cache_file: pathlib.Path):
        self.config = StreamCheckerGeneralConfig.model_validate(config)
        self.instance: CheckerBase = self.config.type(config)
        self.push = push
        self.cache = None
        self.cache_file = cache_file
        self.last_reported_http = 0

    def get_cache(self):
        if self.cache is None:
            try:
                with self.cache_file.open() as f:
                    self.cache = json.load(f)
            except Exception:
                self.cache = {}

        return self.cache

    def set_cache(self, info):
        # Remove internal attributes that starts with _
        dump = {key: value for key, value in info.items() if not key.startswith("_")}
        content = json.dumps(
            dump, default=lambda o: f"<<{type(o).__qualname__}>>", indent=2
        )
        if self.cache_file:
            self.cache_file.write_text(content)
        self.cache = json.loads(content)
        return content

    async def sleep(self):
        await asyncio.sleep(self.interval)

    @property
    def interval(self):
        return self.config.interval or self.instance.config.check_interval

    async def send_report(self, **kwargs):
        args = {"color": self.instance.config.color} | kwargs
        await self.push.send_report(self.config.report, **args)

    async def send_report_http(self, text=None):
        if not self.config.report_url:
            return

        if time() - self.last_reported_http > self.config.report_interval:
            self.last_reported_http = time()
            timeout = ClientTimeout(total=10)
            async with ClientSession(timeout=timeout) as session:
                async with session.post(str(self.config.report_url), data=text):
                    pass

    async def run_once(self):
        last_notified = Dict(self.get_cache())
        info = Dict(await self.instance.run_check(last_notified))

        if not info:
            return

        await self.instance.process_result(info)
        cached_content = self.set_cache(info)
        summary = self.instance.summary(info)

        try:
            if not self.instance.verify_push(last_notified, info):
                return cached_content

        except ValueError as e:
            await self.send_report(
                title="Push notification cancelled!🚫",
                desc=f"Reason: {str(e)}",
                fields=summary,
            )
            return cached_content

        await self.send_report(
            title=f"Stream found for {self.config.type}", fields=summary
        )

        try:
            await self.push.send_push(self.config.push_contents, **info)
        except Exception as e:
            await self.send_report(
                title="Notification Push failed!❌", desc=f"{type(e).__name__}: {str(e)}"
            )
            logger.exception("Push notification failed!")

        return cached_content

    async def run(self):
        await self.send_report(
            title="Stream Notifier Started",
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
                logger.exception("Error while checking for stream")
