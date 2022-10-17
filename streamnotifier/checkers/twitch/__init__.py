from functools import cache

from loguru import logger
from streamnotifier.model import BaseModel, CheckerConfig, Color

from .twitch_api_client import TwitchClient


class PollingApi(BaseModel):
    twitch_app_id: str
    twitch_app_secret: str


class Config(CheckerConfig):
    color: Color = "a364fe"
    check_interval = 2
    channel_name: str
    polling_api: PollingApi

    def create_client(self):
        return TwitchClient(
            self.polling_api.twitch_app_id, self.polling_api.twitch_app_secret
        )


class RequestInstance:
    def __init__(self, config):
        self.config = Config.parse_obj(config)
        self.client = self.config.create_client()
        logger.info("Target Channel: {}", self.config.channel_name)

    @cache
    def get_user(self):
        return self.client.get_user(self.config.channel_name)

    async def run_check(self):
        user = self.get_user()

        output = self.client.get_stream(user.id, log=False)

        if output and output.type == "live":
            return output.as_dict()

    @classmethod
    def verify_push(cls, last_notified, current_info):
        if current_info.get("started_at") == last_notified.get("started_at"):
            return False

        if current_info.get("title") == last_notified.get("title"):
            raise ValueError("Twitch stream title did not change!")

        return True

    @classmethod
    def summary(cls, info):
        return {
            "Started": info["started_at"],
            "Title": info["title"],
            "Type": info["type"],
            "Content": info["game_name"],
            "Delay": info["delay"],
            "Live": info["is_live"],
        }
