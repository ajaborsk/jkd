import inspect

from .node import *
from .serialize import *

class Subprocessus(Node):
    tagname = "subprocessus"
    #TODO: Manage subprocessus death (and get error message and backtrace if possible)...
    def __init__(self, appname, content=None, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.subprocess = None
        self.appname = appname
        self.next_pipe_lcid = 2000
        self.reply = None
        #self.subscription = None
        self.pipe_channels = {}
        if elt is not None:
            self.xml_contents = ET.tostring(elt, encoding='utf8')
        else:
            self.xml_contents = ''
            self.warning("No description for suprocess.")

    def subscribe(self, coro):
        self.subscription = coro

    async def _introspect(self, args={}):
        ret = await super()._introspect(args=args)
        ret['subprocess'] = str(self.subprocess)
        return ret

    async def launch(self):
        #self.debug("Subprocessus {}s : Launching subprocessus...".format(self.appname))
        test_xml = b'"' + self.xml_contents.replace(b'"', b'\"') + b'"'
        self.debug(test_xml.decode('utf8'))
        try:
            #self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", self.fqn(), '"' + self.xml_contents.replace('"', '\\"') + '"', loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
            self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "-m", "slave", self.fqn(), test_xml.decode('utf8'), loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
            self.done = False
            self.reply = ''
        except Exception as ex:
            self.subprocess = None
            self.warning("Unable to launch subprocess: " + str(ex))

    async def msg_pipe_loop(self):
        while not self.done:
            #self.debug("Subprocessus {}s : Waiting for messages...".format(self.appname))
            #print("Waiting...", file=sys.stderr, flush=True)
            msg = await self.msg_pipe_recv()
            #self.debug("Subprocessus {} : Handling message : {}".format(self.appname, str(msg)), 'msg')

            if 'lcid' in msg and msg['lcid'] in self.pipe_channels:
                # Get the pipe channel stored at creation
                pipe_channel = self.pipe_channels[msg['lcid']]
                #self.debug('pipe_channel = '+str(pipe_channel),'msg')
                if 'f' in msg['flags']:
                    self.back_channels[(id(pipe_channel['prx_dst']), pipe_channel['lcid'])] = msg['lcid']
                    self.debug('subp:back_channels['+str((id(pipe_channel['prx_dst']), pipe_channel['lcid']))+'] = '+str(self.back_channels[(id(pipe_channel['prx_dst']), pipe_channel['lcid'])]), 'msg')
                # Get the queue channel id and create a queue channel reference
                #self.channels[channel['lcid']] =
                msg.update({'lcid':pipe_channel['lcid']})
                msg.update({'prx_src':self})
                #self.debug('reply_to'+str(channel['prx_dst']), 'msg')
                await self.msg_send(pipe_channel['prx_dst'], msg)

#            if 0:#msg['reply'] == 'exited':
#                self.done = True
#            else:
#                if inspect.iscoroutinefunction(self.subscription):
#                    #self.debug("Subprocessus {}s : transfering message {}...".format(self.appname, str(msg)))
#                    await self.subscription(msg)
#                    self.debug("Subprocessus {}s : message transfered : {}".format(self.appname, str(msg)))
        # end task
        await self.subprocess.wait()
        await self.bg
        self.subprocess = None

    def msg_pipe_send(self, msg):
        "Send message to subprocess pipe"
        #self.debug("Sending : {}".format(self.appname, str(msg)))
        self.subprocess.stdin.write(jkd_serialize(msg) + b'\n')

    async def msg_pipe_recv(self):
        "Get message from subprocess pipe"
        line = await self.subprocess.stdout.readline()
        msg = jkd_deserialize(line[:-1])
        return msg

    async def msg_queue_handle(self, msg):
        #self.debug("msg_handle: "+str(msg), 'msg')

        if 'c' in msg['flags']:
            if self.subprocess is None:
                await self.launch()
                self.bg = self.env.loop.create_task(self.msg_pipe_loop())

            pipe_lcid = self.next_pipe_lcid
            self.next_pipe_lcid += 1
            self.pipe_channels[pipe_lcid] = {'prx_dst':msg['prx_src'], 'lcid':msg['lcid']} # reply_to
            self.debug("pipe_channels["+str(pipe_lcid)+"] = "+str(self.pipe_channels[pipe_lcid]), 'msg')
            msg['lcid'] = pipe_lcid
            del msg['prx_src']
            #self.debug("subprocessus.sending to process: " + str(msg), 'msg')
            self.msg_pipe_send(msg)
        elif 'f' in msg['flags']:
            #TODO
            pass
        else:
            key = (id(msg['prx_src']), msg['lcid'])
            #self.debug("USE: key = "+str(key)+' msg='+str(msg), "msg")
            if key in self.back_channels:
                #self.debug("USE1: ", "msg")
                pipe_lcid = self.back_channels[key]
                msg['lcid'] = pipe_lcid
                #self.debug("USE2: pipe_lcid = "+str(pipe_lcid)+' msg='+str(msg), "msg")
                #self.debug("subprocessus.sending to process: " + str(msg), 'msg')
                del msg['prx_src'] # remove non serializable (and useless) part
                self.msg_pipe_send(msg)
                #self.debug("USE3: msg="+str(msg), "msg")
                if 'd' in msg['flags']:
                    del self.back_channels[key]
                    self.debug('Removing back channels for key = ' + str(key), 'msg')
                    del self.pipe_channels[pipe_lcid]
                    self.debug('Removing pipe channels for pipe_lcid = ' + str(pipe_lcid), 'msg')
            else:
                self.warning('pipe channel not found for source'+str(), 'msg')


        # else:
            # self.warning('Unhandled (queue) incoming message: ' + str(msg), 'msg')

    # async def msg_query_handle(self, msg):
        # "Handle message from python queue input"
        # self.debug("subprocessus.query_handle: " + str(msg), 'msg')


        # if 'query' in msg:
            # if self.subprocess is None:
                # await self.launch()
                # self.bg = self.env.loop.create_task(self.loop())
            # pipe_lcid = self.next_pipe_lcid
            # self.next_pipe_lcid += 1

            # #self.debug("subprocessus.sending to process: " + str({'lcid':msg['lcid'], 'query':'data'}), 'msg')
            # self.pipe_channels[pipe_lcid] = {'prx_dst':msg['prx_src'], 'lcid':msg['lcid']} # reply_to

        # self.send({'lcid':pipe_lcid, 'query':'data'})
        # #return self.reply

    # Initiate a query (launching subprocess if not already running)
    # async def aget(self, lcid = None):
        # if self.subprocess is None:
            # await self.launch()
            # self.bg = self.env.loop.create_task(self.loop())
        # #self.debug("Subprocessus {}s: Running on...".format(self.appname))
        # #print("Running on...", file=sys.stderr, flush=True)
        # # Try to write...
        # self.send({'lcid':lcid, 'cmd':'get'})
        # #TODO: Wait a little bit for the message reply !
        # #await asyncio.sleep(1)

        # return self.reply

