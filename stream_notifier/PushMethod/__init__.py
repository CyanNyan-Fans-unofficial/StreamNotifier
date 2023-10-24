from typing import Optional

from loguru import logger

from stream_notifier.model import BaseModel, from_mapping

from .discord_push import DiscordPush
from .task import PushTask
from .telegram_push import TelegramPush
from .twitter_push import TwitterPush

_push_methods = {
    "discord": DiscordPush,
    "telegram": TelegramPush,
    "twitter": TwitterPush,
}


class PushMethodGeneralConfig(BaseModel):
    type: from_mapping(_push_methods)
    comment: Optional[str] = None


class Push:
    def __init__(self, push_methods: dict[str, dict], test_mode=False):
        self.methods = {}
        self.comments = {}
        self.test_mode = test_mode

        for name, config in push_methods.items():
            # Look up the push module by "type" field
            push_config = PushMethodGeneralConfig.model_validate(config)
            instance = push_config.type(config)
            self.methods[name] = instance
            self.comments[name] = push_config.comment or push_config.type.__name__

    async def verify_push(self):
        for name, instance in self.methods.items():
            try:
                await instance.verify()
            except Exception:
                logger.exception(
                    "Got Error during verifying {} ({})",
                    name,
                    type(instance).__name__,
                )

    async def send_push(self, push_contents: dict[str, str], **kwargs):
        logger.info("Notifier callback started")
        if self.test_mode:
            logger.warning("Test mode enabled, will not push to platforms")

        for task in self.iter_push_tasks(push_contents, **kwargs):
            logger.info(
                "Pushing for {} ({})",
                task.name,
                task.comment,
            )

            try:
                await task.send()
            except Exception:
                logger.exception("Push failed for {}!", task.name)

    def iter_push_tasks(self, push_contents: dict[str, str], **kwargs):
        for name, content in push_contents.items():
            text = content.format(**kwargs)
            try:
                module = self.methods[name]
                comment = self.comments[name]
            except KeyError:
                logger.warning("Push method {} is not configured! Skipping.", name)
                continue

            yield PushTask(name, comment, module, text, self.test_mode)

    async def send_report(self, report_methods, **kwargs):
        for name in report_methods:
            try:
                module = self.methods[name]
            except KeyError:
                logger.warning("Push method {} is not configured! Skipping.", name)
                continue

            logger.info("Sending report for {}", type(module).__name__)
            params = kwargs

            try:
                await module.report(**params)
            except Exception:
                logger.exception("Report failed for {}!", name)

    async def close(self):
        for method in self.methods.values():
            await method.close()
