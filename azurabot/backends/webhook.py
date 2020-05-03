"""aiohttp-based webhook.
"""

import configparser

from aiohttp import web
import ssl

from azurabot.backends.backend import Backend
from azurabot.bot import AzuraBotError


class Webhook(Backend):

    def __init__(self, bot, config: configparser.ConfigParser,
                 name: str = "(unnamed webhook plugin)"):
        super().__init__(bot, config, name)

    async def start_serving(self, routes, port=8080, cert_file_name=None,
                            privkey_file_name=None):
        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()

        # Attempt to setup / use SSL, if cert and key files are available
        if cert_file_name and privkey_file_name:
            try:
                ssl_context = \
                    ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(cert_file_name,
                                            keyfile=privkey_file_name)
            except FileNotFoundError:
                raise AzuraBotError(f"Could not find both cert file "
                                    f"{cert_file_name} and privkey file "
                                    f"{privkey_file_name}")
            # Success - we have loaded both the cert file, and the privkey
            # file. Thus, we run with encryption.
            site = web.TCPSite(runner, "0.0.0.0", port,
                               ssl_context=ssl_context)
        else:
            # No cert file and privkey file was provided, so we run without
            # encryption.
            site = web.TCPSite(runner, "0.0.0.0", port)

        await site.start()
