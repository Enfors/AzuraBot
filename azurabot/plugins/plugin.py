"""
The base Plugin class file.

All other plugins inherit this class, directly or indirectly.
"""

import configparser


class Plugin:

    def __init__(self, bot, config: configparser.ConfigParser,
                 name="(unnamed plugin)"):
        self.bot = bot
        self.config = config
        self.name = name

    async def start(self):
        """
        When a plugin is loaded by the bot, the bot calls its
        start() function. That function is then responsible for
        calling the object's run() function.

        This is done by AsyncInterface's and ThreadedInterface's
        start() function, which typically should not be overridden.
        """
        self.bot.log_debug(self.name,
                           "This plugin doesn't have its own start() "
                           "function.")

    async def run(self):
        """
        Called by the plugin's start() function. Ordinary plugins
        should put their code here.
        """
        self.bot.log_warn(self.name,
                          "This plugin doesn't have its own run() function.")

    def log(self, msg):
        self.bot.log_warn(self.name, "Using deprecated azurabot.plugin.log "
                          "function for following message:")
        self.bot.log_info(self.name, msg)
