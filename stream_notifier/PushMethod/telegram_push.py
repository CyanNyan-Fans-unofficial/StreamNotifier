from html import escape
from typing import Union

from aiogram import Bot
from aiogram.enums import ParseMode
from loguru import logger

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

        self.bot = Bot(token=self.token)

    async def verify(self):
        if self.skip_verify:
            logger.info("Skip telegram token verification")
            return

        logger.info("Verification of telegram token started.")

        updates = await self.bot.get_updates()
        chats = set()

        # populate set
        for update in updates:
            if update.message:
                chats.add(update.message.chat.id)

        # check diff
        not_found = set(self.chat_ids) - chats

        if not_found:
            for chat_id in not_found:
                logger.warning(
                    "Cannot find group chat id {}, is bot added to the group? Is group inactive?",
                    chat_id,
                )

        logger.info(
            "Verification of telegram token completed. {} of {} chats are visible.",
            len(chats),
            len(self.chat_ids),
        )

    async def send(self, content):
        for chat_id in self.chat_ids:
            try:
                message = await self.bot.send_message(chat_id=chat_id, text=content)
                if self.pin:
                    await self.bot.pin_chat_message(message.chat.id, message.message_id)
                logger.info("Notified to telegram channel {}.", chat_id)
            except Exception:
                logger.exception("Failed to send message or pin: chat id {}.", chat_id)

    async def report(
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
                await self.bot.send_message(
                    chat_id, "\n".join(message), parse_mode=ParseMode.HTML
                )
            except Exception:
                logger.exception("Telegram report failed! chat_id: {}", chat_id)

    async def close(self):
        await self.bot.session.close()
