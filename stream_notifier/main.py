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
        self.checkers = set()
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
            self.checkers.add(checker)

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

        await asyncio.gather(*(checker.run() for checker in self.checkers))
