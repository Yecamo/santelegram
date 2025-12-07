#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Telegram advent calendar bot.

AI ANNOTATION:
- Sections marked between "### AI-EDIT START" and "### AI-EDIT END" were inserted/modified by an AI assistant.
- Everything outside those markers is unchanged from prior behavior or preserved author code where possible.
"""

####### IMPORTS #######
import configparser
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from telegram import Update, constants
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

######## GLOBAL VARIABLES #######
DEBUG = True  # if True, accept requests at random time (useful for local testing)
MONTH = 12

# base directory for resolving image filenames and config file location
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = str(BASE_DIR / "config.ini")

# Globals to track last sent date
has_sent_message_today = False
last_sent_date: Optional[datetime] = None


def _find_section_name(cfg: configparser.ConfigParser, desired: str) -> Optional[str]:
    """
    Return the actual section name in cfg that matches 'desired' case-insensitively,
    or None if not found.
    """
    for sec in cfg.sections():
        if sec.lower() == desired.lower():
            return sec
    return None


### AI-EDIT START: Robust config loading and init_api improvements ###
def init_api():
    """Read API_KEY, START_TIME and STOP_TIME from config (robustly)."""
    config = configparser.ConfigParser()
    read_files = config.read(CONFIG_FILE)
    if not read_files:
        logger.error("Config file not found at %s. Please create config.ini next to the script.", CONFIG_FILE)
        raise SystemExit(1)

    api_section = _find_section_name(config, "API")
    if not api_section:
        logger.error("No [API] section found in %s. Please add one (see config_example.ini).", CONFIG_FILE)
        raise SystemExit(1)

    # option names are case-insensitive by default; try common variations for token
    token = None
    for token_key in ("token", "TOKEN", "Token"):
        if config.has_option(api_section, token_key):
            token = config.get(api_section, token_key).strip()
            break

    if not token:
        logger.error("API token not found in section [%s] of %s. Add 'token = <your-bot-token>'", api_section, CONFIG_FILE)
        raise SystemExit(1)

    # find CONFIG section (case-insensitive)
    cfg_section = _find_section_name(config, "CONFIG")
    if cfg_section:
        starttime_str = config.get(cfg_section, "starttime", fallback="0")
        stoptime_str = config.get(cfg_section, "stoptime", fallback="23")
    else:
        starttime_str = "0"
        stoptime_str = "23"
        logger.warning("No [CONFIG] section found in %s — using defaults for starttime/stoptime.", CONFIG_FILE)

    try:
        starttime = int(starttime_str)
    except Exception:
        logger.warning("Invalid starttime '%s' in config; using 0", starttime_str)
        starttime = 0
    try:
        stoptime = int(stoptime_str)
    except Exception:
        logger.warning("Invalid stoptime '%s' in config; using 23", stoptime_str)
        stoptime = 23

    return token, starttime, stoptime
### AI-EDIT END ###


(API_KEY, START_TIME, STOP_TIME) = init_api()


########### HELPERS ########


def read_config(section: str, key: str, fallback: Optional[str] = None) -> Optional[str]:
    """Read a value from the config file with an optional fallback (case-insensitive section)."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    actual_section = _find_section_name(config, section)
    if actual_section and key in config[actual_section]:
        return config[actual_section][key]
    return fallback


def get_last_sent_date() -> Optional[datetime]:
    """Get last_sent_date from config (ISO format)."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    actual_section = _find_section_name(config, "CONFIG")
    if actual_section:
        last_date_str = config.get(actual_section, "last_sent_date", fallback=None)
    else:
        last_date_str = None
    if last_date_str:
        try:
            return datetime.fromisoformat(last_date_str)
        except Exception:
            logger.exception("Failed to parse last_sent_date from config: %s", last_date_str)
    return None


def save_last_sent_date(date: datetime) -> None:
    """Save last_sent_date in ISO format to config (creates section if needed)."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    actual_section = _find_section_name(config, "CONFIG")
    if not actual_section:
        # create a canonical section name
        config["CONFIG"] = {}
        actual_section = "CONFIG"
    config[actual_section]["last_sent_date"] = date.isoformat()
    with open(CONFIG_FILE, "w") as configfile:
        config.write(configfile)


def is_time_ok(date: datetime) -> bool:
    """
    Return True if the given datetime is within configured month/hour ranges
    (or if DEBUG=True).
    """
    if DEBUG:
        return True
    in_month = date.month == MONTH
    in_hour = START_TIME <= date.hour <= STOP_TIME
    return in_month and in_hour


