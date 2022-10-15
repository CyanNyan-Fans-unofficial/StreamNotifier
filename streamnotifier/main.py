import argparse
import asyncio
import pathlib

from .PushMethod import Push
from loguru import logger
from yaml import safe_load
from .checker import StreamChecker




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
    push_methods_config = config.pop("push methods")
    push = Push(push_methods_config, test_mode=args.test)
    logger.info(f'Verified push methods: {", ".join(push.methods.keys())}')

    # Initialize stream checkers
    coro_list = []
    for name, service_config in config.items():
        cache_file = pathlib.Path(args.cache_dir) / f"cache-{name}.json"
        checker = StreamChecker(service_config, push, cache_file)
        logger.info(
            "Loaded stream checker={}, type={}, test_mode={}",
            name,
            checker.checker_type,
            args.test,
        )
        coro_list.append(checker.run())

    await asyncio.gather(*coro_list)
