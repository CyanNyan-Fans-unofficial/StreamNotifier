import asyncio
import json
import pathlib
from importlib import import_module
from time import time
from typing import Literal

from addict import Dict
from aiohttp import ClientSession, ClientTimeout
from loguru import logger
from pydantic import validate_call

from stream_notifier.PushMethod import Push
from stream_notifier.model import PushContext


@validate_call
def import_checker(checker_type: Literal["debug", "twitch", "twitter", "youtube"]):
    base = "".join(word.capitalize() for word in checker_type.split("_"))
    module = import_module(f".{checker_type}", __name__)
    return (
        getattr(module, f"{base}Checker"),
        getattr(module, f"{base}CheckerConfig"),
        getattr(module, f"{base}CheckerPushRule", None),
    )


class StreamChecker:
    def __init__(self, config, push: Push, cache_file: pathlib.Path):
        self.type = config.pop("type")
        checker_cls, checker_config_cls, push_rule_cls = import_checker(self.type)

        self.config = checker_config_cls.model_validate(config)
        self.instance = checker_cls(self.config)

        self.push_contents = []
        self.push_rules = []
        if self.config.push_rules:
            for rule in self.config.push_rules:
                self.push_contents.append(rule.contents)
                self.push_rules.append(push_rule_cls.model_validate(rule.rule))
        else:
            self.push_contents.append(self.config.push_contents)
            self.push_rules.append(self.instance)

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

    @property
    def active_push_destinations(self):
        for contents in self.push_contents:
            for name in contents:
                yield name

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

        for rule, contents in zip(self.push_rules, self.push_contents):
            try:
                if not self.instance.verify_push(rule, last_notified, info):
                    continue

            except Exception as e:
                await self.send_report(
                    title="Push notification cancelled!🚫",
                    desc=f"Reason: {str(e)}",
                    fields=summary,
                )
                continue

            await self.send_report(
                title=f"Stream found for {type(self.instance).__qualname__}",
                fields=summary,
            )

            try:
                context = PushContext(type=self.type, data=info)
                await self.push.send_push(contents, context, **info)
            except Exception as e:
                await self.send_report(
                    title="Notification Push failed!❌",
                    desc=f"{type(e).__name__}: {str(e)}",
                )
                logger.exception("Push notification failed!")

        return cached_content

    async def run(self):
        await self.send_report(
            title="Stream Notifier Started",
            fields={
                "Active Push Destination": "\n".join(
                    f"{name}: {self.push.comments[name]}"
                    for name in self.active_push_destinations
                ),
                "Active Report Destination": "\n".join(
                    f"{name}: {self.push.comments[name]}" for name in self.config.report
                ),
                "Type": type(self.instance).__qualname__,
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