### AI-EDIT START: send_message supports IMAGE & MARKDOWN for interactive messages ###
async def send_message(update: Update, msg: Any) -> None:
    """
    Send message(s) to the chat that triggered 'update'.
    msg may be:
    - a Python list of strings
    - a JSON-encoded list string ('["a","b"]')
    - a plain string (single message)
    Special prefixes supported:
    - 'IMAGE:<path-or-filename>' -> sends photo from provided path or from same dir as script
    - 'MARKDOWN:<text>' -> sends markdown_v2 text
    """
    # Normalize into list of strings
    lines: List[str]
    if isinstance(msg, list):
        lines = msg
    elif isinstance(msg, str):
        text = msg.strip()
        if text.startswith("[") and (text.endswith("]") or "\n" in text):
            try:
                lines = json.loads(text)
            except Exception:
                lines = [msg]
        else:
            lines = [msg]
    else:
        lines = [str(msg)]

    for line in lines:
        if not line:
            continue
        if line.startswith("IMAGE:"):
            file_spec = line[6:].strip()
            p = Path(file_spec)
            # If not absolute and file doesn't exist, try same dir as script
            if not p.is_absolute():
                candidate = BASE_DIR / file_spec
                if candidate.exists():
                    p = candidate
            if not p.exists():
                logger.error("Image file not found: %s (tried %s)", file_spec, p)
                await update.effective_message.reply_text("Image not found: " + file_spec)
                continue
            try:
                with open(p, "rb") as photo:
                    await update.effective_message.reply_photo(photo)
            except Exception:
                logger.exception("Failed to send image: %s", p)
                await update.effective_message.reply_text("Failed to send image.")
        elif line.startswith("MARKDOWN:"):
            await update.effective_message.reply_markdown_v2(line[9:])
        else:
            await update.effective_message.reply_text(line)
### AI-EDIT END ###


### AI-EDIT START: send_content_to_chat for auto_send to send images/markdown ###
async def send_content_to_chat(context, chat_id: int, content: Any) -> None:
    """
    Send content to a chat_id using context.bot.
    Supports same prefixes as send_message: IMAGE:, MARKDOWN:
    content may be a list or a string.
    """
    # Normalize into list of strings
    if isinstance(content, list):
        items = content
    elif isinstance(content, str):
        text = content.strip()
        if text.startswith("[") and (text.endswith("]") or "\n" in text):
            try:
                items = json.loads(text)
            except Exception:
                items = [content]
        else:
            items = [content]
    else:
        items = [str(content)]

    for item in items:
        if not item:
            continue
        if isinstance(item, str) and item.startswith("IMAGE:"):
            file_spec = item[6:].strip()
            p = Path(file_spec)
            # If not absolute and file doesn't exist, try same dir as script
            if not p.is_absolute():
                candidate = BASE_DIR / file_spec
                if candidate.exists():
                    p = candidate
            if not p.exists():
                logger.error("Image file not found for auto-send: %s (tried %s)", file_spec, p)
                try:
                    await context.bot.send_message(chat_id=chat_id, text="Image not found: " + file_spec)
                except Exception:
                    logger.exception("Failed to notify user about missing image.")
                continue
            try:
                with open(p, "rb") as photo:
                    await context.bot.send_photo(chat_id=chat_id, photo=photo)
            except Exception:
                logger.exception("Failed to send image in auto_send: %s", p)
                try:
                    await context.bot.send_message(chat_id=chat_id, text="Failed to send image: " + file_spec)
                except Exception:
                    logger.exception("Failed to notify user after image send failure.")
        elif isinstance(item, str) and item.startswith("MARKDOWN:"):
            md = item[9:]
            try:
                await context.bot.send_message(chat_id=chat_id, text=md, parse_mode=constants.ParseMode.MARKDOWN_V2)
            except Exception:
                logger.exception("Failed to send markdown message to %s", chat_id)
                try:
                    await context.bot.send_message(chat_id=chat_id, text=md)
                except Exception:
                    logger.exception("Failed to fall back to plaintext for markdown message.")
        else:
            # plain text
            try:
                await context.bot.send_message(chat_id=chat_id, text=str(item))
            except Exception:
                logger.exception("Failed to send text message to %s", chat_id)
### AI-EDIT END ###


async def send_message_to_user(context, user_id: int, username: Optional[str], message: Any) -> None:
    """Send a message (or image/markdown) to a user by chat_id (handles IMAGE:/MARKDOWN:)."""
    logger.info("Sending message to user ID: %s (%s) message: %s", user_id, username, message)
    try:
        await send_content_to_chat(context, int(user_id), message)
    except Exception:
        logger.exception("Failed to send content to user ID %s (%s)", user_id, username)


########### HANDLERS (commands use _command, non-commands use _handler) ########


async def start_command(update: Update, context) -> None:
    """Send a message when the command /start is issued."""
    text = read_config("CONFIG", "starttext", fallback="Welcome!")
    await send_message(update, text)


