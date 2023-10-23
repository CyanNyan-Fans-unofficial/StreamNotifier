import argparse
import asyncio
import pathlib

from loguru import logger
from yaml import safe_load

from .checkers import StreamChecker
from .PushMethod import Push


class StreamNotifier:
    def __init__(self, args):
        # Load the config meow meow
        with open(args.path, encoding="utf8") as f:
            config = safe_load(f)

        # Create push methods
        push_config = config.pop("push methods")
        self.push = Push(push_config, test_mode=args.test)
        self.push_test = args.push_test

        # Initialize stream checkers
        self.checker_loops = []
        for name, service_config in config.items():
            cache_file = None
            if not args.no_cache:
                cache_file = pathlib.Path(args.cache_dir) / f"cache-{name}.json"
            checker = StreamChecker(service_config, self.push, cache_file)
            logger.info(
                "Loaded stream checker={}, type={}, test_mode={}",
                name,
                checker.config.type,
                args.test,
            )
            self.checker_loops.append(checker.run())

    async def start(self):
        # Verify push methods
        await self.push.verify_push()
        method_names = ", ".join(self.push.methods.keys())
        logger.info(f"Verified push methods: {method_names}")

        # Push test mode: send push and exit
        if self.push_test:
            destination, content = self.push_test
            await self.push.send_push({destination: content})
            await self.push.close()
            return

        await asyncio.gather(*self.checker_loops)


def stream_notifier_cli():
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
    stream_notifier_instance = StreamNotifier(args)
    asyncio.run(stream_notifier_instance.start())
