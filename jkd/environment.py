# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:48:33 2018

"""
import sys
import asyncio

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    
from aiohttp import web

from .container import *

import aiohttp_jinja2
import jinja2
import time

class Processor(Node):
    def __init__(self, content = None, **kwargs):
        super().__init__(**kwargs)
        self.next_id = 1

    async def process(self, future): # unused
        asyncio.sleep(2)
        return "<html><head></head><body><p>Full one !</p></body></html>"

    def get(self, callback, client):
        time.sleep(1)
        self.env.loop.call_soon(callback, client, "Process Result")


class HtmlReport(Node):

    def __init__(self, content = None, processor = None, **kwargs):
        super().__init__(**kwargs)
        self.processor = processor

    def get_cb(self, future, result):
        # callback for the callback based interface
        return future.set_result(result)

    async def aget(self):
        # create a future to "manage" the callback based interface
        future = self.env.loop.create_future()

        # call a callback based interface
        self.processor.get(self.get_cb, future)
        # await for the future to be completed (by the callback)
        await asyncio.wait_for(future, None)
        # return the future result
        return future.result()

# The Web server part (to be put in a separate module)

application = HtmlReport()

class Environment(Container):

    def __init__(self):
        super().__init__(env=self)
        self.web_app = web.Application()

        self.loop = self.web_app.loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self.web_app.router.add_get('/', self.handle)
        self.web_app.router.add_get('/{app}', self.handle)

        self.processor = Processor(env = self)
        self.test_application = HtmlReport(env = self, processor = self.processor)

    async def handle(self, request):
        name = request.match_info.get('app', "Anonymous")

        if name == "Anonymous":
            text = await self.test_application.aget()
        else:
            self.subprocess = await asyncio.create_subprocess_exec("Python", "-m", "jkd", "slave", "testapp", loop=self.loop, stdout=asyncio.subprocess.PIPE)
            line = b' '
            text = ''
            while line != b'':
                line = await self.subprocess.stdout.readline()
                print('line=', line)
                text += line.decode('ascii')
            await self.subprocess.wait()
            return web.Response(body=text)

        #text = "Hello, " + name
        return web.Response(body=text)

    def http_serve(self):
        print("serving...")
        web.run_app(self.web_app)
