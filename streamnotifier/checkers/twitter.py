import tweepy
import tweepy.models

from streamnotifier.model import CheckerConfig, Color


class Config(CheckerConfig):
    color: Color = "00acee"
    api_key: str
    api_secret_key: str
    access_token: str
    access_token_secret: str
    username: str

    def create_client(self):
        auth = tweepy.OAuthHandler(
            self.api_key,
            self.api_secret_key,
            self.access_token,
            self.access_token_secret,
        )
        return tweepy.API(auth)


class TwitterChecker:
    def __init__(self, config):
        self.config = Config.parse_obj(config)
        self.api = self.config.create_client()

    async def run_check(self):
        tweets = self.api.user_timeline(
            screen_name=self.config.username, tweet_mode="extended"
        )
        if not tweets:
            return
        info = tweets[0].__dict__
        info["url"] = f"https://vxtwitter.com/{info['source']}/status/{info['id']}"
        return info

    @classmethod
    def verify_push(cls, last_notified, current_info):
        if not last_notified.get("id"):
            raise ValueError("Last notified ID does not exist!")
        if not last_notified["source"] != current_info["source"]:
            raise ValueError(
                f"Twitter has changed! {last_notified['source']} -> {current_info['source']}"
            )
        return last_notified["id"] != current_info["id"]

    @classmethod
    def summary(cls, info):
        return {"ID": info["id"], "Source": info["source"]}
