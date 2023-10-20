import traceback
from html import escape
from typing import Union

import telegram
from loguru import logger
from telegram.parsemode import ParseMode

from .base import Push


class TelegramPush(Push):
    def __init__(self, config: dict):
        self.token = config["token"]
        self.chat_ids = config["chat id"]
        self.pin = config.get("pin", False)
        self.skip_verify = config.get("skip_verify", False)

        if not all((self.token, self.chat_ids)):
            logger.info("One or more Telegram parameters are empty, skipping.")
            raise ValueError("One or more Telegram parameters are empty, skipping.")

        self.bot = telegram.Bot(token=self.token)

    def verify(self):
        if self.skip_verify:
            logger.info("Skip telegram token verification")
            return

        logger.info("Verification of telegram token started.")

        updates = self.bot.get_updates()

        effective_chats = set()

        # populate set
        update: telegram.Update

        for update in updates:
            effective_chats.add(update.effective_chat.id)

        # check diff
        not_found = set(self.chat_ids) - effective_chats

        if not_found:
            for chat_id in not_found:
                logger.warning(
                    "Cannot find group chat id {}, is bot added to the group? Is group inactive?",
                    chat_id,
                )

        reachable = len(self.chat_ids) - len(not_found)
        logger.info(
            "Verification of telegram token completed. {} of {} chats are visible.",
            reachable,
            len(self.chat_ids),
        )

    def send(self, content):
        for chat_id in self.chat_ids:
            try:
                message: telegram.Message = self.bot.send_message(
                    chat_id=chat_id, text=content
                )
                if self.pin:
                    self.bot.pin_chat_message(message.chat_id, message.message_id)
                logger.info("Notified to telegram channel {}.", chat_id)
            except Exception:
                traceback.print_exc()
                logger.warning("Failed to send message or pin: chat id {}.", chat_id)

    def report(
        self,
        title="StreamNotifier Status",
        desc=None,
        color=None,
        fields: Union[dict[str, str], None] = None,
    ):
        message = []

        if title:
            message.extend([f"<b>{escape(title)}</b>", ""])

        if desc:
            message.extend([escape(desc), ""])

        if fields:
            for title, value in fields.items():
                if title:
                    message.append(f"<b>{escape(str(title))}</b>")
                if value:
                    message.append(f"{escape(str(value))}")
                message.append("")

        for chat_id in self.chat_ids:
            try:
                self.bot.send_message(
                    chat_id, "\n".join(message), parse_mode=ParseMode.HTML
                )
            except Exception as err:
                traceback.print_exception(err, err, err.__traceback__)
