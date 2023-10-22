"""
Simple Twitch API wrapper of what I frequently use.
"""

import time
from datetime import datetime
from pprint import pformat
from typing import Dict, List, Union

import requests
from loguru import logger


class TwitchGame:
    def __init__(self, **kwargs):
        # https://dev.twitch.tv/docs/api/reference#get-games

        self.box_art_url: Union[None, str] = None
        self.id: Union[None, str] = None
        self.name: Union[None, str] = None

        self.__dict__.update(kwargs)

    def __repr__(self):
        string = [f"{k}={v}" for k, v in vars(self).items()]
        return f"TwitchGame({', '.join(string)})"


class TwitchUser:

    def __init__(self, **kwargs):
        # https://dev.twitch.tv/docs/api/reference#get-users

        self.broadcaster_type: Union[None, str] = None
        self.description: Union[None, str] = None
        self.display_name: Union[None, str] = None
        self.id: Union[None, str] = None
        self.login: Union[None, str] = None
        self.offline_image_url: Union[None, str] = None
        self.profile_image_url: Union[None, str] = None
        self.type: Union[None, str] = None
        self.view_count: Union[None, int] = None
        self.email: Union[None, str] = None
        self.created_at: Union[None, str, datetime] = None

        self.__dict__.update(kwargs)

        # if self.created_at:
        #     self.created_at = date_parser.parse(self.created_at)

    def __repr__(self):
        string = [f"{k}={v}" for k, v in vars(self).items()]
        return f"TwitchUser({', '.join(string)})"


class TwitchChannel:

    def __init__(self, **kwargs):
        # https://dev.twitch.tv/docs/api/reference#get-channel-information

        self.broadcaster_id: Union[None, str] = None
        self.broadcaster_language: Union[None, str] = None
        self.broadcaster_login: Union[None, str] = None
        self.game_id: Union[None, str] = None
        self.game_name: Union[None, str] = None
        self.id: Union[None, str] = None
        self.is_live: Union[None, bool] = None
        self.tag_ids: Union[None, List[str]] = None
        self.thumbnail_url: Union[None, str] = None
        self.title: Union[None, str] = None
        self.delay: Union[None, int] = None
        self.started_at: Union[None, str, datetime] = None
        self.type: Union[None, str] = None

        self.__dict__.update(kwargs)

        # if self.started_at:
        #     self.created_at = date_parser.parse(self.started_at)

    def __repr__(self):
        string = [f"{k}={v}" for k, v in vars(self).items()]
        return f"TwitchChannel({', '.join(string)})"

    def as_dict(self):
        return vars(self)


class TwitchClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

        self.header: Dict[str, str] = {}
        self.next_check: int = 0

        self.session: requests.Session = requests.session()

        self.generate_new_header()

    def _get_new_token(self) -> str:
        req_url = f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}" \
                  f"&client_secret={self.client_secret}" \
                  f"&grant_type=client_credentials"

        logger.debug("Sending request: \n{}", req_url)

        req = self.session.post(req_url)
        logger.debug("response: {}", req)

        dict_ = req.json()
        logger.debug("Received: \n{}", pformat(dict_, indent=2))

        token: str = dict_["access_token"]
        expires_in: int = dict_["expires_in"]

        self.next_check = time.time() + (expires_in // 2)
        logger.debug("Received token [{}] with lifespan of {} seconds.", token, expires_in)

        return token

    def generate_new_header(self):

        if time.time() < self.next_check:
            return

        logger.info("Generating new header")

        header = {
            "Authorization": f"Bearer {self._get_new_token()}",
            "Client-ID": f"{self.client_id}"
        }

        self.header = header

    @staticmethod
    def _check_and_raise_error(req: requests.Response, log_response=True):
        try:
            json_ = req.json()
        except Exception as err:
            logger.critical("response: {}\n{}", req, req.text)
            logger.exception("Got error parsing JSON, content:\n{}", req.text)
            return False

        if log_response:
            logger.debug("response: {}\n{}", req, pformat(json_, indent=2))

        if req.status_code != 200:
            raise RuntimeError(f"Got Problem calling API, Response:\n{pformat(json_, indent=2)}")

        if not json_["data"]:
            return False

        return True

    @staticmethod
    def _exact_match(response, key, value):

        for dict_ in response.json()["data"]:
            if dict_[key] == value:
                return dict_

        logger.warning("Could not find exact match of user {}", value)
        raise RuntimeError(f"Can't find exact match of user {value}")

    def get_user(self, user_name) -> TwitchUser:
        self.generate_new_header()

        req_url = f"https://api.twitch.tv/helix/users?&login={user_name}"

        req = self.session.get(req_url, headers=self.header)
        logger.info(req_url)

        self._check_and_raise_error(req)

        return TwitchUser(**self._exact_match(req, "login", user_name))

    def get_channel(self, channel_id) -> TwitchChannel:
        self.generate_new_header()

        req_url = f"https://api.twitch.tv/helix/channels?broadcaster_id={channel_id}"

        req = self.session.get(req_url, headers=self.header)
        logger.info(req_url)

        self._check_and_raise_error(req)

        return TwitchChannel(**req.json()["data"][0])

    def search_channel(self, channel_name) -> Union[TwitchChannel, None]:
        self.generate_new_header()

        req_url = f"https://api.twitch.tv/helix/search/channels?query={channel_name}"

        req = self.session.get(req_url, headers=self.header)
        logger.info(req_url)

        try:
            matched = self._exact_match(req, "broadcaster_login", channel_name)
            logger.debug("response: {}\n{}", req, pformat(matched, indent=2))
        except IndexError:
            logger.debug("response: {}\n{}", req, pformat(req.json(), indent=2))

        if self._check_and_raise_error(req, log_response=False):
            return TwitchChannel(**self._exact_match(req, "broadcaster_login", channel_name))

        return None

    def get_stream(self, user_id, log=True) -> Union[TwitchChannel, None]:
        self.generate_new_header()

        req_url = f"https://api.twitch.tv/helix/streams?user_id={user_id}"

        req = self.session.get(req_url, headers=self.header)
        if log:
            logger.info(req_url)

        if self._check_and_raise_error(req, log):
            return TwitchChannel(**req.json()["data"][0])

        return None

    def get_game(self, game_id="", game_name="") -> TwitchGame:
        self.generate_new_header()

        if game_id:
            req_url = f"https://api.twitch.tv/helix/games?id={game_id}"
        elif game_name:
            req_url = f"https://api.twitch.tv/helix/games?name={game_id}"
        else:
            raise RuntimeError("Provide either non-empty game_id or game_name.")

        req = self.session.get(req_url, headers=self.header)
        logger.info(req_url)

        self._check_and_raise_error(req)

        return TwitchGame(**req.json()["data"][0])
