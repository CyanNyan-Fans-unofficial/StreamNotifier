from pprint import pformat
from typing import Union

import requests
from discord_webhook import DiscordEmbed, DiscordWebhook
from loguru import logger

from .base import Push


class DiscordPush(Push):
    def __init__(self, config: dict):
        self.webhook_url = config["webhook url"]
        if not self.webhook_url:
            logger.info("Discord webhook url empty, skipping.")
            raise ValueError("Discord webhook url empty, skipping.")

    async def verify(self):
        logger.info("Verification of discord webhook url started.")

        response = requests.get(self.webhook_url)

        if not response:
            raise AssertionError(
                f"Webhook verification failed! Response:\n{pformat(response.json())}"
            )

        logger.info("Verification of discord webhook url complete.")

    async def send(self, content):
        DiscordWebhook(
            url=self.webhook_url,
            content=content,
            rate_limit_retry=True,
        ).execute()

        logger.info("Notified to discord webhook.")

    async def report(
        self,
        title="StreamNotifier Status",
        desc=None,
        color=None,
        fields: Union[dict[str, str], None] = None,
    ):
        embed = DiscordEmbed(title=title, description=desc, color=color)
        embed.set_timestamp()

        if fields:
            for title, value in fields.items():
                if value == "":
                    value = None
                embed.add_embed_field(name=title, value=str(value))

        result = DiscordWebhook(self.webhook_url, embeds=[embed]).execute()
        result.raise_for_status()
