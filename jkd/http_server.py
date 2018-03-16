from urllib.parse import urlparse
import os.path
import json

from aiohttp import web
import aiohttp
import jinja2
import aiohttp_jinja2

from .container import *
from .subprocessus import *
from .application import*


class HttpServer(Node):
    tagname = "http_server"
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
        self.web_app.router.add_get('/view/{app}', self.http_view_handler)
        self.web_app.router.add_get('/{app}', self.http_handler)
        self.web_app.router.add_get('/{app}/{address:[^{}$]+}', self.http_handler)
        self.web_app.router.add_put('/{app}/{address:[^{}$]+}', self.http_put_handler)

        aiohttp_jinja2.setup(self.web_app, loader=jinja2.FileSystemLoader('templates/'))

    async def msg_ws_send(self, wsid, message):
        if self.ws[wsid] is not None and self.ws[wsid].closed == False:
            await self.ws[wsid].send_json(message)
        else:
            self.info('Trying to send message '+str(message)+' to WS'+str(wsid)+' while it is closed => closing channel', 'msg')
            # Closing channel
            # Send back a 'stop' query update
            channel = self.ws_channels[(wsid, message['lcid'])]
            msg = {'lcid':channel['lcid'], 'prx_src':self, 'cmd':'close', 'flags':'d'}
            await self.msg_send(channel['prx_src'], msg)
            del self.ws_channels[(wsid, message['lcid'])]
            self.debug('ws_channels['+str((wsid, message['lcid']))+'] deleted', 'msg')

    async def reply_for_ws(self, msg, client = None):
        #self.debug("handling reply for ws " + str(msg) + ' client:' + str(client), 'msg')
        lcid = client['lcid']
        wsid = client['wsid']
        #self.debug("ids = "+str(lcid)+' '+str(wsid))
        if 'f' in msg['flags']:
            self.ws_channels[(wsid, lcid)] = {'lcid':msg['lcid'], 'prx_src':msg['prx_src']}
            self.debug('ws_channels['+str((wsid, lcid))+'] = '+str({'lcid':msg['lcid'], 'prx_src':msg['prx_src']}), 'msg')
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
                    #self.debug('WS message received : '+str(msg), "msg")
                    if 'lcid' in msg and (wsid, msg['lcid']) in self.ws_channels:
                        # This is a message for a existing channel
                        #self.debug("Send on existing channel "+str(msg), 'msg')
                        channel = self.ws_channels[(wsid, msg['lcid'])]
                        msg['lcid'] = channel['lcid']
                        msg['prx_src'] = self
                        await self.msg_send(channel['prx_src'], msg)
                    elif 'url' in msg:
                        self.debug("msg: " + str(msg), "msg")
                        path = msg['url'].split('/')
                        app_name = path[1]
                        port_name = path[-1]
                        msg_url = '/'.join(path[1:-1])
                        self.debug('url data: '+str(path)+' '+str(app_name)+' '+str(msg_url)+' '+str(port_name))
                        msg['url'] = msg_url
                        msg['port']= port_name
                        #appname = msg['url'][1:].split('/')[0]
                        if app_name in self.env:
                            lcid = await self.msg_query(self.env[app_name], msg, self.reply_for_ws, {'wsid':wsid, 'lcid':msg['lcid']})
                        else:
                            self.warning('Unknown application: '+str(app_name))
                    elif msg['lcid'] == "q1":
                        reply = await self.ext_app.aget(msg['lcid'])
                    elif msg['lcid'] == "q2":
                        reply = await self.ext_app2.aget(msg['lcid'])
                    else:
                    # test echo reply
                        self.warning("Unknown lcid for message: "+str(msg), "msg")
                        #reply = await self.ext_app.aget("other")
