import tweepy
from loguru import logger

from .base import Push


class TwitterPush(Push):
    def __init__(self, config: dict):
        self.api_key = config["api key"]
        self.api_secret = config["api secret key"]

        self.token = config["access token"]
        self.token_secret = config["access token secret"]

        if not all((self.api_key, self.api_secret, self.token, self.token_secret)):
            logger.info("One or more Twitter parameters empty, skipping.")
            raise ValueError("One or more Twitter parameters empty, skipping.")

        # Use API v2 to send tweet
        self.api = tweepy.Client(
            consumer_key=self.api_key,
            consumer_secret=self.api_secret,
            access_token=self.token,
            access_token_secret=self.token_secret,
        )

    async def send(self, content, context):
        self.api.create_tweet(text=content)

        logger.info("Notified to twitter.")
