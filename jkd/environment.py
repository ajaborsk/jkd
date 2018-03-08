# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 09:48:33 2018

"""
import sys
import asyncio

if sys.platform == 'win32':
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

from .logging import *
from .container import Container
from .report_bokeh_offline_html import *

import time

#TODO: A better repository system (parsing source directories ?)
from .html_page import HtmlPage
from .subprocessus import Subprocessus
from .signal_generator import SignalGenerator
from .serial_capture import SerialCapture
from .data_file import DataFile
from .history import History
from .text_parser import TextParser
from .serial_line_process import SerialLineProcess
from .data_process import DataProcess
from .cache import Cache
from .sql_datasource import SqlDatasource
registry = {
        "html_page":HtmlPage,
        "subprocessus":Subprocessus,
        "cache":Cache,            # Not Working (yet) !
        "data_file":DataFile,     # Not Working (yet) !
        "history":History,
        "signal_generator":SignalGenerator,
        "serial_capture":SerialCapture,
        "text_parser":TextParser,
        "serial_line_process":SerialLineProcess,
        "data_process":DataProcess,
        "sql_datasource":SqlDatasource,
         }


class Environment(Container):
    tagname = "environment"
    def __init__(self):
        self.loggers = {'main':logger_main, "msg":logger_msg}
        super().__init__(env=self, name='/env')
        self.loop = asyncio.get_event_loop()
        # Manually launch mainloop since self.loop was not initialized on Node class initialization
        self.loop_task = self.env.loop.create_task(self.msg_queue_loop())
        self.registry = registry


    def run(self):
        # default
        self.loop.run_forever()


import time

from .serialize import *

class EnvSubApplication(Environment):
    tagname = "env_sub_application"
    def __init__(self, root_name, tree = None, **kwargs):
        self.root_name = '/'.join(root_name.split('/')[:-1])
        super().__init__(**kwargs)
        self.name = 'env'
        self.done = False
        self.pipe_channels = {}

        self.root = Container(env = self, parent = self, name = root_name.split('/')[-1], elt = tree, **kwargs)
        self.root.run()
        if tree is not None:
            # Construct the sub-application tree
            self.debug("tree appname = " + str(tree.attrib['appname']))
            for elt in tree:
                self.debug("  subnode " + str(elt.tag))

        # Launch the reading/handle mainloop task
        self.reader_t = self.loop.create_task(self.msg_pipe_loop())
        #self.debug("subapplication initialized")

    def fqn(self):
        return self.root_name

    async def _introspect(self):
        ret = await super()._introspect()
        ret['subprocess'] = str(self.pipe_channels)
        return ret

    def msg_pipe_send(self, msg):
        #self.debug("SubApplication {}: Sending message : {}".format(self.root_name, str(msg)), 'msg')
        line = jkd_serialize(msg) + b'\n'
        #self.debug("SubApplication {}s: Serialized message : {}".format(self.appname, line))
        # To be sure to write binary data to stdout, use .buffer.raw
        sys.stdout.buffer.raw.write(line)
        #self.debug("SubApplication {}s: message sent".format(self.appname))

    async def msg_queue_handle(self, msg):
        #self.debug("Handling queue message: {}".format(str(msg)), 'msg')
        if 'query' in msg:
            #TODO: Transmit query from subprocess node to parent process
            pass
        elif 'reply' in msg:
            pipe_lcid = self.channels[msg['lcid']]
            msg['lcid'] = pipe_lcid
            del msg['prx_src'] # not serializable entry
            self.msg_pipe_send(msg)

    async def msg_pipe_handle(self, msg):
        #self.debug("Handling pipe message: {}".format(str(msg)), 'msg')
        if 'c' in msg['flags']:
            #self.debug(" Query message", 'msg')
            pipe_lcid = msg['lcid']
            queue_lcid = await self.msg_send(self.root, msg)
            self.channels[queue_lcid] = pipe_lcid
            self.debug('self.channels['+str(queue_lcid)+'] = '+str(self.channels[queue_lcid]),'msg')
        else:
            self.debug("non c msg="+str(msg),"msg")
            pipe_lcid = msg['lcid']
            self.debug("non c pipe_lcid="+str(pipe_lcid),"msg")
            channel = self.back_channels[pipe_lcid]
            self.debug("non c channel="+str(channel),"msg")
            msg['lcid'] = channel['lcid']
            await self.msg_queue_transmit(channel['prx_dst'], msg)
            self.debug("non c channel done "+str(msg),"msg")

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

        self.loop = self.http_server.web_app.loop
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

    def run(self, host='0.0.0.0', port=8080):
        self.info("Launching http server node...")
        self.http_server.run(host=host, port=port)
