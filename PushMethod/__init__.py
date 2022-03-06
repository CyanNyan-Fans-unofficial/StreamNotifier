import traceback

from loguru import logger

from . import discord_push, telegram_push, twitter_push


modules = {
    'discord': discord_push.DiscordPush,
    'telegram': telegram_push.TelegramPush,
    'twitter': twitter_push.TwitterPush
}


def verify_methods(config: dict, push_contents: dict[str, str]):
    for name, push_method_config in config.items():
        content = push_contents.get(name)

        # If content is not set, disable such push method
        if not content:
            continue

        # Look up the push module by "type" field
        push_type = push_method_config['type']
        method = modules[push_type]

        try:
            instance = method(push_method_config, content)
        except Exception as err:
            logger.warning("Got Error during verifying {}", method.__name__)
            traceback.print_exception(err, err, err.__traceback__, limit=2)
        else:
            yield instance
