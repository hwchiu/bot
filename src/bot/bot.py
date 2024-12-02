from __future__ import annotations

import os

from loguru import logger
from telegram import Update
from telegram.ext import Application
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import filters

from . import callbacks


def get_chat_filter() -> filters.BaseFilter:
    whitelist = os.getenv("BOT_WHITELIST")
    if not whitelist:
        logger.warning("No whitelist specified, allowing all chats")
        return filters.ALL
    else:
        chat_ids = [int(chat_id) for chat_id in whitelist.replace(" ", "").split(",")]
        return filters.Chat(chat_ids)


def run_bot() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN is not set")

    chat_filter = get_chat_filter()

    app = Application.builder().token(token).build()
    app.add_handlers(
        [
            CommandHandler("help", callbacks.help, filters=chat_filter),
            CommandHandler("sum", callbacks.summarize, filters=chat_filter),
            CommandHandler("jp", callbacks.create_translate_callback("Japanese"), filters=chat_filter),
            CommandHandler("tc", callbacks.create_translate_callback("Traditional Chinese"), filters=chat_filter),
            CommandHandler("en", callbacks.create_translate_callback("English"), filters=chat_filter),
            CommandHandler("polish", callbacks.polish, filters=chat_filter),
            CommandHandler("yf", callbacks.query_ticker, filters=chat_filter),
            CommandHandler("twse", callbacks.query_twse_ticker, filters=chat_filter),
            CommandHandler("yt", callbacks.search_youtube, filters=chat_filter),
            CommandHandler("g", callbacks.search_google, filters=chat_filter),
            CommandHandler("recipe", callbacks.generate_recipe, filters=chat_filter),
            CommandHandler("trip", callbacks.trip, filters=chat_filter),
            CommandHandler("jlpt", callbacks.learn_japanese, filters=chat_filter),
            CommandHandler("echo", callbacks.echo),
            MessageHandler(filters=chat_filter, callback=callbacks.summarize_document),
        ]
    )
    app.add_handler(MessageHandler(filters=chat_filter, callback=callbacks.log), group=1)

    app.add_error_handler(callbacks.error_callback)
    app.run_polling(allowed_updates=Update.ALL_TYPES)
