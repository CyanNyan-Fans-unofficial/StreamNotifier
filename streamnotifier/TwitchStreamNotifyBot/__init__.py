from functools import cache

from loguru import logger

from .twitch_api_client import TwitchClient


class RequestInstance:
    color = 'a364fe'
    check_interval = 2

    def __init__(self, config):
        client_id = config["polling api"]["twitch app id"]
        client_secret = config["polling api"]["twitch app secret"]

        self.channel_name = config["channel name"]
        self.client = TwitchClient(client_id, client_secret)

        logger.info("Target Channel: {}", self.channel_name)

    @cache
    def get_user(self):
        return self.client.get_user(self.channel_name)

    async def run_check(self):
        user = self.get_user()

        output = self.client.get_stream(user.id, log=False)

        if output and output.type == "live":
            return output.as_dict()

    @classmethod
    def verify_push(cls, last_notified, current_info):
        if current_info.get("started_at") != last_notified.get("started_at"):
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
