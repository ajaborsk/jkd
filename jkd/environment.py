# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:48:33 2018

"""
import sys
#import json
import asyncio

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

#from aiohttp import web
#import aiohttp

from .logging import *
from .container import Container
from .report_bokeh_offline_html import *

import aiohttp_jinja2
import jinja2
import time


from .html_page import HtmlPage
from .subprocessus import Subprocessus
from .signal_generator import SignalGenerator
registry = {
        "html_page":HtmlPage,
        "subprocessus":Subprocessus,
        "signal_generator":SignalGenerator,
         }


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


#application = HtmlReport()


class Environment(Container):

    def __init__(self):
        self.loggers = {'main':logger_main, "msg":logger_msg}
        super().__init__(env=self)
        self.loop = asyncio.get_event_loop()
        # Manually launch mainloop since self.loop was not initialized on Node class initialization
        self.loop_task = self.env.loop.create_task(self.mainloop())
        self.registry = registry


    def run(self):
        # default
        self.loop.run_forever()


import time

from .serialize import *

class EnvSubApplication(Environment):
    def __init__(self, root_name, tree = None, **kwargs):
        self.root_name = '/'.join(root_name.split('/')[:-1])
        super().__init__(**kwargs)
        self.done = False
        self.pipe_channels = {}

        self.root = Container(env = self, parent = self, name = root_name.split('/')[-1], elt = tree, **kwargs)
        if tree is not None:
            # Construct the sub-application tree
            self.debug("tree appname = " + str(tree.attrib['appname']))
            for elt in tree:
                self.debug("  subnode " + str(elt.tag))

        # Launch the reading/handle mainloop task
        self.reader_t = self.loop.create_task(self.msg_pipe_loop())
        self.debug("subapplication initialized")

    def fqn(self):
        return self.root_name

    def msg_pipe_send(self, msg):
        #self.debug("SubApplication {}: Sending message : {}".format(self.root_name, str(msg)), 'msg')
        line = jkd_serialize(msg) + b'\n'
        #self.debug("SubApplication {}s: Serialized message : {}".format(self.appname, line))
        # To be sure to write binary data to stdout, use .buffer.raw
        sys.stdout.buffer.raw.write(line)
        #self.debug("SubApplication {}s: message sent".format(self.appname))

    async def msg_handle(self, msg):
        #self.debug("Handling queue message: {}".format(str(msg)), 'msg')
        if 'query' in msg:
            pass
        elif 'reply' in msg:
            pipe_lcid = self.channels[msg['lcid']]['lcid']
            msg['lcid'] = pipe_lcid
            del msg['prx_src'] # not serializable entry
            self.msg_pipe_send(msg)

    async def msg_pipe_handle(self, msg):
        self.debug("Handling pipe message: {}".format(str(msg)), 'msg')
        if 'query' in msg:
            self.debug(" Query message", 'msg')
            lcid = self.next_lcid
            self.next_lcid += 1
            # queue lcid       ...        pipe lcid
            self.channels[lcid] = {'lcid':msg['lcid']}
            msg['lcid'] = lcid
            msg['prx_src'] = self
            await self.msg_send(self.root, msg)
        elif 'cmd' in msg:
            self.debug(" Cmd (query update) message", "msg")
        else:
            self.warning('Unhandled message: ' + str(msg), 'msg')
        # if 'cmd' in msg and msg['cmd'] == 'get':
            # lcid = msg['lcid']
            # self.reply = {'reply':'This is the reply from the subprocess application.'}
            # self.send(self.reply)
            # # a fully synchronous code part...
            # parts = 10
            # for i in range(parts):
                # self.send({"lcid":lcid, "ratio":i / parts})
                # time.sleep(0.05)
            # for i in range(parts):
                # self.send({"lcid":lcid, "part": i, "parts": parts})
                # time.sleep(0.05)
        # elif 'cmd' in msg and msg['cmd'] == 'exit':
            # self.reply = {'reply':'exited'}
            # self.send(self.reply)
            # self.done = True
            # self.loop.exit()
        # elif 0:
            # self.debug('data query requested', 'msg')
            # lcid = msg['lcid']
            # self.reply = {'lcid':lcid, 'reply':'This is the data reply from the subprocess application.'}
            # self.pipe_send(self.reply)
        # else:
            # self.warning('Unhandled message: '+str(msg), 'msg')

    async def msg_pipe_loop(self):
        # The mainloop
        while not self.done:
            #self.debug("SubApplication {}: Waiting...".format(self.root_name), 'msg')
            line = await self.loop.run_in_executor(None, sys.stdin.readline)
            msg = jkd_deserialize(line[:-1])
            await self.msg_pipe_handle(msg)


from .http_server import *

class EnvHttpServer(Environment):
    def __init__(self):
        super().__init__()
        self.http_server = HttpServer(env = self, parent = self, name = 'httpd')
        self.name = ''

        self.loop = self.http_server.web_app.loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

    def run(self):
        self.info("Launching http server node...")
        self.http_server.run()
