import traceback

from loguru import logger

from . import discord_push, telegram_push, twitter_push
from .discord_report import report_closure


modules = discord_push.DiscordPush, telegram_push.TelegramPush, twitter_push.TwitterPush


def verify_methods(config: dict):
    push_config = config["push methods"]

    for method in modules:
        try:
            instance = method(push_config)
        except Exception as err:
            logger.warning("Got Error during verifying {}", method.__name__)
            traceback.print_exception(err, err, err.__traceback__, limit=2)
        else:
            yield instance
