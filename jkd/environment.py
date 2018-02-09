# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:48:33 2018

"""
import sys
import json
import asyncio

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

from aiohttp import web
import aiohttp

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

def jkd_serialize(data):
    return json.dumps(data).encode('utf8')

def jkd_deserialize(bytestring):
    return json.loads(bytestring)

application = HtmlReport()

class Subprocessus(Node):
    #TODO: Manage subprocessus death (and get error message and backtrace if possible)...
    def __init__(self, appname, content=None, **kwargs):
        super().__init__(**kwargs)
        self.subprocess = None
        self.appname = appname
        self.reply = None

    async def launch(self):
        logger.debug("Subprocessus : Launching subprocessus...")
        self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", self.appname, loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        self.done = False
        self.reply = ''

    async def loop(self):
        while not self.done:
            logger.debug("Subprocessus : Waiting for messages...")
            #print("Waiting...", file=sys.stderr, flush=True)
            msg = await self.recv()
            logger.debug("Subprocessus : Handling message : {}".format(str(msg)))
            if msg['reply'] == 'exited':
                self.done = True
            else:
                self.reply = msg['reply']
        # end task
        await self.subprocess.wait()
        await self.bg
        self.subprocess = None

    def send(self, msg):
        logger.debug("Subprocessus : Sending : {}".format(str(msg)))
        #print("Sending : ", str(msg), file=sys.stderr, flush=True)
        self.subprocess.stdin.write(jkd_serialize(msg) + b'\n')

    async def recv(self):
        line = await self.subprocess.stdout.readline()
        msg = jkd_deserialize(line[:-1])
        return msg

    async def aget(self, address = None):
        if self.subprocess is None:
            await self.launch()
            self.bg = self.env.loop.create_task(self.loop())
        logger.debug("Subprocessus : Running on...")
        #print("Running on...", file=sys.stderr, flush=True)
        # Try to write...
        self.send({'cmd':'get'})
        #TODO: Wait a little bit for the message reply !
        #await asyncio.sleep(1)

        return self.reply


async def continuous_task(c):
    while True:
        await asyncio.sleep(1)
        c.count += 1


class Environment(Container):

    def __init__(self):
        super().__init__(env=self)
        self.loop = asyncio.get_event_loop()

    def run(self):
        # default
        self.loop.run_forever()


#class MyProtocol(asyncio.Protocol):
#
#    def connection_made(self, transport):
#        print('pipe opened', file=sys.stderr, flush=True)
#        super(MyProtocol, self).connection_made(transport=transport)
#
#    def data_received(self, data):
#        print('received: {!r}'.format(data), file=sys.stderr, flush=True)
#        print(data.decode(), file=sys.stderr, flush=True)
#        super(MyProtocol, self).data_received(data)
#
##    def pipe_data_received(self, data):
##        print('pipe received: {!r}'.format(data), file=sys.stderr, flush=True)
##        print(data.decode(), file=sys.stderr, flush=True)
##        super(MyProtocol, self).data_received(data)
##
#    def connection_lost(self, exc):
#        print('pipe closed', file=sys.stderr, flush=True)
#        super(MyProtocol, self).connection_lost(exc)



class SubApplication(Environment):
    def __init__(self, appname, **kwargs):
        super().__init__(**kwargs)
        self.done = False
        # Get inputs from stdin & send output to stdout
        self.appname = appname

        self.test_count = 0
        self.main = self.loop.create_task(self.test_task())

        #self.read_p = self.loop.connect_read_pipe(MyProtocol, sys.stdin)
        self.reader_t = self.loop.create_task(self.aio_readline())
        #print(sys.stdin.read(3), file = sys.stderr, flush=True)
        #self.write_p = self.loop.connect_write_pipe(MyProtocol, sys.stdout)
        #self.loop.add_reader(sys.stdin.fileno(), self.reader)
        #self.loop.add_writer(sys.stdout.fileno(), self.writer)
        #sys.stdout.write("Subapplication init OK...")

    def send(self, msg):
        logger.debug("SubApplication : Sending message : {}".format(str(msg)))
        line = jkd_serialize(msg) + b'\n'
        logger.debug("SubApplication : Serialized message : {}".format(line))
        # To write binary data to stdout, use buffer.raw
        sys.stdout.buffer.raw.write(line)
        logger.debug("SubApplication : message sent")

    async def handler(self, msg):
        logger.debug("SubApplication : Handling message : {}".format(str(msg)))
        if msg['cmd'] == 'get':
            self.reply = {'reply':'This is the reply from the subprocess application : ' + str(self.test_count) + ' cycles done'}
            self.send(self.reply)
        elif msg['cmd'] == 'exit':
            self.reply = {'reply':'exited'}
            self.send(self.reply)
            self.done = True
            self.loop.exit()

    async def aio_readline(self):
        while not self.done:
            logger.debug("SubApplication : Waiting...")
            line = await self.loop.run_in_executor(None, sys.stdin.readline)
            msg = jkd_deserialize(line[:-1])
            await self.handler(msg)
            #print('Got line:', line, end='', file=sys.stderr, flush=True)

#    def reader(self, stream):
#        sys.stderr.write("reader...")
#        pass
#
#    def writer(self, stream):
#        sys.stderr.write("writer...")
#        pass
#
    async def test_task(self):
        while True:
            await asyncio.sleep(1)
            self.test_count += 1
            self.send({'reply':'Update at ' + str(self.test_count) + ' cycles'})

import json
import jinja2
import aiohttp_jinja2

class HttpServer(Environment):

    def __init__(self):
        super().__init__()
        self.web_app = web.Application()

        self.loop = self.web_app.loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

        self.web_app.router.add_get('/', self.handle)
        self.web_app.router.add_static('/static', 'static/')
        self.web_app.router.add_get('/ws', self.ws_handler)
        self.web_app.router.add_get('/tmpl/{x}', self.tmpl_handler)
        #self.web_app.router.add_get('/{app}', self.handle)
        #self.web_app.router.add_get('/{app}/{address:[^{}$]+}', self.handle)
#        self.processor = Processor(env = self)
#        self.test_application = HtmlReport(env = self, processor = self.processor)
        self.test_application = BokehOfflineReportHtml(env = self)
        self.count = 1
        self.task = self.loop.create_task(continuous_task(self))

        aiohttp_jinja2.setup(self.web_app, loader=jinja2.FileSystemLoader('templates/'))

        self.ext_app = Subprocessus('heavyapp', env = self)

    async def ws_send(self, message):
        if self.ws is not None:
            self.ws.send_str(json.dumps(message))

    async def ws_handler(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                message = json.loads(msg.data);
                if msg.data == 'close':
                    await self.ws.close()
                else:
                    # test echo reply
                    await self.ws_send({"reply": message['data'] + '/answer'})
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.warning('ws connection closed with exception %s' %
                  self.ws.exception())
        logger.debug('websocket connection closed')
        return self.ws

    @aiohttp_jinja2.template('tmpl.jinja2')
    def tmpl_handler(self, request):
        return {'name': 'Andrew', 'surname': 'Svetlov'}


    async def handle(self, request):
        name = request.match_info.get('app', "Anonymous")

        if name == "Anonymous":
            text = "<html><body><p>Count = {}</p></body></html>".format(self.count)

            #text = await self.test_application.aget()
        else:
            logger.debug("application :{:s} // address: {:s}".format(name, request.match_info.get('address', "")))
            #self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", "testapp", loop=self.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
            #line = b' '
            #text = ''
            #while line != b'':
            #    line = await self.subprocess.stdout.readline()
            #    print('line=', line)
            #    text += line.decode('ascii')
            #await self.subprocess.wait()
            address = request.match_info.get('address', "")
            text = await self.ext_app.aget(address)
            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

        #text = "Hello, " + name
        return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    def run(self):
        logger.info("serving...")
        web.run_app(self.web_app)
