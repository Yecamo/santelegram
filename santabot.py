#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to make a Telegram advent calendar.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""

###### IMPORTS #######
import configparser
import logging

from telegram.ext import Application, Updater, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Bot, Update

try:
	import json
except ImportError:
	import simplejson as json


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__) # i.e logger displays which file the package contains


######## GLOBAL VARIABLES #######

DEBUG = True # if True, accept requests at random time
MONTH = 12
config_file_name = "config.ini" # super original hein


## READ config file and set Auth variables
def init_api():
	config = configparser.ConfigParser()
	config.read(config_file_name)
	API_KEY = config['API']['TOKEN']
	START_TIME = int(config['CONFIG']['STARTTIME'])
	STOP_TIME = int(config['CONFIG']['STOPTIME'])
	return(API_KEY, START_TIME, STOP_TIME)

## SET GLOBAL VARIABLES
(API_KEY, START_TIME, STOP_TIME) = init_api()

########### FUNCTIONS ######## 

"""open config file and read tip in the right category
   chat_id has to be numeric
"""
def read_config(section,key):
	config=configparser.ConfigParser()
	config.read(config_file_name)
	config_value = config[section][key]
	# logger.info("read "+str(key)+" : "+config_value)
	return(config_value)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
async def start(update, context):
	"""Send a message when the command /start is issued."""
	await send_message(update, read_config("CONFIG", "starttext"))

"""return of the day if it's in december (or in month MONAT) between START_TIME and STOP_TIME"""
def is_time_ok(date):
	if(date.month == MONTH or DEBUG):
		if(date.hour >= START_TIME and date.hour <= STOP_TIME or DEBUG):
			return date.day
		else:
			return False
	else:
		return False

async def open_day(update,context):
	"""Sends a tip if and only if the right sender issues /open"""
	# logger.info(update)
	chat = "MACONV"
	# logger.info("chat : "+chat)
	day=is_time_ok(update.message.date)
	# logger.info("day : "+str(day))
	if(day):
		authorized_users = json.loads(read_config(chat,"users"))
		logger.info("users : "+str(authorized_users)+" , open request from : "+str(update.message.from_user.id)+":"+update.message.from_user.first_name)
		logger.info(update.message.from_user.username)
		if(update.message.from_user.id in authorized_users):
			# update.message.reply_text(read_config("CONFIG","opentext")+" "+str(update.message.from_user.first_name))
			await send_message(update, read_config("CONFIG","opentext"))
			array = json.loads(read_config(chat,"messages")) # -1 because array, in contrast to Month, starts with zero
			tip = array[day-1]
			logger.info(tip)
			await send_message(update, tip)
		else:
			# update.message.reply_markdown_v2("Das ist nicht Dein Tag")
			await send_message(update, "Heute ist nicht dein Tag.")


async def send_message(update, msg: str):
	if not isinstance(msg, list):
		if msg.strip().startswith('['):
			lines = json.loads(msg)
		else:
			lines = [msg]
	else:
		lines = msg
	for line in lines:
		if line.startswith('IMAGE:'):
			file = line[6:]
			photo = open(file, 'rb')
			await update.message.reply_photo(photo)
		elif line.startswith('MARKDOWN:'):
			await update.message.reply_markdown_v2(line[9:])
		else:
			await update.effective_message.reply_text(line)

async def help(update, context):
	"""Send a message when the command /help is issued."""
	await send_message(update, read_config("CONFIG", "help"))

async def erreur(update, context):
	"""Echo the user message."""
	await send_message(update, read_config("CONFIG", 'erreur'))
	# update.message.reply_text(read_config("CONFIG",'erreur'))
	# logger.info("erreur : "+str(update))

async def error(update, context):
	"""Log Errors caused by Updates."""
	logger.warning('Update "%s" caused error "%s"', update, context.error)



######## MAIN #######

def main():
	"""Start the bot."""
	# Create the Updater and pass it your bot's token.
	# Make sure to set use_context=True to use the new context based callbacks
	# Post version 12 this will no longer be necessary

	application = Application.builder().token(API_KEY).build()

	application.add_handler(CommandHandler("start", start))

	# updater = Updater(API_KEY)

	# Get the dispatcher to register handlers
	# dp = updater.dispatcher

	# on different commands - answer in Telegram
	application.add_handler(CommandHandler("start", start))
	application.add_handler(CommandHandler("help", help))
	application.add_handler(CommandHandler("open", open_day))

	# on noncommand i.e message - echo the message on Telegram
	application.add_handler(MessageHandler(filters.TEXT, erreur))

	# log all errors
	# dp.add_error_handler(error)

	# Start the Bot
	# updater.start_polling()
	application.run_polling(allowed_updates=Update.ALL_TYPES)

	# bot = Bot(API_KEY)
	# print(bot.send_message("CHAT-ID", 'Message'))

	# Run the bot until you press Ctrl-C or the process receives SIGINT,
	# SIGTERM or SIGABRT. This should be used most of the time, since
	# start_polling() is non-blocking and will stop the bot gracefully.
	# updater.idle()


if __name__ == '__main__':
	main()
