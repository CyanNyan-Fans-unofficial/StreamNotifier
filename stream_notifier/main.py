import argparse
import asyncio
from loguru import logger
from os.path import join
from yaml import safe_load
from TwitchStreamNotifyBot import main as twitch_main
from YoutubeStreamNotifyBot import main as youtube_main
from PushMethod import verify_method


stream_types = {
    'twitch': twitch_main,
    'youtube': youtube_main
}


async def stream_notifier_cli():
    # Parsing arguments from command
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        "--path",
        metavar="CONFIG_PATH",
        default="config.yml",
        help="Path to configuration json file. Default path is 'config.yml' on the working directory",
    )

    parser.add_argument(
        "-c",
        "--cache-dir",
        metavar="CACHE_DIR",
        default="cache",
        help="Directory where cache files will be. Default path is 'cache' on the working directory",
    )

    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        default=False,
        help="Enable test mode, this does not actually push to platforms.",
    )
    args = parser.parse_args()

    # Load the config meow meow
    with open(args.path, encoding="utf8") as f:
        config = safe_load(f)

    # Verify push methods
    push_methods = config.pop('push methods')
    callback_list = {}
    for name, push_method_config in push_methods.items():
        method = verify_method(name, push_method_config)
        if method:
            callback_list[name] = method

    names = (f'{name}: {x.__class__.__name__}' for name, x in callback_list.items())
    logger.info("Verified {}", ", ".join(names))

    # Initialize stream checkers
    coro_list = []
    for name, service_config in config.items():
        stream_type = service_config.pop('type')

        checker_main = stream_types[stream_type]
        logger.info('Loaded stream checker={}, type={}, testmode={}', name, stream_type, args.test)
        coro_list.append(checker_main(service_config, callback_list, join(args.cache_dir, f'cache-{name}.json'), args.test))

    await asyncio.gather(*coro_list)
