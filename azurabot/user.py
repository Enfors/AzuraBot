"""
The user class file.
"""

import asyncio

import azurabot


class User:
    """
    Represents a user who communicates with the bot.

    Since AzuraBot allows users to talk to the bot from several
    services (like Slack, Telegram, etc), it's a bit complicated
    to keep track of them. User A can have one name on Slack, and
    a completely different one on Telegram. Additionally, on some
    services, the name is the user's unique identifier, while on
    others, it is not (for example, on Telegram you have both a
    name and a number).

    Therefore, the name the bot refers to the user as, may or may
    not be the same as the service the user is connecting through
    uses. Additionally, users can be in different states.

    1. The user is now sending their first message to the bot.
       In this case, the user is unidentified. It has some sort
       of identifier (typically a name or a number) from the
       service through which they are connected.
    2. Once the first message from the user arrives at the bot,
       the bot will map the user identifier sent by the user's
       service (Slack, Telegram, etc) to a user in the bot's
       internal database. Then the user becomes identified.

    Because of this, several name-like variables are needed for
    each user:

    - "name" (str) is the name which the bot refers to the user
      as. The user can set this name themself at will.
    - "identifiers" (dict) is a dictionary in which each key is
      the name of a serice (Telegram, Discord, etc) and each
      value is the user identifier provided by that service.
    - Additionally, the "identified" bool tells us whether the
      user has been identified (read: had its service-provided
      identifier successfully mapped against a unique user in
      the bot's user database).
    """

    def __init__(self, bot, identifiers: dict):
        self.bot = bot
        self.name = None
        self.identified = False
        self.identifiers = identifiers
        #self.msgs = list()
        self.inbox = asyncio.Queue()
        self.loop_task = None

        try:
            service = list(identifiers.keys())[0]
            ident = identifiers[service]
            self.current_address = f"{ident}#{service}"
        except:
            self.current_address = f"(unknown)#(unknown)"
            raise

    async def identify(self):
        """
        Attempt to identify a user (read: find them in the bot's
        database) by matching an entry in the user's 'identifiers'
        dict to one in the database.

        If successful:
        - Set 'name' field according to the database
        - Set 'identified' to True
        - Return True
        Else:
        - Return False
        """
        service = list(self.identifiers.keys())[0]
        self.name = self.identifiers[service]
        self.identified = True
        return False

    async def tell(self, text):
        await self.bot.send_text_to_user(self, text)

    async def ask(self, question_text):
        await self.bot.send_text_to_user(self, question_text)
        answer = await self.inbox.get()
        return answer.text

    def __str__(self):
        return f"User: {self.name} [{self.current_address}]"
