import logging

from .node import *


class Container(Node):
    def __init__(self):
        super().__init(self)

class Data:
    pass

class DatabaseManager(Node):
    pass

class DataTable(Data):
    pass

class DataBase(Data):
    pass

class Cache(Node):
    pass

class Processor(Node):
    def __init__(self):
        pass
    async def process(self):
        pass
    async def get_results(self):
        pass

# HTML report

import aiohttp_jinja2
import jinja2

class HtmlReport(Node):
    async def get(self):
        return "<html><head></head><body><p>Full one !</p></body></html>"

# The Web server part (to be put in a separate module)

application = HtmlReport()

from aiohttp import web

async def handle(request):
    name = request.match_info.get('name', "Anonymous")

    text = await application.get()

    #text = "Hello, " + name
    return web.Response(body=text)

def serve():
    print("serving...")
    app = web.Application()
    app.router.add_get('/', handle)
    app.router.add_get('/{name}', handle)
    web.run_app(app)
