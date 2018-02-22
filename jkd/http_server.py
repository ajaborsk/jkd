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
        self.next_lcid = 0
        self.next_wsid = 0
        self.ws = {}
        self.ws_channels = {}
        self.web_app = web.Application()

        self.web_app.router.add_get('/', self.http_handler)
        self.web_app.router.add_static('/static', 'static/')
        self.web_app.router.add_get('/ws', self.ws_handler)
#        self.web_app.router.add_get('/tmpl/{x}', self.tmpl_handler)
        self.web_app.router.add_get('/{app}', self.http_handler)
        self.web_app.router.add_get('/{app}/{address}', self.http_handler)

        aiohttp_jinja2.setup(self.web_app, loader=jinja2.FileSystemLoader('templates/'))

    async def msg_ws_send(self, wsid, message):
        if self.ws[wsid] is not None and self.ws[wsid].closed == False:
            await self.ws[wsid].send_json(message)
        else:
            self.info('Trying to send message '+str(message)+' to WS'+str(wsid)+' while it is closed => closing channel', 'msg')
            # Closing channel
            # Send back a 'stop' query update
            channel = self.ws_channels[(wsid, message['lcid'])]
            msg = {'lcid':channel['lcid'], 'prx_src':self, 'prx_dst':channel['prx_src'], 'cmd':'close', 'flags':'d'}
            await self.msg_send(channel['prx_src'], msg)
            del self.ws_channels[(wsid, message['lcid'])]

    async def reply_for_ws(self, msg, client = None):
        #self.debug("handling reply for ws " + str(msg) + ' client:' + str(client), 'msg')
        lcid = client['lcid']
        wsid = client['wsid']
        #self.debug("ids = "+str(lcid)+' '+str(wsid))
        self.ws_channels[(wsid, lcid)] = {'lcid':msg['lcid'], 'prx_src':msg['prx_src']}
        msg['lcid'] = lcid
        del msg['prx_src'] # remove non serializable tag
        #self.debug("ids = "+str(lcid)+' '+str(wsid))
        await self.msg_ws_send(wsid, msg)
        #self.debug("handled reply for ws " + str(msg) + ' client:' + str(client))

    async def ws_handler(self, request):
        wsid = self.next_wsid
        self.next_wsid += 1
        self.ws[wsid] = web.WebSocketResponse()
        await self.ws[wsid].prepare(request)
        self.info("websocket connection {} opened".format(wsid), 'msg')
        async for message in self.ws[wsid]:
            if message.type == aiohttp.WSMsgType.TEXT:
                if message.data == 'close':
                    #TODO : Better close handling
                    await self.ws[wsid].close()
                else:
                    msg = json.loads(message.data);
                    self.debug('WS message received : '+str(msg), "msg")
                    if 'lcid' in msg and (wsid, msg['lcid']) in self.ws_channels:
                        self.debug("Send on existing channel "+str(msg), 'msg')
                        channel = self.ws_channels[(wsid, msg['lcid'])]
                        msg['lcid'] = channel['lcid']
                        msg['prx_src'] = self
                        await self.msg_send(channel['prx_src'], msg)
                    elif 'url' in msg:
                        appname = msg['url'][1:].split('/')[0]
                        lcid = await self.query(self[appname], msg, self.reply_for_ws, {'wsid':wsid, 'lcid':msg['lcid']})
                    elif msg['lcid'] == "q1":
                        reply = await self.ext_app.aget(msg['lcid'])
                    elif msg['lcid'] == "q2":
                        reply = await self.ext_app2.aget(msg['lcid'])
                    else:
                    # test echo reply
                        reply = await self.ext_app.aget("other")
#                    await self.msg_ws_send({"reply": message['data'] + '/answer'})
                        await self.msg_ws_send(wsid, {"reply": reply})
            elif message.type == aiohttp.WSMsgType.ERROR:
                self.warning('websocket connection {} closed with exception {}'.format(wsid, self.ws[wsid].exception()), 'msg')
            else:
                self.warning('websocket connection {} unhandled message {} '.format(wsid, message), 'msg')
        self.debug('websocket connection {} closed'.format(wsid), 'msg')
        return self.ws[wsid] #useless ?

    # @aiohttp_jinja2.template('tmpl.jinja2')
    # def tmpl_handler(self, request):
        # return {'name': 'Andrew', 'surname': 'Svetlov'}

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
                self[name] = Application(env = self.env, parent = self.env, name = name)
                app = self[name]

            if app is not None:
                lcid = await self.query(app, {'query':'get', 'src':self.fqn(), 'url':name})
                #self.debug("Query launched "+str(lcid))
                #self.next_lcid += 1
                text = "Timeout."
                try:
#                    text = await asyncio.shield(self.wait_for_reply(lcid, timeout = 0.1))
                    msg = await self.wait_for_reply(lcid, timeout = 5.)
                    text = msg['reply']
                except asyncio.TimeoutError:
                    self.info("http request timeout")
                #self.debug("Query first reply "+str(lcid))
                if lcid in self.channels:
                    del self.channels[lcid] # remove query input queue
            else:
                #TODO : True 404 Not Found page
                text = 'Application Not found'
            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

        return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    def run(self):
        web.run_app(self.web_app)

