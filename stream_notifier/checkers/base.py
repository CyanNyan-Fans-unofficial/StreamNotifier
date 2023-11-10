from typing import Any, Optional

from pydantic import Field, HttpUrl

from stream_notifier.model import BaseModel, Color


class StreamCheckerPushRule(BaseModel):
    contents: dict[str, str]
    rule: dict[str, Any]


class CheckerConfig(BaseModel):
    color: Color = 0
    check_interval: int = 10
    report: list[str]
    push_contents: Optional[dict[str, str]] = None  # Deprecated. Replaced by push_rules
    push_rules: list[StreamCheckerPushRule] = Field(default_factory=list)
    interval: Optional[float] = None
    report_url: Optional[HttpUrl] = None
    report_interval: int = 20


class CheckerBase:
    """ABC for all stream checkers"""

    async def run_check(self, last_notified):
        """Check for requested resource, and return the latest instance in a dict."""

        raise NotImplementedError()

    async def process_result(self, info):
        """Add additional attributes to returned result from run_check."""

        return info

    def verify_push(self, push_rule, last_notified, current_info):
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
