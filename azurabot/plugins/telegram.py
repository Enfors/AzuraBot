import asyncio
import configparser
import logging
import pprint

from aiogram import Bot, Dispatcher, types

import azurabot

from azurabot.interface.asyncinterface import AsyncInterface

config = configparser.ConfigParser()
config.read("etc/azurabot.conf")
token = config["telegram"]["api_key"]
logging.basicConfig(level=logging.INFO)

# bot = Bot(token=token)
# dp = Dispatcher(bot)

"""
Message structure:

[('message_id', 44),
 ('from',
  {'first_name': 'Christer',
   'id': 1212215613,
   'is_bot': False,
   'language_code': 'en',
   'last_name': 'Enfors',
   'username': 'CEnfors'}),
 ('chat',
  {'first_name': 'Christer',
   'id': 1212215613,
   'last_name': 'Enfors',
   'type': 'private',
   'username': 'CEnfors'}),
 ('date', 1594034606),
 ('text', 'hoho')]
"""


class Plugin(AsyncInterface):

    async def run(self):
        self.bot.log_debug("Telegram", "Telegram plugin starting.")
        self.telegram_bot = Bot(token=token)
        self.dp = Dispatcher(self.telegram_bot)
        self.dp.register_message_handler(self._handle_inc_message)
        asyncio.create_task(self._send_loop())
        asyncio.create_task(self._poll())
        self.bot.log_info("telegram", "Telegram plugin started.")

    async def _poll(self):
        # This call (start_polling) used to be part of the run() function
        # above, but it doesn't return - so I had to move it to its own
        # function, so that I could create a task for it.
        await self.dp.start_polling()

    async def _handle_inc_message(self, message: types.Message):
        pprint.pprint(list(message))
        # await message.reply("It works!")

        username = message["chat"]["username"]
        telegram_uid = message["from"]["id"]
        text = message["text"]

        user = azurabot.user.User(self.bot,
                                  identifiers={"telegram": telegram_uid})

        self.bot.log_info("Telegram", f"Message from {username}: '{text}'")
        await self.send_user_text_to_bot(user, text)

    async def _send_loop(self):
        """Gets messages from AzuraBot, and sends them to Telegram.
        """
        keep_running = True

        while keep_running:
            msg = await self.inbox.get()
            user = msg.user
            self.bot.log_debug("Telegram",
                               f"_send_loop: message to send: {msg.text}")
            self.bot.log_debug("Telegram",
                               f"_send_loop: user: {user}")
            await self._send_msg_to_telegram(user, msg)

    async def _send_msg_to_telegram(self, user, msg):
        telegram_uid = user.identifiers["telegram"]
        await self.telegram_bot.send_message(telegram_uid, msg.text)
