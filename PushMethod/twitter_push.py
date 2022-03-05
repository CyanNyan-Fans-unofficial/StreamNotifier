from typing import TYPE_CHECKING
from typing import Union

import tweepy
from loguru import logger

from .base import Push


class TwitterPush(Push):
    def __init__(self, config: dict, content: str):
        self.content: str = content

        self.api_key = config["api key"]
        self.api_secret = config["api secret key"]

        self.token = config["access token"]
        self.token_secret = config["access token secret"]

        self.api: Union[None, tweepy.API] = None

        self.auth()

    def auth(self):

        if not all((self.api_key, self.api_secret, self.token, self.token_secret)):
            logger.info("One or more Twitter parameters empty, skipping.")
            raise ValueError("One or more Twitter parameters empty, skipping.")

        logger.info("Twitch auth started.")

        auth = tweepy.OAuthHandler(self.api_key, self.api_secret)

        auth.set_access_token(self.token, self.token_secret)

        self.api = tweepy.API(auth)

        logger.info("Twitch auth complete.")

    def send(self, channel_object, **kwargs):

        dict_ = channel_object.as_dict()
        dict_.update(kwargs)

        self.api.update_status(self.content.format(**dict_))

        logger.info("Notified to twitter.")
