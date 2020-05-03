import logging

import asyncio
import configparser

# from aiogram import Bot, Dispatcher, executor, types
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from azurabot.interface.asyncinterface import AsyncInterface

config = configparser.ConfigParser()
config.read("etc/azurabot.conf")
token = config["telegram"]["api_key"]
print("Token:", token)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot)


class Plugin(AsyncInterface):

    async def run(self):
        # self.log("Telegram plugin started.")
        # test_task = asyncio.create_task(self._telegram_test())
        # asyncio.gather(test_task)
        executor.start_polling(dp, loop=asyncio.get_running_loop(),
                               skip_updates=True)

    @dp.message_handler(commands=["start", "help"])
    async def send_welcome(message: types.Message):
        await message.reply("It works!")
