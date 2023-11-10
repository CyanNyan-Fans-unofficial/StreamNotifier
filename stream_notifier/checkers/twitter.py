import tweepy
import tweepy.models
from pydantic import Field, field_validator

from stream_notifier.model import BaseModel, Color
from stream_notifier.utils import flatten_dict

from .base import CheckerBase, CheckerConfig


class TwitterCheckerPushRule(BaseModel):
    username: str | list[str]
    include_retweets: bool = True
    include_quoted: bool = True
    include_replies: bool = True
    skip_tags: list[str] = Field(default_factory=list)

    @field_validator("username")
    @classmethod
    def convert_username(cls, username):
        if type(username) is str:
            return [username.lower()]
        return map(str.lower, username)

    def match_name(self, screen_name: str) -> bool:
        return screen_name.lower() in self.username


class TwitterCheckerConfig(CheckerConfig):
    color: Color = "00acee"
    api_key: str
    api_secret_key: str
    access_token: str
    access_token_secret: str

    def create_client(self):
        auth = tweepy.OAuthHandler(
            self.api_key,
            self.api_secret_key,
            self.access_token,
            self.access_token_secret,
        )
        return tweepy.API(auth, timeout=5)


class TwitterChecker(CheckerBase):
    def __init__(self, config: TwitterCheckerConfig):
        self.config = config
        self.api = self.config.create_client()

    async def run_check(self, last_notified):
        # Use home_timeline instead of user_timeline due to Twitter's new restrictions
        tweets = self.api.home_timeline(tweet_mode="extended")
        if not last_notified.id:
            return tweets[0]._json
        for tweet in reversed(tweets):
            if last_notified.id < tweet.id:
                return tweet._json

    async def process_result(self, info):
        flatten_dict(info, "user")

        # Use third party service to fix Telegram / Discord preview
        url_path = f"/{info.user_screen_name}/status/{info.id}"
        info.url_vxtwitter = f"https://vxtwitter.com{url_path}"
        info.url_fxtwitter = f"https://fxtwitter.com{url_path}"
        info.url_twittpr = f"https://twittpr.com{url_path}"
        info.url_fixupx = f"https://fixupx.com{url_path}"
        info.url = info.url_fxtwitter

        # Prevent Telegram auto-linking @user
        info.text_no_mention = info.full_text.replace("@", "@\u200c")

    def verify_push(
        self, push_rule: TwitterCheckerPushRule, last_notified, current_info
    ):
        if not last_notified.id:
            raise ValueError("Last notified ID does not exist!")

        if not push_rule.match_name(current_info.user_screen_name):
            return False

        if current_info.retweeted_status and not push_rule.include_retweets:
            return False

        if current_info.quoted_status and not push_rule.include_quoted:
            return False

        if (
            current_info.in_reply_to_status_id is not None
            and not push_rule.include_replies
        ):
            return False

        for hashtag in current_info.entities.hashtags:
            tag = hashtag.text
            if tag in push_rule.skip_tags:
                raise ValueError(f"Hashtag is skipped! #{tag}")

        # Check if current ID is newer than last notified ID
        return last_notified.id < current_info.id

    @classmethod
    def summary(cls, info):
        return {"User": info.user_screen_name, "URL": info.url}
