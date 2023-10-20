import tweepy
import tweepy.models
from stream_notifier.model import CheckerConfig, Color
from stream_notifier.utils import flatten_dict
from pydantic import validator

from .base import CheckerBase


class Config(CheckerConfig):
    color: Color = "00acee"
    api_key: str
    api_secret_key: str
    access_token: str
    access_token_secret: str
    username: str | list
    include_retweets: bool = True
    include_quoted: bool = True
    include_replies: bool = True

    @validator("username")
    def convert_username(cls, username):
        if type(username) is str:
            return [username.lower()]
        return [name.lower for name in username]

    def create_client(self):
        auth = tweepy.OAuthHandler(
            self.api_key,
            self.api_secret_key,
            self.access_token,
            self.access_token_secret,
        )
        return tweepy.API(auth, timeout=5)

    def match_name(self, screen_name: str) -> bool:
        return screen_name.lower() in self.username


class TwitterChecker(CheckerBase):
    def __init__(self, config):
        self.config = Config.parse_obj(config)
        self.api = self.config.create_client()

    async def run_check(self):
        # Use home_timeline instead of user_timeline due to Twitter's new restrictions
        tweets = self.api.home_timeline(tweet_mode="extended")
        for tweet in tweets:
            if self.config.match_name(tweet.user.screen_name):
                return tweet._json

    async def process_result(self, info):
        flatten_dict(info, "user")

        # Use third party service to fix Telegram / Discord preview
        info.url = f"https://vxtwitter.com/{info.user_screen_name}/status/{info.id}"

        # Prevent Telegram auto-linking @user
        info.text_no_mention = info.full_text.replace("@", "@\u200c")

    def verify_push(self, last_notified, current_info):
        if not last_notified.id:
            raise ValueError("Last notified ID does not exist!")

        if current_info.retweeted_status and not self.config.include_retweets:
            return False

        if current_info.quoted_status and not self.config.include_quoted:
            return False

        if current_info.in_reply_to_status_id is not None and not self.config.include_replies:
            return False

        # Check if current ID is newer than last notified ID
        return last_notified.id < current_info.id

    @classmethod
    def summary(cls, info):
        return {"User": info.user_screen_name, "URL": info.url}
