"""
The Interface class file.

You won't normally use this directly, but rather one of its
decendants interface.async or interface.threaded.
"""

import asyncio
import configparser

import azurabot
from azurabot.msg import Msg
from azurabot.user import User


class Interface(azurabot.plugins.plugin.Plugin):
    """
    Represents an interface between the bot and an external service,
    such as Slack or IRC. Basically, an interface talks to something
    in the external world, to which users connect.
    """

    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "(unnamed interface plugin)"):
        self.bot = bot
        self.config = config
        self.name = name
        self.inbox = asyncio.Queue()

    async def put_msg(self, msg):
        await self.inbox.put(msg)

    async def get_msg(self):
        return await self.inbox.get()

    async def send_msg_to_bot(self, msg: Msg):
        """
        Send any kind of message to the bot.
        """
        msg.direction = azurabot.msg.TO_BOT
        await self.bot.bot_inbox.put(msg)

    async def send_user_text_to_bot(self, user: User, text: str):
        """
        Send a text message from the user to the bot.
        """
        msg = Msg(direction=azurabot.msg.TO_BOT,
                  user=user,
                  reply_to=self.inbox,
                  text=text)
        await self.send_msg_to_bot(msg)
