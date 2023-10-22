from stream_notifier.model import BaseModel, Color


class CheckerConfig(BaseModel):
    color: Color = 0
    check_interval: int = 10


class CheckerBase:
    """ABC for all stream checkers"""

    async def run_check(self, last_notified):
        """Check for requested resource, and return the latest instance in a dict."""

        raise NotImplementedError()

    async def process_result(self, info):
        """Add additional attributes to returned result from run_check."""

        return info

    def verify_push(self, last_notified, current_info):
        """Confirm whether the resource need to trigger a push notification.

        Returns:
        * None or False: Do not trigger push notification.
        * True: Trigger push notification.
        * raise ValueError: Do not trigger notification but send a report.
        """
        return False

    @classmethod
    def summary(cls, info):
        return info
