#!/usr/bin/env python3

import asyncio
import configparser
import importlib
import os

import motor.motor_asyncio

import azurabot.user
import azurabot.msg

from azurabot.intent import Intent
from azurabot.msg import Msg
from azurabot.user import User

"""
AzuraBot's most important file.
"""

LOG_LEVEL_CRIT = 2
LOG_LEVEL_ERR = 3
LOG_LEVEL_WARN = 4
LOG_LEVEL_NOTICE = 5
LOG_LEVEL_INFO = 6
LOG_LEVEL_DEBUG = 7

log_level_words = {
    2: "Critical",
    3: "Error",
    4: "Warning",
    5: "Notice",
    6: "Info",
    7: "Debug"
}

address_split_char = "#"


class Bot:
    """
    The bot itself. When you make a bot, it should inherit this class.
    """

    def __init__(self):
        self.config = configparser.ConfigParser()
        if not os.path.isfile("etc/azurabot.conf"):
            raise AzuraBotError("Config file etc/azurabot.conf not found")
        self.config.read("etc/azurabot.conf")
        main_config = self.config["main"]
        self.log_level = main_config.getint("log_level", LOG_LEVEL_NOTICE)

        self.plugins = []
        self.plugin_inboxes = {}

        self.intents = {}

        self.online_users = {}

    async def run(self):
        # user = azurabot.user.User("Enfors")
        # msg = azurabot.msg.Msg(azurabot.msg.FROM_USER, user, "foo")
        # print(user)
        # print(msg)
        self.bot_inbox = asyncio.Queue()

        # Initialize MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient()
        self.db = client["AzuraBotDB"]

        #
        # Step 1: Load all plugins
        #
        await self._load_all_plugins()

        #
        # Step 2: Start all plugins
        #
        self.log_notice("bot", "AzuraBot running.")
        await self._start_all_plugins()

        #
        # Step 3: Start all background tasks
        #
        self.log_notice("bot", "AzuraBot running.")
        await self._start_cron_task()

        #
        # Step 4: Enter main loop
        #
        self.log_notice("bot", "AzuraBot running.")
        await self._main_loop()

    #
    # Public functions
    #

    async def send(self, msg: Msg, address: str):
        """This is a low level function for sending a Msg to an address.
        Most other sending functions route the message through this function.
        """
        ident, interface = address.split(address_split_char)

        try:
            inbox = self.plugin_inboxes[interface]
        except AttributeError:
            raise AzuraBotError(f"There is no inbox registered for "
                                f"'{interface} (address {address})")

        self.log("bot", "Private message: AzuraBot->{address}: {msg.text}",
                 LOG_LEVEL_INFO)
        await inbox.put(msg)

    async def send_to_user(self, user: User, msg: Msg, address: str = None):
        """This is a higher level function that send(). It sends a Msg to the
        specified user. If no address is specified, then the user's last used
        address (user.current_address) is used.
        """
        if address is None:
            address = user.current_address

        await self.send(msg, address)

    async def send_text_to_user(self, user: User, text: str,
                                address: str = None):
        msg = Msg(direction=azurabot.msg.FROM_BOT,
                  user=user,
                  reply_to=self.bot_inbox,  # Is this right?
                  text=text)

        await self.send_to_user(user, msg, address)

    async def reply(self, old_msg: Msg, text: str):
        """Given a previous message old_msg, this function replies to it with
        the text in the text argument.

        """
        if old_msg.direction == azurabot.msg.TO_BOT:
            direction = azurabot.msg.FROM_BOT
        else:
            direction = azurabot.msg.TO_BOT

        reply_msg = Msg(direction=direction,
                        user=old_msg.user,
                        reply_to=old_msg.reply_to,
                        text=text)
        await old_msg.put(reply_msg)

    #
    # Public logging functions
    #
    # There are several public logging functions:
    #
    # - log(self, section: str, text: str, level: int)
    #   This is the main logging function. The others are convenience
    #   functions, which are ultimately routed through this one.
    #
    # - log_crit(self, section: str, text: str)
    # - log_err(self, section: str, text: str)
    # - log_warn(self, section: str, text: str)
    # - log_notice(self, section: str, text: str)
    # - log_info(self, section: str, text: str)
    # - log_debug(self, section: str, text: str)
    #
    # The main logging function ("log"), will probably log using the
    # standard python logging module. So why have my own functions?
    # The reason is that then I can add the "section" argument, which
    # will make it possible to have different log levels for different
    # sections. For example, I might want debugging information to be
    # logged from the telegram module, but not from everything else.

    def log(self, section: str, text: str, level: int):
        # print(f"Section: {section}")
        # print(f"Level  : {level} ({self.log_level})")
        # print(f"Text   : {text}")

        if level > self.log_level:
            return

        print(f"[{section}:{log_level_words[level]}] {text}")

    def log_crit(self, section: str, text: str):
        self.log(section, text, LOG_LEVEL_CRIT)

    def log_err(self, section: str, text: str):
        self.log(section, text, LOG_LEVEL_ERR)

    def log_warn(self, section: str, text: str):
        self.log(section, text, LOG_LEVEL_WARN)

    def log_notice(self, section: str, text: str):
        self.log(section, text, LOG_LEVEL_NOTICE)

    def log_info(self, section: str, text: str):
        self.log(section, text, LOG_LEVEL_INFO)

    def log_debug(self, section: str, text: str):
        self.log(section, text, LOG_LEVEL_DEBUG)

    #
    # Private functions
    #

    async def _load_all_plugins(self):
        """
        Load all plugins.
        """
        plugins_dir = self.config["plugins"]["dir"]
        plugins_str = self.config["plugins"]["plugins"].replace("\r", "")
        file_names = [file_name for file_name in plugins_str.split("\n")
                      if len(file_name)]
        for file_name in file_names:
            full_path = "%s.%s" % (plugins_dir, file_name)
            plugin = self._load_plugin(full_path)

            if plugin:
                self.plugins.append(plugin)

    def _load_plugin(self, file_name):
        """
        Load a single plugin. Return True on success.
        """
        if file_name.endswith(".py"):
            file_name = file_name[:-3]

        base_name = file_name.split(".")[-1]

        self.log("bot", f"Loading plugin {base_name}", LOG_LEVEL_INFO)

        try:
            plugin_file = importlib.import_module(file_name)
        except ModuleNotFoundError:
            self.log("bot", "Plugin not found:" + file_name.replace(".", "/")
                     + ".py", LOG_LEVEL_ERR)
            raise
        plugin = plugin_file.Plugin(bot=self,
                                    config=self.config,
                                    name=base_name)

        try:
            self.plugin_inboxes[base_name] = plugin.inbox
        except AttributeError:
            # This plugin has no inbox; that's fine. It's obviously not
            # an interface plugin.
            pass

        return plugin

    async def _main_loop(self):
        keep_running = True

        while keep_running:
            pass
            msg = await self.bot_inbox.get()
            text = msg.text
            self.log_info("bot", "Received text: '%s'" % text)

            # The reason why we start a task here, is because in the
            # future, the functio _handle_inc_msg() might be slow -
            # perhaps it has to load users from a slow database, or
            # something.

            asyncio.create_task(self._handle_inc_msg(msg))

            # if text == "Hello, bot!":
            #     print("[bot] Replying...")
            #     await msg.reply("Hello yourself!", self.bot_inbox)
            # else:
            #     print("[bot] Replying again...")
            #     await msg.reply("Your message has been received.",
            #                     self.bot_inbox)
            #     keep_running = False

    async def _start_all_plugins(self):

        start_tasks = []

        for plugin in self.plugins:
            self.log_info("bot", f"Starting plugin {plugin.name}...")
            start_tasks.append(asyncio.create_task(plugin.start()))

            try:
                plugin_intents = plugin.intents

                await self._add_intents(plugin_intents)
            except AttributeError:
                pass

        await asyncio.gather(*start_tasks)

    async def _add_intents(self, intents: list):
        for intent in intents:
            await self._add_intent(intent)

    async def _add_intent(self, intent: Intent):
        if intent.name in self.intents:
            existing_intent = self.intents[intent.name]
            self.log_warn("bot", f"[bot] Intent conflict: {intent.name} "
                          f"exists in both {intent.intent_file} and "
                          f"{existing_intent.intent_file}. "
                          f"Using the one in {existing_intent.intent_file}.")
            return False

        self.log_debug("bot", f" - Adding intent {intent.name}.")
        self.intents[intent.name.lower()] = intent

    async def _start_cron_task(self):
        """This function starts the background timer task. For example, if
        users want a weather report at a certain time each day, it
        will be handled by the background timer.

        """
        pass

    async def _handle_inc_msg(self, msg: azurabot.msg.Msg):

        user = await self._identify_msg_user(msg)

        if user.current_address not in self.online_users:
            user = await self._login_user(user)
            user.loop_task = asyncio.create_task(self._user_loop(user))
            # asyncio.gather(user.loop_task) # todo: Maybe shouldn't be here
        else:
            user = self.online_users[user.current_address]

        # print(f"Putting message in user box {user.inbox!r}")
        await user.inbox.put(msg)

    async def _login_user(self, user):
        self.online_users[user.current_address] = user

        # See if this user exists in the collection
        document = await self.db.users.find_one({"name": user.name})

        # If user exists, load it
        if document:
            await self._load_user(user)
        else:
            # If user doesn't exist, save it
            await self._save_user(user)

        await self._save_user(user)
        return user

    async def _load_user(self, user):
        document = await self.db.users.find_one({"name": user.name})
        user.uid = document["uid"]
        user.identifiers = document["identifiers"]

        self.log_debug("bot", f"- User loaded: {user.name}:{user.uid} - "
                       f"{user.identifiers}")
        return user

    async def _save_user(self, user):
        if not user.uid:
            user.uid = await self._get_next_uid()

        # Create a document for this user
        document = {"name": user.name,
                    "uid": user.uid,
                    "identifiers": user.identifiers}

        old_doc = await self.db.users.find_one({"name": user.name})

        # If the user already exists...
        if old_doc:
            # ... then replace it...
            await self.db.users.replace_one({"name": user.name},
                                            document)
        else:
            # ... otherwise, insert the user document into the database
            await self.db.users.insert_one(document)

    async def _get_next_uid(self):
        next_uid = 1
        # I think "-uid" works for sorting, but not 100% positive.
        cursor = self.db.users.find({"uid": {"$gt": 0}}).sort("-uid")

        for document in await cursor.to_list(length=10):
            uid = int(document["uid"])
            if uid >= next_uid:
                next_uid = uid + 1

        return next_uid

    async def _user_loop(self, user: azurabot.user.User):
        keep_running = True
        # out_msgs = []

        self.log_debug("bot", f"User loop started for {user.current_address}")

        while keep_running:
            # print(f"[bot] Awaiting messages from user box {user.inbox!r}")
            msg = await user.inbox.get()
            # print("[bot] Filtering")
            msg = await self._filter_inc_msg(msg)
            # print("[bot] Selecting intent")
            intent = await self._select_intent(msg)
            # print("[bot] Checking intent")
            if intent:
                await self._run_intent(user, intent, msg)
                self.log_debug("bot", "Intent completed.")
            else:
                self.log_debug("bot" "Intent failed.")
                await msg.reply("I'm sorry, but I don't understand.",
                                self.bot_inbox)

    async def _identify_msg_user(self, msg: azurabot.msg.Msg):
        user = msg.user
        await user.identify()
        self.log_debug("bot", f"User identified: {user}")
        return user

    async def _filter_inc_msg(self, msg: azurabot.msg.Msg):
        return msg

    async def _select_intent(self, msg: azurabot.msg.Msg):
        text = msg.text
        intent_name = text.split(" ")[0]
        try:
            intent = self.intents[intent_name.lower()](self)
            self.log_debug("bot", f"Intent: \"{intent_name}\"")
            return intent
        except KeyError:
            self.log_debug("bot", f"No intent found for \"{intent_name}\"")
            return None

    async def _run_intent(self, user: User, intent: Intent,
                          msg: azurabot.msg.Msg):
        await intent.do(user, msg)


class AzuraBotError(Exception):
    pass


if __name__ == "__main__":
    bot = Bot()
    asyncio.run(bot.run())
