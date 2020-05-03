"""Dialogflow-based weather webhook.
"""

import configparser

from aiohttp import web

from azurabot.backends.webhook import Webhook

routes = web.RouteTableDef()


@routes.get("/df-weather")
async def weather(request):
    return web.Response(text="Weather not implemented yet.")


class Plugin(Webhook):
    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "Dialogflow weather"):
        super().__init__(bot, config, name)

    async def run(self):
        await self.start_serving(routes)
