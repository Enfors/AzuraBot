"""
An IRC interface plugin for AzuraBot.
"""

import asyncio

import botymcbotface.async_irc

import azurabot

from azurabot.interface.asyncinterface import AsyncInterface


class Plugin(AsyncInterface):

    async def run(self):
        """This starts the plugin.
        """
        self.log("IRC plugin started.")
        await self._init_irc()
        asyncio.create_task(self._receive_loop())
        asyncio.create_task(self._send_loop())

    async def _init_irc(self):
        self.server = self.config["irc"]["server"]
        self.nickname = self.config["irc"]["nickname"]
        self.password = self.config["irc"]["password"]
        debug_level = self.config.getint("irc", "debug_level",
                                         fallback=0)
        self.main_channel = "#" + self.config.get("irc", "main_channel",
                                                  fallback="AzuraBot")

        self.irc_bot = botymcbotface.async_irc.IRCBot(self.nickname,
                                                      self.password,
                                                      debug_level=debug_level,
                                                      version="0.0.1")

        await self.irc_bot.connect(self.server, self.main_channel)

    async def _receive_loop(self):
        """This is the loop that receives messages for AzuraBot, that is,
        messages sent TO AzuraBot from the IRC server. It should NOT
        respond directly to messages it receives, instead it should
        forward them all to AzuraBot proper, to let it figure out what
        to do with them.

        """
        while True:
            irc_msg = await self.irc_bot.get_msg(5)

            if not irc_msg:
                continue

            user = azurabot.user.User(self.bot,
                                      identifiers={"irc": irc_msg.sender})

            if irc_msg.msg_type == "PRIVMSG" and \
               irc_msg.channel == self.nickname:
                self.log(f"Private message: {irc_msg.sender}->"
                         f"{irc_msg.channel}: {irc_msg.msg_text}")
                await self.send_user_text_to_bot(user, irc_msg.msg_text)

            if irc_msg.msg_type == "PRIVMSG" and \
               irc_msg.channel != self.nickname:
                self.log(f"Channel message: "
                         f"{irc_msg.sender} @ {irc_msg.channel}: "
                         f"{irc_msg.msg_text}")

    async def _send_loop(self):
        """This is the loop that sends messages from AzuraBot, that is,
        it gets messages from AzuraBot to send to the IRC server.
        """
        keep_running = True

        while keep_running:
            msg = await self.inbox.get()
            user = msg.user
            await self.irc_bot.privmsg(user.identifiers["irc"], msg.text)
