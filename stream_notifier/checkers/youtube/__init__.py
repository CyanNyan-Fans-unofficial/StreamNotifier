from typing import Optional

from loguru import logger

from stream_notifier.model import Color

from ..base import CheckerBase, CheckerConfig
from .youtube_api_client import build_client


class YoutubeCheckerConfig(CheckerConfig):
    color: Color = "ff0000"
    check_interval: int = 10
    client_secret: str
    token: Optional[str] = None

    def create_client(self):
        return build_client(client_secret=self.client_secret, token=self.token)


class YoutubeChecker(CheckerBase):
    def __init__(self, config: YoutubeCheckerConfig):
        self.config = config
        self.client = self.config.create_client()
        logger.info("Application successfully authorized.")

    async def run_check(self, last_notified):
        active = self.client.get_active_user_broadcasts(max_results=1)
        if active:
            # gotcha! there's active stream
            stream = active[0]

            logger.debug("Found Active stream: {}", stream)
            return stream.as_dict()

    async def process_result(self, info):
        if info.description:
            description = info.description.strip().split("\n")
            info.description_first_line = description[0]

    def verify_push(self, last_notified, current_info):
        if current_info.id == last_notified.id:
            return False

        if current_info.title == last_notified.title:
            raise ValueError("YouTube stream title did not change!")

        if current_info.privacy_status == "private":
            raise ValueError("YouTube Stream is private!")

        return True

    def summary(self, info):
        return {
            "Started": info.actual_start_time,
            "Title": info.title,
            "Privacy": info.privacy_status,
            "link": info.link,
            "Live": info.life_cycle_status,
        }
