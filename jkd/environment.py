# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:48:33 2018

"""

from aiohttp import web

from .container import *

import aiohttp_jinja2
import jinja2

class HtmlReport(Node):
    async def get(self):
        return "<html><head></head><body><p>Full one !</p></body></html>"

# The Web server part (to be put in a separate module)

application = HtmlReport()



class Environment(Container):

    async def handle(self, request):
        name = request.match_info.get('name', "Anonymous")

        text = await application.get()

        #text = "Hello, " + name
        return web.Response(body=text)

    def http_serve(self):
        print("serving...")
        app = web.Application()
        app.router.add_get('/', self.handle)
        app.router.add_get('/{name}', self.handle)
        web.run_app(app)
        