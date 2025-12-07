# Telegram Bot

## installation

```
pip install python-telegram-bot
pip install telethon
pip install configparser logging
git clone https://github.com/Yecamo/santelegram.git
```

## usage : 

> RDumarais did a *huge* tutorial for beginners (in French) on his personal blog and here : https://github.com/RduMarais/santelegram/blob/master/Tutoriel.md It is pretty outdated but can be useful for understanding what the original bot does and why.

 * Change the **config_example.ini** file name to **config.ini**
 * Write in it the Advent Calendar you want, with the usernames you want to be able to open.
 * get the usernames with telethon_get_users.py (or just look them up with one of the methods mentioned below)
 * put your API token in the config.ini
 * run 


```bash
python santabot.py
```
Stop it with Ctrl+C

Enjoy


# documentation : 

 * API python : https://python-telegram-bot.readthedocs.io/en/stable/telegram.chat.html#telegram.Chat
 * get chat ID : https://www.wikihow.com/Know-Chat-ID-on-Telegram-on-Android
 	 * mieux https://www.wikihow.com/Know-a-Chat-ID-on-Telegram-on-PC-or-Mac
   * in Mercurygram (fork of Telegram for Android) you can look up the IDs on the info pop-up of chats and groups: https://github.com/Mercurygram/Mercurygram
   * on Telegram Web you can move your cursor over chats; after a while it appears a small window with the chat ID
   * there are also a few Telegram bots who fetch the user IDs for you, like @userinfobot

# AI-assisted changes and transparency :

Some edits in this repository were created or refactored with assistance from an AI (OpenAI ChatGPT). We document these edits here to maintain transparency and make it easy for reviewers to find and evaluate AI-assisted code.

What "AI-assisted" means
- "AI-assisted" indicates that an AI model helped structure, suggest, or refactor parts of the code. Human maintainers reviewed and committed the changes.
- The repository does not delegate acceptance of changes to the AI — human reviewers are responsible for validating behavior, style, and security.

How AI-assisted edits are marked in the code
- AI-assisted functions or sections include in-code comments such as:
  - # This function was structured with assistance from OpenAI's ChatGPT
  - or the recommended short marker:
    - # AI-ASSISTED: structured with OpenAI ChatGPT (YYYY-MM-DD) — brief note of why changed
- These markers make it simple to search the codebase for AI-assisted changes.
