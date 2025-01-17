from functools import cache

from loguru import logger

from stream_notifier.model import BaseModel, Color

from ..base import CheckerBase, CheckerConfig
from .twitch_api_client import TwitchClient


class PollingApi(BaseModel):
    twitch_app_id: str
    twitch_app_secret: str


class TwitchCheckerConfig(CheckerConfig):
    color: Color = "a364fe"
    check_interval: int = 2
    channel_name: str
    polling_api: PollingApi

    def create_client(self):
        return TwitchClient(
            self.polling_api.twitch_app_id, self.polling_api.twitch_app_secret
        )


class TwitchChecker(CheckerBase):
    def __init__(self, config: TwitchCheckerConfig):
        self.config = config
        self.client = self.config.create_client()
        logger.info("Target Channel: {}", self.config.channel_name)

    @cache
    def get_user(self):
        return self.client.get_user(self.config.channel_name)

    async def run_check(self, last_notified):
        user = self.get_user()

        output = self.client.get_stream(user.id, log=False)

        if output:
            return output.as_dict()

    async def process_result(self, info):
        info.link = f"https://www.twitch.tv/{info.user_login}"

    def verify_push(self, push_rule, last_notified, current_info):
        if current_info.type != "live":
            return False

        if current_info.started_at == last_notified.started_at:
            return False

        if current_info.title == last_notified.title:
            raise ValueError("Twitch stream title did not change!")

        return True

    @classmethod
    def summary(cls, info):
        return {
            "Started": info.started_at,
            "Title": info.title,
            "Type": info.type,
            "Content": info.game_name,
            "Delay": info.delay,
            "Live": info.is_live,
        }
