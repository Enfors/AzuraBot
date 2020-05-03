"""aiohttp-based webhook.
"""

import configparser

from aiohttp import web

from azurabot.backends.backend import Backend


class Webhook(Backend):

    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "(unnamed webhook plugin)"):
        super().__init__(bot, config, name)

    async def start_serving(self, routes, port=8080):
        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
