import pathlib

from loguru import logger
from yaml import safe_load

from stream_notifier.model import Color

from .base import CheckerBase, CheckerConfig


class DebugCheckerConfig(CheckerConfig):
    file: pathlib.Path
    color: Color = "00ff00"


class DebugChecker(CheckerBase):
    def __init__(self, config: DebugCheckerConfig):
        self.config = config
        logger.info("Target File: {}", self.config.file)

    async def run_check(self, last_notified):
        with self.config.file.open() as f:
            data = safe_load(f)
        return data

    def verify_push(self, last_notified, current_info):
        if current_info.id == last_notified.id:
            return False

        if not current_info.should_push:
            raise ValueError("Push is disabled!")

        return True

    @classmethod
    def summary(cls, info):
        return info
