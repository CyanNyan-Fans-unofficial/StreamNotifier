import argparse
import asyncio

from . import StreamNotifier


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
