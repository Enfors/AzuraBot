"""
The Backends class file.

This serves as a parent class for other backend classes.
"""

import asyncio
import configparser

import azurabot


class Backend(azurabot.plugins.plugin.Plugin):
    """
    Represents a backend for AzuraBot. A backend can work in one of two ways:

    First case
    ----------

    For example, take AzuraBot's Dialogflow support. In that case, much of
    AzuraBot's code isn't used; AzuraBot doesn't analyze user input to select
    intents, etc. All that is done in Dialogflow. Dialogflow then just needs
    to call a backend (a REST-like service) which executes the intent which
    Dialogflow has selected. An AzuraBot backend can be such an interface,
    running as a plugin inside AzuraBot:

    Dialogflow
      ^
      |
    +-|-- A Z U R A B O T ---+
    | |                      |
    | v                      |
    | Backend class          |
    |                        |
    +------------------------+

    As stated above, this approach doesn't use a lot of AzuraBot's code,
    AzuraBot is then mainly used as a "container" and infrastructure for a
    webhook or similar, to provide configuration handling, logging, etc.

    Second case
    -----------

    In the second case, AzuraBot is used in a more traditional way. The user
    communicates with AzuraBot through one of AzuraBot's interface classes,
    AzuraBot selects the intent, and then uses a backend (which inherits from
    the Backend class in this file) to execute something.

    User using IRC
      ^
      |
    +-|-- A Z U R A B O T ---+
    | |                      |
    | v                      |
    | IRC Interface class    |
    | ^                      |
    | |                      |
    | v                      |
    | Main Bot class         |
    | ^                      |
    | `-> Backend            |
    |                        |
    +------------------------+
    """

    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "(unnamed backend plugin)"):
        self.bot = bot
        self.config = config
        self.name = name
        self.inbox = asyncio.Queue()

    async def start(self):
        await self.run()

    async def put_msg(self, msg):
        await self.inbox.put(msg)

    async def get_msg(self, msg):
        await self.inbox.get()
