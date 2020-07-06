import logging

import configparser
import pprint

from aiogram import Bot, Dispatcher, types

from azurabot.interface.asyncinterface import AsyncInterface

config = configparser.ConfigParser()
config.read("etc/azurabot.conf")
token = config["telegram"]["api_key"]
logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)


class Plugin(AsyncInterface):

    async def run(self):
        self.log("Telegram plugin started.")
        dp.register_message_handler(self.send_welcome)
        await dp.start_polling()

    async def send_welcome(self, message: types.Message):
        pprint.pprint(list(message))
        await message.reply("It works!")
