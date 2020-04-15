"""
The weather plugin for AzuraBot.
"""

import aiohttp
import datetime
# import pprint
# import sys

import azurabot
from azurabot.intent import Intent
from azurabot.msg import Msg
from azurabot.user import User


class WeatherIntent(Intent):
    name = "Weather"

    base_url = "https://api.openweathermap.org/data/2.5/"

    def __init__(self, bot: azurabot.bot.Bot):
        super().__init__(bot)
        self.intent_file = __file__
        self.api_key = bot.config["weather"]["api_key"]

    async def do(self, user: User, msg: Msg):
        args = [words for words in msg.text.split(" ")[1:]]

        if len(args) < 1:
            location = await user.ask("For what location would you like "
                                      "a weather report?")
        else:
            location = args[0]

        report = await self.get_report(location)

        if report["cod"] != "200":
            await user.tell(f"Weather API call failed with error code "
                            f"{report['cod']}: {report['message']}")
            return

        messages = self.format_report(report)

        if len(messages) == 0:
            await user.tell("Unfortunately, I couldn't produce a "
                            "weather forecast right now.")
            return

        await user.tell(f"Weather forecast for {location.title()}:")

        for message in messages:
            await user.tell(message)

    async def get_report(self, location: str):
        url = f"{self.base_url}forecast?" \
            f"q={location}&units=metric&appid={self.api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()

    def format_report(self, report: dict):
        num_messages = len(report["list"])
        if num_messages > 8:
            num_messages = 8

        messages = []
        for item in report["list"][:num_messages]:
            messages.append(self.format_item(item, int(item["dt"])))
        # item = report["list"][0]
        # message = self.format_item(item, int(item["dt"]))

        return messages

    def format_item(self, data, timestamp):
        disp = ""

        disp += datetime.datetime.fromtimestamp(timestamp).\
            strftime("%Y-%m-%d %H:%M: ")
        disp += f"{data['weather'][0]['description'].capitalize()}, "
        disp += f"{int(data['main']['temp'])} C, wind "
        wind = data["wind"]
        disp += f"{self.format_direction(wind['deg'])} at "
        disp += f"{int(wind['speed'] + 0.5)} m/s."

        return disp

    def format_direction(self, degrees):
        cardinals = ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"]
        return cardinals[int((degrees + 22.5) / 45)]


class Plugin(azurabot.plugins.plugin.Plugin):
    name = "weather"

    intents = [WeatherIntent]
