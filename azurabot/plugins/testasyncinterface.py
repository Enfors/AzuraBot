"""
A test plugin for the async interface.
"""

import asyncio

import azurabot

from azurabot.interface.asyncinterface import AsyncInterface


class Plugin(AsyncInterface):

    async def run(self):
        self.name = "testasyncinterface"
        self.log("Async plugin started.")
        send_task = asyncio.create_task(self.send_msg("Hello, bot!"))

    async def send_msg(self, text: str):
        await asyncio.sleep(1)

        user = azurabot.user.User(self.bot,
                                  identifiers={"testinterface": "Tester"})

        self.log("Sending...")
        await self.send_user_text_to_bot(user, "Hello, bot!")
        answer = await self.inbox.get()
        self.log(f"Received answer: '{answer.text}'")

        await asyncio.sleep(1)

        self.log("Sending...")
        await self.send_user_text_to_bot(user, "Nice to meet you!")
        answer = await self.inbox.get()
        self.log(f"Received another answer: '{answer.text}'")
