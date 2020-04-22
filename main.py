#!/usr/bin/env python3

import os
import logging
from uuid import uuid4
import urllib.parse
import requests
from cachetools import cached, TTLCache

from telegram import InlineQueryResultArticle, ParseMode, \
    InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler
from telegram.utils.helpers import escape_markdown

TOKEN = os.getenv("TOKEN", None)
if not TOKEN:
    print("Define the TOKEN env variable containing the Telegram's token.")
    exit(1)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def start(update, context):
    update.message.reply_text('Reply to a message with /o and I\'ll convert the links.')


def outline_cmd(update, context):
    if not update.message.reply_to_message:
        update.message.reply_text('Reply to a message containing a link to use me.')
        return

    msg = update.message.reply_to_message
    entities = msg.parse_entities("url")
    if not entities:
        entities = msg.parse_caption_entities("url")
    if not entities:
        update.message.reply_text("This message doesn't contain any link.")
        return

    urls = []
    for url in entities.values():
        res = outline(url)
        if not res:
            continue
        res_url = extract_result_url(res)
        urls.append(res_url)

    if not urls:
        update.message.reply_text("Some errors occured: couldn't outline.")
        return

    txt = "\n\n".join(urls)
    update.message.reply_text(txt)


def inlinequery(update, context):
    query = update.inline_query.query
    if not query or len(query) < 4:
        return

    outline_data = outline(query)
    if not outline_data:
        return
    url = extract_result_url(outline_data)

    results = [
        InlineQueryResultArticle(
            id=outline_data["short_code"],
            title=f"Link ready. Click me!",
            input_message_content=InputTextMessageContent(
                f'{url}',
                parse_mode=ParseMode.HTML,
            ))]

    update.inline_query.answer(results)


@cached(cache=TTLCache(maxsize=65536, ttl=86400))
def outline(url: str) -> str:
    enc_url = urllib.parse.quote(url, safe='')
    url = f"https://api.outline.com/v3/parse_article?source_url={enc_url}"
    res = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.113 Safari/537.36",
        "Referer": "https://outline.com/",
        })
    try:
        return res.json()["data"]
    except:
        return None


def extract_result_url(data):
    res_url = f"https://outline.com/{data['short_code']}"
    return res_url



def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("o", outline_cmd))
    dp.add_handler(CommandHandler("outline", outline_cmd))
    dp.add_handler(InlineQueryHandler(inlinequery))

    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
