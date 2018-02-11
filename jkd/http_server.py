import json

from aiohttp import web
import aiohttp
import jinja2
import aiohttp_jinja2

from .container import *
from .subprocessus import *


class HttpServer(Container):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.web_app = web.Application()

        self.web_app.router.add_get('/', self.handle)
        self.web_app.router.add_static('/static', 'static/')
        self.web_app.router.add_get('/ws', self.ws_handler)
        self.web_app.router.add_get('/tmpl/{x}', self.tmpl_handler)
        #self.web_app.router.add_get('/{app}', self.handle)
        #self.web_app.router.add_get('/{app}/{address:[^{}$]+}', self.handle)
#        self.processor = Processor(env = self)
#        self.test_application = HtmlReport(env = self, processor = self.processor)
#        self.test_application = BokehOfflineReportHtml(env = self)
#        self.count = 1
#        self.task = self.loop.create_task(continuous_task(self))

        aiohttp_jinja2.setup(self.web_app, loader=jinja2.FileSystemLoader('templates/'))

        self.ext_app = Subprocessus('heavyapp', env = self.env)
        self.ext_app.subscribe(self.ws_send)
        self.ext_app2 = Subprocessus('heavyapp2', env = self.env)
        self.ext_app2.subscribe(self.ws_send)

    async def ws_send(self, message):
        if self.ws is not None:
            self.ws.send_str(json.dumps(message))

    async def ws_handler(self, request):
        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        async for message in self.ws:
            if message.type == aiohttp.WSMsgType.TEXT:
                if message.data == 'close':
                    #TODO : Better close handling
                    await self.ws.close()
                else:
                    msg = json.loads(message.data);
                    if msg['qid'] == "q1":
                        reply = await self.ext_app.aget(msg['qid'])
                    elif msg['qid'] == "q2":
                        reply = await self.ext_app2.aget(msg['qid'])
                    else:
                    # test echo reply
                        reply = await self.ext_app.aget("other")
#                    await self.ws_send({"reply": message['data'] + '/answer'})
                    await self.ws_send({"reply": reply})
            elif message.type == aiohttp.WSMsgType.ERROR:
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
        web.run_app(self.web_app)

