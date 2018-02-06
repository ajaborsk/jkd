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

from .logging import *
from .container import *
from .report_bokeh_offline_html import *

import aiohttp_jinja2
import jinja2
import time

from bokeh.plotting import figure
from bokeh.models import Range1d
from bokeh.embed import components
from bokeh.models import ColumnDataSource

# create some data

cds = ColumnDataSource(data = {
'x1':[0, 1, 2, 3, 4, 5, 6, 7,  8,  9, 10, 9],
'y1':[0, 8, 2, 4, 6, 9, 5, 6, 25, 28,  4, 7]
})


# select the tools we want
TOOLS="pan,wheel_zoom,box_zoom,reset,save"

# the red and blue graphs will share this data range
xr1 = Range1d(start=0, end=15)
yr1 = Range1d(start=0, end=30)

# only the green will use this data range
xr2 = Range1d(start=0, end=30)
yr2 = Range1d(start=0, end=30)

# build our figures
p1 = figure(x_range=xr1, y_range=yr1, tools=TOOLS, plot_width=900, plot_height=600)
p1.scatter('x1', 'y1', size=12, color="red", alpha=0.5, source = cds)

#p2 = figure(x_range=xr1, y_range=yr1, tools=TOOLS, plot_width=900, plot_height=300)
#p2.scatter(x2, y2, size=12, color="blue", alpha=0.5)

#p3 = figure(x_range=xr2, y_range=yr2, tools=TOOLS, plot_width=900, plot_height=300)
#p3.scatter(x3, y3, size=12, color="green", alpha=0.5)

# plots can be a single Bokeh Model, a list/tuple, or even a dictionary
plots = {'Red': p1}
#plots = {'Red': p1, 'Blue': p2, 'Green': p3}

script, div = components(plots)
#print(script)
#print(div)

class Processor(Node):
    def __init__(self, content = None, **kwargs):
        super().__init__(**kwargs)
        self.next_id = 1

    async def process(self, future): # unused
        asyncio.sleep(2)
        return "<html><head></head><body><p>Full one !</p></body></html>"

    def get(self, callback, client, portname = None, format = None):
        time.sleep(1)
        self.env.loop.call_soon(callback, client, """<html>
  <head>
    <meta charset="utf-8">
    <title>Bokeh Scatter Plots</title>

    <link rel="stylesheet" href="http://cdn.pydata.org/bokeh/release/bokeh-0.12.13.min.css" type="text/css" />
    <script type="text/javascript" src="http://cdn.pydata.org/bokeh/release/bokeh-0.12.13.min.js"></script>

    {script}

  </head>
  <body>
    <p>Paragraph Test</p>
    {red}
  </body>
</html>
""".format(script=script, red=div['Red']))


class HtmlReport(Node):

    def __init__(self, content = None, processor = None, **kwargs):
        super().__init__(**kwargs)
        self.processor = processor

    def get_cb(self, future, result):
        # callback for the callback based interface
        return future.set_result(result)

    async def aget(self, portname = None, format = None):
        # create a future to "manage" the callback based interface
        future = self.env.loop.create_future()
        # call a callback based interface
        self.processor.get(self.get_cb, future)
        # await for the future to be completed (by the callback)
        await asyncio.wait_for(future, None)
        # return the future result
        return future.result()


# The Web server part (to be put in a separate module)

#import pyodbc

application = HtmlReport()

class Subprocessus(Node):
    def __init__(self, content=None):
        super().__init__(content)

    def launch(self):
        pass

    async def aget_status(self):
        pass

    async def aget(self):
        pass


async def continuous_task(c):
    while True:
        await asyncio.sleep(1)
        c.count += 1


class Environment(Container):

    def __init__(self):
        super().__init__(env=self)
        self.web_app = web.Application()

        self.loop = self.web_app.loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self.web_app.router.add_get('/', self.handle)
        self.web_app.router.add_get('/{app}', self.handle)
        self.web_app.router.add_get('/{app}/{address:[^{}$]+}', self.handle)

#        self.processor = Processor(env = self)
#        self.test_application = HtmlReport(env = self, processor = self.processor)
        self.test_application = BokehOfflineReportHtml(env = self)
        self.count = 1
        self.task = self.loop.create_task(continuous_task(self))


    async def handle(self, request):
        name = request.match_info.get('app', "Anonymous")

        if name == "Anonymous":
            text = "<html><body><p>Count = {}</p></body></html>".format(self.count)

            #text = await self.test_application.aget()
        else:
            logger.debug("application :{:s} // address: {:s}".format(name, request.match_info.get('address', "")))
            self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", "testapp", loop=self.loop, stdout=asyncio.subprocess.PIPE)
            line = b' '
            text = ''
            while line != b'':
                line = await self.subprocess.stdout.readline()
                print('line=', line)
                text += line.decode('ascii')
            await self.subprocess.wait()
            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

        #text = "Hello, " + name
        return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    def http_serve(self):
        logger.info("serving...")
        web.run_app(self.web_app)