async def help_command(update: Update, context) -> None:
    """Send a message when the command /help is issued."""
    text = read_config("CONFIG", "help", fallback="No help configured.")
    await send_message(update, text)


async def erreur_handler(update: Update, context) -> None:
    """Reply to non-command messages (fallback)."""
    # prefer 'erreur' but fall back to 'error' for backwards compatibility
    text = read_config("CONFIG", "erreur", fallback=read_config("CONFIG", "error", fallback="I didn't understand that."))
    await send_message(update, text)


async def error_handler(update: object, context) -> None:
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def _is_user_authorized(user_id: int, authorized_json: str) -> bool:
    """
    authorized_json may be a JSON list of numeric ids, or a list of objects
    like [{"id": 123, "username": "..."}]. This helper handles both.
    """
    try:
        auth = json.loads(authorized_json)
    except Exception:
        logger.exception("Failed to parse authorized users JSON.")
        return False

    # If list of dicts
    if isinstance(auth, list):
        if not auth:
            return False
        first = auth[0]
        if isinstance(first, dict):
            return any((u.get("id") == user_id or str(u.get("id")) == str(user_id)) for u in auth)
        # assume list of ids
        try:
            return any(int(u) == int(user_id) for u in auth)
        except Exception:
            return False
    return False


async def open_command(update: Update, context) -> None:
    """Open today's day if it's allowed and the user is authorized."""
    if not update.message:
        return
    date = update.message.date or datetime.now()
    if not is_time_ok(date):
        await send_message(update, "Not the right time to open a day.")
        return

    chat_section = "MACONV"
    users_json = read_config(chat_section, "users", fallback="[]")
    logger.info("Open request from: %s (%s)", update.message.from_user.id, update.message.from_user.first_name)

    if _is_user_authorized(update.message.from_user.id, users_json):
        # Send open-text and the tip for the day
        await send_message(update, read_config("CONFIG", "opentext", fallback="Here is your tip:"))
        messages_json = read_config(chat_section, "messages", fallback="[]")
        try:
            messages = json.loads(messages_json)
        except Exception:
            logger.exception("Failed to parse messages for %s", chat_section)
            messages = []

        day_index = date.day - 1
        if 0 <= day_index < len(messages):
            tip = messages[day_index]
            await send_message(update, tip)
        else:
            await send_message(update, "No tip configured for today.")
    else:
        await send_message(update, "Heute ist nicht dein Tag.")


########### SCHEDULED JOB ########

### AI-EDIT START ###
async def auto_send(context) -> None:
    """
    Scheduled job that sends daily messages to all configured users.
    Uses get_last_sent_date/save_last_sent_date to avoid sending multiple times per day.
    """
    global has_sent_message_today, last_sent_date
    current_date = datetime.now()
    last_sent_date = get_last_sent_date()
    logger.info("auto_send: current_date=%s last_sent_date=%s", current_date, last_sent_date)

    if last_sent_date is None or last_sent_date.date() != current_date.date():
        has_sent_message_today = False
    else:
        has_sent_message_today = True

    if has_sent_message_today and not DEBUG:
        logger.info("Message already sent today; skipping.")
        return

    messages_json = read_config("MACONV", "messages", fallback="[]")
    users_json = read_config("MACONV", "users", fallback="[]")

    try:
        messages = json.loads(messages_json)
    except Exception:
        logger.exception("Failed to parse messages JSON.")
        messages = []

    try:
        users = json.loads(users_json)
    except Exception:
        logger.exception("Failed to parse users JSON.")
        users = []

    current_day = current_date.day
    if 1 <= current_day <= len(messages):
        daily_messages = messages[current_day - 1]
        # Ensure daily_messages is a list
        if not isinstance(daily_messages, list):
            daily_messages = [daily_messages]
        for user in users:
            # Support both dict users (with "id"/"username") and plain id lists
            if isinstance(user, dict):
                user_id = user.get("id")
                username = user.get("username")
            else:
                user_id = int(user)
                username = None
            if user_id is None:
                continue
            for message in daily_messages:
                # send_content_to_chat handles IMAGE:/MARKDOWN: as needed
                await send_message_to_user(context, int(user_id), username, message)
        has_sent_message_today = True
        save_last_sent_date(current_date)
        logger.info("All messages sent successfully. Last sent date updated.")
    else:
        logger.info("No message configured for day %s", current_day)

### AI-EDIT END ###

######## MAIN ########


def main():
    """Start the bot."""
    application = Application.builder().token(API_KEY).build()

    # Schedule auto_send to run once shortly after start (original behavior).
    application.job_queue.run_once(auto_send, when=30)

    # Register handlers (commands use *_command, non-commands use *_handler)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("open", open_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, erreur_handler))

    # Start polling
    application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()