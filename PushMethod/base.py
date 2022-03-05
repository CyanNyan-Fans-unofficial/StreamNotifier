"""
Unnecessary dummy ABC
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TwitchStreamNotifyBot.twitch_api_client import TwitchChannel


# This is unnecessary, but for fun


class Push:
    """ABC for all push methods"""

    def send(self, link, channel_object: "TwitchChannel"):
        """Formats text with contents and sends to respective platforms."""
        raise NotImplementedError
