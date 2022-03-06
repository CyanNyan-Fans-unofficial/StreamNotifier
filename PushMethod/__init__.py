import traceback
from typing import Callable

from loguru import logger

from . import discord_push, telegram_push, twitter_push


modules = {
    'discord': discord_push.DiscordPush,
    'telegram': telegram_push.TelegramPush,
    'twitter': twitter_push.TwitterPush
}


def verify_method(name, config: dict):
    # Look up the push module by "type" field
    push_type = config['type']
    method = modules[push_type]

    try:
        instance = method(config)
    except Exception as err:
        logger.warning("Got Error during verifying {} ({})", name, method.__name__)
        traceback.print_exception(err, err, err.__traceback__, limit=2)
    else:
        return instance

def callback_notify_closure(notify_callbacks: dict[str, Callable], contents: dict[str, str], test_mode=False):
    callbacks = dict(notify_callbacks)

    if test_mode:
        logger.warning("Test mode enabled, will not push to platforms")

    def inner(**kwargs):
        logger.info("Notifier callback started.")
        for name, callback in callbacks.items():
            content = contents[name]
            text = content.format(**kwargs)

            if test_mode:
                logger.info("Test mode, skipping {}", type(callback).__name__)
                continue
            else:
                logger.info("Pushing for {}", type(callback).__name__)

            try:
                callback.send(text)
            except Exception:
                traceback.print_exc()

    return inner

def report_closure(notify_callbacks, **default_kwargs):
    callbacks = list(notify_callbacks)
    def inner(**kwargs):
        kwargs = default_kwargs | kwargs
        for callback in callbacks:
            logger.info("Sending report for {}", type(callback).__name__)
            try:
                callback.report(**kwargs)
            except Exception:
                traceback.print_exc()

    return inner
