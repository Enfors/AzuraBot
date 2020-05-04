"""Dialogflow-based weather webhook.
"""

import calendar
import configparser
import datetime
import os

from typing import List

import aiohttp
from aiohttp import web
import dateutil.parser

from azurabot.bot import AzuraBotError
from azurabot.backends.webhook import Webhook

routes = web.RouteTableDef()


@routes.post("/df-weather")
async def weather(request):
    # return web.Response(text="Weather not implemented yet.")

    response = {
        "fulfillmentText": ("How the hell should I know? "
                            "Do I look like John Polman to you?")
    }

    req = await request.json()

    location = req["queryResult"]["parameters"]["geo-city"]
    date = req["queryResult"]["parameters"]["date"]
    if date:
        date = dateutil.parser.parse(date)
    else:
        date = datetime.datetime.today()

    weekday = calendar.day_name[date.weekday()]

    report = f"Weather report for {location}, {weekday}: \n"

    forecast = WeatherForecast()

    items = await forecast.get_items(location)
    items = await forecast.filter_to_date(items, date)
    items = await forecast.filter_out_night_items(items)

    # days = await forecast.group_items_into_days(items)

    # for day in days:
    #    report += await forecast.make_day_report(day)

    if items:
        report += await forecast.make_day_report(items)
    else:
        report = "Unfortunately, the forecast only stretches five days " \
            "into the future."

    response = {
        "fulfillmentText": report
    }

    print(report)
    return web.json_response(response)


class Plugin(Webhook):
    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "Dialogflow weather"):
        super().__init__(bot, config, name)

    async def run(self):
        await self.start_serving(routes, cert_file_name="secret/cert1.pem",
                                 privkey_file_name="secret/privkey1.pem")


class WeatherForecast:

    base_url = "https://api.openweathermap.org/data/2.5/"

    def __init__(self):
        self.config = configparser.ConfigParser()
        if not os.path.isfile("etc/azurabot.conf"):
            raise AzuraBotError("Config file etc/azurabot.conf not found")
        self.config.read("etc/azurabot.conf")

        self.api_key = self.config["weather"]["api_key"]
        if not self.api_key:
            raise AzuraBotError("There is no 'api_key' under the 'weather' "
                                "heading in the configuration file. "
                                "Therefore, I can't access the Open Weather "
                                "Map service to get a forecast.")
        self.forecast = None

    async def get_items(self, location: str):
        if not self.forecast:
            await self.get_complete_forecast(location)

        for item in self.forecast["list"]:
            item["datetime"] = datetime.datetime.fromtimestamp(int(item["dt"]))

        return self.forecast["list"]

    async def filter_to_date(self, items: List, date: datetime.datetime):
        return [item for item in items if
                item["datetime"].year == date.year and
                item["datetime"].month == date.month and
                item["datetime"].day == date.day]

    async def filter_out_night_items(self, items: List):
        return [item for item in items if
                datetime.datetime.fromtimestamp(int(item["dt"])).hour >= 6 and
                datetime.datetime.fromtimestamp(int(item["dt"])).hour <= 21]

    async def group_items_into_days(self, items: List):
        """
        This functions takes a list of items, and makes it a list of lists.
        Each top-level list represents a day. In other words, it turns

        [ monday_time1, monday_time2, tuesday_time1, tuesday_time2]

        into

        [[ monday_time1, monday_time2], [tuesday_time1, tuesday_time2]]
        """

        days = []
        day = []
        cur_date = items[0]["datetime"].strftime("%Y-%m-%d")

        for item in items:
            if item["datetime"].strftime("%Y-%m-%d") != cur_date:
                days.append(day.copy())
                day = []
                cur_date = item["datetime"].strftime("%Y-%m-%d")
            day.append(item)

        return days

    async def group_day_into_periods(self, items):
        """
        Like group_items_into_days, except groups a day into morning,
        afternoon, and evening. Also, it creates a dict.
        """

        morning = []
        afternoon = []
        evening = []

        for item in items:
            if item["datetime"].hour <= 11:
                morning.append(item)
            elif item["datetime"].hour <= 16:
                afternoon.append(item)
            else:
                evening.append(item)

        report = {"morning": morning,
                  "afternoon": afternoon,
                  "evening": evening}
        return report

    async def make_day_report(self, day: List):
        report = ""

        day = await self.group_day_into_periods(day)

        for period in ["morning", "afternoon", "evening"]:
            report += await self.make_period_report(day[period], period)

        return report

    async def make_period_report(self, items: List, period: str):
        temps = []
        descs = []

        if not items:
            return ""

        for item in items:
            temps.append(int(0.5 + item["main"]["temp"]))
            desc = item["weather"][0]["description"]
            if desc not in descs:
                descs.append(desc)

        highest = max(temps)
        lowest = min(temps)

        desc = ", then ".join(descs)

        report = f"{period.title()}: {desc} with temperatures "

        if lowest == highest:
            report += f"around {highest} degrees.\n"
        else:
            f"between {lowest} and {highest} degrees.\n"
        return report

    async def get_complete_forecast(self, location: str):
        url = f"{self.base_url}forecast?" \
            f"q={location}&units=metric&appid={self.api_key}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                self.forecast = await resp.json()
