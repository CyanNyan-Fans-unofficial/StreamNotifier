import tweepy
import tweepy.models
from stream_notifier.model import CheckerConfig, Color
from stream_notifier.utils import flatten_dict

from .base import CheckerBase


class Config(CheckerConfig):
    color: Color = "00acee"
    api_key: str
    api_secret_key: str
    access_token: str
    access_token_secret: str
    username: str
    include_retweets: bool = True
    include_quoted: bool = True
    include_replies: bool = True
    debug_count: int = 0

    def create_client(self):
        auth = tweepy.OAuthHandler(
            self.api_key,
            self.api_secret_key,
            self.access_token,
            self.access_token_secret,
        )
        return tweepy.API(auth, timeout=5)


class TwitterChecker(CheckerBase):
    def __init__(self, config):
        self.config = Config.parse_obj(config)
        self.api = self.config.create_client()
        self.debug = self.config.debug_count

    async def run_check(self):
        tweets = self.api.user_timeline(
            screen_name=self.config.username, tweet_mode="extended"
        )
        if tweets:
            self.debug = tweet_idx = max(self.debug - 1, 0)
            return tweets[tweet_idx]._json

    async def process_result(self, info):
        flatten_dict(info, "user")
        info.url = f"https://vxtwitter.com/{info.user_screen_name}/status/{info.id}"
        info.text_no_mention = info.full_text.replace("@", "@\u200c")
        info.is_reply = info.in_reply_to_status_id is not None

    def verify_push(self, last_notified, current_info):
        if not last_notified.id:
            raise ValueError("Last notified ID does not exist!")

        if last_notified.user_id != current_info.user_id:
            raise ValueError(
                f"Twitter user has changed! {last_notified.user_screen_name} -> {current_info.user_screen_name}"
            )

        if current_info.retweet_status and not self.config.include_retweets:
            return False

        if current_info.is_quote_status and not self.config.include_quoted:
            return False

        if current_info.is_reply and not self.config.include_replies:
            return False

        return last_notified.id != current_info.id

    @classmethod
    def summary(cls, info):
        return {"User": info.user_screen_name, "URL": info.url}
