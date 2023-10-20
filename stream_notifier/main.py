import argparse
import asyncio
import pathlib

from .PushMethod import Push
from loguru import logger
from yaml import safe_load
from .checkers import StreamChecker


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
    parser.add_argument(
        "--push-test",
        nargs=2,
        help="Send a test push into specific push destination and quit.",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Do not use cache file."
    )
    args = parser.parse_args()

    # Load the config meow meow
    with open(args.path, encoding="utf8") as f:
        config = safe_load(f)

    # Verify push methods
    push_methods_config = config.pop("push methods")
    push = Push(push_methods_config, test_mode=args.test)
    logger.info(f'Verified push methods: {", ".join(push.methods.keys())}')

    if args.push_test:
        destination, content = args.push_test
        push.send_push({destination: content})
        return

    # Initialize stream checkers
    coro_list = []
    for name, service_config in config.items():
        if args.no_cache:
            cache_file = None
        else:
            cache_file = pathlib.Path(args.cache_dir) / f"cache-{name}.json"
        checker = StreamChecker(service_config, push, cache_file)
        logger.info(
            "Loaded stream checker={}, type={}, test_mode={}",
            name,
            checker.config.type,
            args.test,
        )
        coro_list.append(checker.run())

    await asyncio.gather(*coro_list)
