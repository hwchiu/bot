from __future__ import annotations

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from .. import chains
from .utils import get_message_text


async def handle_polish(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    message_text = get_message_text(update)
    if not message_text:
        return

    text = chains.polish(message_text)
    logger.info("Polished text: {}", text)

    await update.message.reply_text(text)
