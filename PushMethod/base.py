"""
Unnecessary dummy ABC
"""


# This is unnecessary, but for fun


class Push:
    """ABC for all push methods"""

    def send(self, channel_object, **kwargs):
        """Formats text with contents and sends to respective platforms.

        Additional formatting variables can be provided as keyword arguments."""
        raise NotImplementedError