#                    await self.msg_ws_send({"reply": message['data'] + '/answer'})
                        #await self.msg_ws_send(wsid, {"reply": reply})
            elif message.type == aiohttp.WSMsgType.ERROR:
                self.warning('websocket connection {} closed with exception {}'.format(wsid, self.ws[wsid].exception()), 'msg')
            else:
                self.warning('websocket connection {} unhandled message {} '.format(wsid, message), 'msg')
        #self.debug('websocket connection {} closed'.format(wsid), 'msg')
        return self.ws[wsid] #useless ?

    # @aiohttp_jinja2.template('tmpl.jinja2')
    # def tmpl_handler(self, request):
        # return {'name': 'Andrew', 'surname': 'Svetlov'}

    async def http_handler(self, request):
        self.debug("request: "+repr(request))
        name = request.match_info.get('app', "Anonymous")

        if name == "Anonymous":
            text = "<html><body><p>Default (empty) page</p></body></html>"

        else:
            #self.debug("application :{:s} // address: {:s}".format(name, request.match_info.get('address', "")))
            address = request.match_info.get('address', "")
            self.debug('request: '+str(request.method)+' '+str(request.path)+' '+str(dict(request.query)))
            #text = await self.ext_app.aget(address)

            path = request.url.path.split('/')
            app_name = path[1]
            port_name = path[-1]
            msg_url = '/'.join(path[1:-1])
            if port_name == '':
                port_name = 'index.html'

            self.debug('url data: '+str(path)+' '+str(app_name)+' '+str(msg_url)+' '+str(port_name))

            try:
                app = self.env[app_name]
                text = await self.msg_query(app, {'method':'get', 'policy':'immediate', 'src':self.fqn(), 'url':msg_url, 'port':port_name, 'args':dict(request.query)}, timeout = 50.)
                if text is None:
                    text = 'Timeout...'
                else:
                    text = str(text)
            except KeyError:
                # Application not found
                #TODO : True 404 Not Found page
                text = 'Application Not found'

            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

        return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    async def http_put_handler(self, request):
        self.debug("PUT: "+str(request))
        app_name = request.match_info.get('app', "")
        if app_name == "":
            text = "<html><body><p>Default (empty) page</p></body></html>"
        else:
            text='well done !'
            path = request.url.path.split('/')
            app_name = path[1]
            port_name = path[-1]
            msg_url = '/'.join(path[1:-1])
            if port_name == '':
                port_name = 'data'
            self.debug('url data: '+str(path)+' '+str(app_name)+' '+str(msg_url)+' '+str(port_name))
            self.debug("args: " + str(await request.json()))
            try:
                app = self.env[app_name]
                text = await self.msg_query(app, {'method':'put', 'policy':'immediate', 'src':self.fqn(), 'url':msg_url, 'port':port_name, 'args':dict(await request.json())}, timeout = 50.)
                if text is None:
                    text = 'Timeout...'
                else:
                    text = str(text)
            except KeyError:
                # Application not found
                #TODO : True 404 Not Found page
                text = 'Application Not found'
            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))
        return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    @aiohttp_jinja2.template('edit.jinja2')
    async def http_view_handler(self, request):
        app_name = request.match_info.get('app', "")
        try:
            app = self.env[app_name]
            data = await self.msg_query(app, {'method':'get', 'policy':'immediate', 'src':self.fqn(), 'url':app_name, 'port':'state'}, timeout = 50.)
            self.debug("data"+str(data))
            if data is None:
                text = 'Timeout...'
                return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))
            else:
                print(data)
                return {'name':app_name, 'nodes':{app_name: data}}
        except KeyError:
            # Application not found
            #TODO : True 404 Not Found page
            text = 'Application Not found'
            return web.Response(content_type = "text/html", charset = 'utf-8', body = text.encode('utf_8'))

    def run(self, host='0.0.0.0', port=8080):
        self.debug("serving on "+str(host)+':'+str(port))
        super().run()
        while True:
            # Run web server, relaunching on OSError (broken socket for WS : aiohttp bug ??)
            try:
                web.run_app(self.web_app, host = host, port = port)
            except OSError:
                pass

