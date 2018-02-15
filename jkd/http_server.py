import os.path
import json

from aiohttp import web
import aiohttp
import jinja2
import aiohttp_jinja2

from .container import *
from .subprocessus import *
from .demo_application import*



class HttpServer(Container):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.debug('httpserver input: '+str(self.input))
        self.next_qid = 0
        self.next_wsid = 0
        self.ws = {}
        self.web_app = web.Application()
        #self.instances = {} # Running applications

        self.web_app.router.add_get('/', self.http_handler)
        self.web_app.router.add_static('/static', 'static/')
        self.web_app.router.add_get('/ws', self.ws_handler)
        self.web_app.router.add_get('/tmpl/{x}', self.tmpl_handler)
        self.web_app.router.add_get('/{app}', self.http_handler)
        self.web_app.router.add_get('/{app}/{address}', self.http_handler)

        aiohttp_jinja2.setup(self.web_app, loader=jinja2.FileSystemLoader('templates/'))

        self.ext_app = Subprocessus('heavyapp', env = self.env)
        self.ext_app.subscribe(self.ws_send)
        self.ext_app2 = Subprocessus('heavyapp2', env = self.env)
        self.ext_app2.subscribe(self.ws_send)

        #self['demo'] = DemoApplication(env = self.env, name="demo")

    async def ws_send(self, wsid, message):
        if self.ws[wsid] is not None:
            self.ws[wsid].send_str(json.dumps(message))

    async def ws_handler(self, request):
        wsid = self.next_wsid
        self.next_wsid += 1
        self.ws[wsid] = web.WebSocketResponse()
        await self.ws[wsid].prepare(request)
        self.info("websocket connection {} opened".format(wsid))
        async for message in self.ws[wsid]:
            if message.type == aiohttp.WSMsgType.TEXT:
                if message.data == 'close':
                    #TODO : Better close handling
                    await self.ws[wsid].close()
                else:
                    msg = json.loads(message.data);
                    if 'dst' in msg:
                        appname = msg['appname']
                        await self.query(self[appname], msg)
                    elif 'url' in msg:
                        appname = msg['url'][2:].split('/')[0]
                        await self.query(self[appname], msg)
                    elif msg['qid'] == "q1":
                        reply = await self.ext_app.aget(msg['qid'])
                    elif msg['qid'] == "q2":
                        reply = await self.ext_app2.aget(msg['qid'])
                    else:
                    # test echo reply
                        reply = await self.ext_app.aget("other")
#                    await self.ws_send({"reply": message['data'] + '/answer'})
                        await self.ws_send(wsid, {"reply": reply})
            elif message.type == aiohttp.WSMsgType.ERROR:
                self.warning('websocket connection {} closed with exception {}'.format(wsid, self.ws[wsid].exception()))
        self.debug('websocket connection {} closed'.format(wsid))
        return self.ws[wsid] #useless ?

    @aiohttp_jinja2.template('tmpl.jinja2')
    def tmpl_handler(self, request):
        return {'name': 'Andrew', 'surname': 'Svetlov'}

    async def http_handler(self, request):
        name = request.match_info.get('app', "Anonymous")

        if name == "Anonymous":
            text = "<html><body><p>Count = {}</p></body></html>".format(self.count)

        else:
            #self.debug("application :{:s} // address: {:s}".format(name, request.match_info.get('address', "")))
            address = request.match_info.get('address', "")
            #text = await self.ext_app.aget(address)
            app = None
            if name in self:
                app = self[name]
            elif os.path.isdir(name) and os.path.isfile(name + '/' + name + '.xml'):
                self[name] = Application(env = self.env, name = name)
                app = self[name]

            if app is not None:
                qid = await self.query(app, {'query':'get'})
                #self.debug("Query launched "+str(qid))
                #self.next_qid += 1
                text = "Timeout."
                try:
#                    text = await asyncio.shield(self.wait_for_reply(qid, timeout = 0.1))
                    msg = await self.wait_for_reply(qid, timeout = 5.)
                    text = msg['reply']
                except asyncio.TimeoutError:
                    self.info("http request timeout")
                #self.debug("Query first reply "+str(qid))
                if qid in self.queries:
                    del self.queries[qid] # remove query input queue
            else:
                #TODO : True 404 Not Found page
                text = 'Application Not found'
            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

        return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    def run(self):
        web.run_app(self.web_app)

