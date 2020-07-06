import logging

import configparser

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
        await dp.start_polling()

    @dp.message_handler(commands=["start", "help"])
    async def send_welcome(message: types.Message):
        await message.reply("It works!")
