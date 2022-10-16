import traceback

from loguru import logger

from streamnotifier.PushMethod.task import PushTask

from .discord_push import DiscordPush
from .telegram_push import TelegramPush
from .twitter_push import TwitterPush


modules = {"discord": DiscordPush, "telegram": TelegramPush, "twitter": TwitterPush}


class Push:
    def __init__(self, push_methods: dict[str, dict], test_mode=False):
        self.methods = {}
        self.test_mode = test_mode

        for name, config in push_methods.items():
            # Look up the push module by "type" field
            push_type = config["type"]
            module = modules[push_type]
            instance = module(config)

            try:
                instance.verify()
            except Exception as err:
                logger.warning(
                    "Got Error during verifying {} ({})", name, module.__name__
                )
                traceback.print_exception(err, err, err.__traceback__, limit=2)
            else:
                self.methods[name] = instance

    def send_push(self, push_contents: dict[str, str], **kwargs):
        logger.info("Notifier callback started")
        if self.test_mode:
            logger.warning("Test mode enabled, will not push to platforms")

        for task in self.iter_push_tasks(push_contents, **kwargs):
            logger.info("Pushing for {} ({})", task.name, type(task.instance).__name__)

            try:
                task.send()
            except Exception:
                traceback.print_exc()

    def iter_push_tasks(self, push_contents: dict[str, str], **kwargs):
        for name, content in push_contents.items():
            text = content.format(**kwargs)
            try:
                module = self.methods[name]
            except KeyError:
                logger.warning("Push method {} is not configured! Skipping.", name)
                continue

            yield PushTask(name, module, text)

    def send_report(self, report_methods, **kwargs):
        for name in report_methods:
            try:
                module = self.methods[name]
            except KeyError:
                logger.warning("Push method {} is not configured! Skipping.", name)
                continue

            logger.info("Sending report for {}", type(module).__name__)
            params = kwargs

            try:
                module.report(**params)
            except Exception:
                traceback.print_exc()
