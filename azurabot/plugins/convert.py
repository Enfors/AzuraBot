"""
This file contains some simple intents for converting between formats.
"""

import azurabot
from azurabot.intent import Intent
from azurabot.msg import Msg
from azurabot.user import User


class ConvertIntent(Intent):
    name = "Convert"

    def __init__(self, bot: azurabot.bot.Bot):
        super().__init__(bot)
        self.intent_file = __file__

    async def do(self, user: User, msg: Msg):
        args = [words for words in msg.text.split(" ")[1:]]

        if len(args) == 1:
            to_convert = args[0]
        else:
            to_convert = await user.ask("What do you want to convert?")

        f = float(to_convert)
        c = (f - 32) * 5/9

        await user.tell(f"{to_convert}F is {c:.1f}C.")


class Plugin(azurabot.plugins.plugin.Plugin):
    name = "convert"

    intents = [ConvertIntent]
