#!/usr/bin/env python3

import configparser
import logging

from aiogram import Bot, Dispatcher, executor, types

config = configparser.ConfigParser()
config.read("../etc/azurabot.conf")
API_TOKEN = config["telegram"]["api_key"]

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=["start", "help"])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends "/start" or "/help".
    """

    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
