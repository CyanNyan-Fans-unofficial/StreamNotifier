import traceback

from pprint import pformat

from loguru import logger
from discord_webhook import DiscordWebhook, DiscordEmbed
import requests
from typing import Union

from .base import Push


class DiscordPush(Push):
    def __init__(self, config: dict):
        self.webhook_url = config["webhook url"]
        self._verify()

    def _verify(self):
        if not self.webhook_url:
            logger.info("Discord webhook url empty, skipping.")
            raise ValueError("Discord webhook url empty, skipping.")

        logger.info("Verification of discord webhook url started.")

        response = requests.get(self.webhook_url)

        if not response:
            raise AssertionError(f"Webhook verification failed! Response:\n{pformat(response.json())}")

        logger.info("Verification of discord webhook url complete.")

    def send(self, content):
        DiscordWebhook(
            url=self.webhook_url,
            content=content,
            rate_limit_retry=True,
        ).execute()

        logger.info("Notified to discord webhook.")

    def report(self, title="StreamNotifier Status", desc=None, color=None, fields: Union[dict[str, str], None] = None):
        embed = DiscordEmbed(title=title, description=desc, color=color)
        embed.set_timestamp()

        if fields:
            try:
                for title, value in fields.items():
                    if value == "":
                        value = None
                    embed.add_embed_field(name=title, value=str(value))

            except Exception:
                traceback.print_exc(limit=3)

        result = DiscordWebhook(self.webhook_url, embeds=[embed]).execute()

        try:
            result.raise_for_status()
        except Exception as err:
            traceback.print_exception(err, err, err.__traceback__)
