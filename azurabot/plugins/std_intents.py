"""
This file contains a set of standard intents, which should always be included.
"""

import azurabot
from azurabot.intent import Intent
from azurabot.msg import Msg


class HelloIntent(Intent):
    name = "Hello"

    def __init__(self, bot: azurabot.bot.Bot):
        super().__init__(bot)
        self.intent_file = __file__

    async def do(self, user: azurabot.user.User, msg: Msg):
        await msg.reply(f"Hello {user.name}!", user.inbox)


class VersionIntent(Intent):
    name = "Version"

    def __init__(self, bot: azurabot.bot.Bot):
        super().__init__(bot)
        self.intent_file = __file__

    async def do(self, user: azurabot.user.User, msg: Msg):
        await msg.reply("Version command not implemented yet.", user.inbox)


class StatusIntent(Intent):
    name = "Status"

    def __init__(self, bot: azurabot.bot.Bot):
        super().__init__(bot)
        self.intent_file = __file__

    async def do(self, user: azurabot.user.User, msg: Msg):
        await msg.reply("Ready.", user.inbox)


class NameIntent(Intent):
    name = "Name"

    def __init__(self, bot: azurabot.bot.Bot):
        super().__init__(bot)
        self.intent_file = __file__

    async def do(self, user: azurabot.user.User, msg: Msg):
        name = await user.ask("What is your name?")
        if len(name):
            user.name = name
            await user.tell(f"Hello {user.name}, nice to meet you.")


class Plugin(azurabot.plugins.plugin.Plugin):
    name = "std_intents"
    # By setting "intents", we signal to the bot that there are intents
    # to use here.
    intents = [HelloIntent, VersionIntent, StatusIntent, NameIntent]

    async def run(self):
        pass
