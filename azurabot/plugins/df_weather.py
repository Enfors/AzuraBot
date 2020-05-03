"""Dialogflow-based weather webhook.
"""

import configparser

from aiohttp import web

from azurabot.backends.webhook import Webhook

routes = web.RouteTableDef()


@routes.post("/df-weather")
async def weather(request):
    # return web.Response(text="Weather not implemented yet.")

    response = {
        "fulfillmentText": ("How the hell should I know? "
                            "Do I look like John Polman to you?")
        }

    return web.json_response(response)


class Plugin(Webhook):
    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "Dialogflow weather"):
        super().__init__(bot, config, name)

    async def run(self):
        await self.start_serving(routes, cert_file_name="secret/cert1.pem",
                                 privkey_file_name="secret/privkey1.pem")
