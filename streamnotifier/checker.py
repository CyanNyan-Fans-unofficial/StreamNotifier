import asyncio
import json
import pathlib
import traceback

from loguru import logger

from .TwitchStreamNotifyBot import RequestInstance as TwitchChecker
from .YoutubeStreamNotifyBot import RequestInstance as YoutubeChecker

stream_types = {
    "twitch": TwitchChecker,
    "youtube": YoutubeChecker,
}


class StreamChecker:
    def __init__(self, config, push, cache_file: pathlib.Path):
        self.checker_type = config.pop("type")
        self.report = config.pop("report", [])
        self.push_contents = config.pop("push contents")
        self.interval_override = config.pop("interval", None)

        self.push = push
        self.cache_file = cache_file

        try:
            checker_cls = stream_types[self.checker_type]
        except KeyError:
            logger.error("Unknown checker type: {}", self.checker_type)

        self.instance = checker_cls(config)

    def get_cache(self):
        if not self.cache_file.exists():
            self.cache_file.write_text("{}")
            return

        try:
            with self.cache_file.open() as f:
                data = json.load(f)
        except Exception:
            self.cache_file.write_text("{}")
            return

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
        interval = self.interval_override
        if interval is None:
            return self.instance.check_interval
        return interval

    async def send_report(self, **kwargs):
        args = {"color": self.instance.color} | kwargs
        self.push.send_report(self.report, **args)

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
            title=f"Stream found for {self.checker_type}", fields=summary
        )

        try:
            self.push.send_push(self.push_contents, **info)
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
                    f"{name}: {self.push.methods[name].__class__.__name__}"
                    for name in self.push_contents
                ),
                "Active Report Destination": "\n".join(
                    f"{name}: {self.push.methods[name].__class__.__name__}"
                    for name in self.report
                ),
                "Type": self.checker_type,
                "Check Interval": self.instance.check_interval,
            },
        )

        while True:
            await self.sleep()
            try:
                await self.run_once()
            except Exception:
                traceback.print_exc()
