"""
Unnecessary dummy ABC
"""
from typing import Union


# This is unnecessary, but for fun
class Push:
    """ABC for all push methods"""

    async def verify(self):
        pass

    async def send(self, content: str, context):
        """Formats text with contents and sends to respective platforms.

        Additional formatting variables can be provided as keyword arguments."""
        raise NotImplementedError()

    async def report(
        self,
        title: str,
        description: str,
        color: str,
        fields: Union[dict[str, str], None] = None,
    ):
        raise NotImplementedError()

    async def close(self):
        pass
