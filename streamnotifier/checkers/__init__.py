import asyncio
import json
import pathlib
import traceback
from typing import Optional

from loguru import logger
from streamnotifier.model import BaseModel, from_mapping

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


class StreamChecker:
    def __init__(self, config, push, cache_file: pathlib.Path):
        self.config = StreamCheckerConfig.parse_obj(config)
        self.instance = self.config.type(config)
        self.push = push
        self.cache_file = cache_file

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
        with self.cache_file.open("w") as f:
            json.dump(dump, f, default=lambda o: f"<<{type(o).__qualname__}>>")

    async def sleep(self):
        await asyncio.sleep(self.interval)

    @property
    def interval(self):
        return self.config.interval or self.instance.config.check_interval

    async def send_report(self, **kwargs):
        args = {"color": self.instance.config.color} | kwargs
        self.push.send_report(self.config.report, **args)

    async def run_once(self):
        info = await self.instance.run_check()
        last_notified = self.get_cache() or {}
        if not info:
            return

        self.set_cache(info)
        summary = self.instance.summary(info)

        try:
            if not self.instance.verify_push(last_notified, info):
                return
        except ValueError as e:
            await self.send_report(
                title=f"Push notification cancelled!🚫",
                desc=f"Reason: {str(e)}",
                fields=summary,
            )
            return

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

        while True:
            await self.sleep()
            try:
                await self.run_once()
            except Exception:
                traceback.print_exc()
