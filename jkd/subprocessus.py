import inspect

from .node import *
from .serialize import *

class Subprocessus(Node):
    #TODO: Manage subprocessus death (and get error message and backtrace if possible)...
    def __init__(self, appname, content=None, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.subprocess = None
        self.appname = appname
        self.next_pipe_lcid = 0
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

    async def launch(self):
        self.debug("Subprocessus {}s : Launching subprocessus...".format(self.appname))
        test_xml = b'"' + self.xml_contents.replace(b'"', b'\"') + b'"'
        self.debug(test_xml.decode('utf8'))
        try:
            #self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", self.fqn(), '"' + self.xml_contents.replace('"', '\\"') + '"', loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
            self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", self.fqn(), test_xml.decode('utf8'), loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
            self.done = False
            self.reply = ''
        except Exception as ex:
            self.subprocess = None
            self.warning("Unable to launch subprocess: " + str(ex))

    async def loop(self):
        while not self.done:
            #self.debug("Subprocessus {}s : Waiting for messages...".format(self.appname))
            #print("Waiting...", file=sys.stderr, flush=True)
            msg = await self.recv()
            self.debug("Subprocessus {} : Handling message : {}".format(self.appname, str(msg)), 'msg')

            if 'lcid' in msg and msg['lcid'] in self.pipe_channels:
                channel = self.pipe_channels[msg['lcid']]
                msg.update({'lcid':channel['lcid']})
                msg.update({'prx_src':self})
                self.debug('reply_to'+str(channel['prx_dst']), 'msg')
                await self.msg_send(channel['prx_dst'], msg)

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

    def send(self, msg):
        "Send message to subprocess pipe"
        #self.debug("Subprocessus {}s : Sending : {}".format(self.appname, str(msg)))
        #print("Sending : ", str(msg), file=sys.stderr, flush=True)
        self.subprocess.stdin.write(jkd_serialize(msg) + b'\n')

    async def recv(self):
        "Get message from subprocess pipe"
        line = await self.subprocess.stdout.readline()
        msg = jkd_deserialize(line[:-1])
        return msg

    async def msg_handle(self, msg):
        self.debug("msg_handle: "+str(msg), 'msg')
        pipe_lcid = self.next_pipe_lcid
        self.next_pipe_lcid += 1

        if 'query' in msg:
            if self.subprocess is None:
                await self.launch()
                self.bg = self.env.loop.create_task(self.loop())

            self.pipe_channels[pipe_lcid] = {'prx_dst':msg['prx_src'], 'lcid':msg['lcid']} # reply_to
            msg['lcid'] = pipe_lcid
            del msg['prx_src']
            self.debug("subprocessus.sending to process: " + str(msg), 'msg')
            self.send(msg)

    async def _query_handle(self, msg):
        "Handle message from python queue input"
        self.debug("subprocessus.query_handle: " + str(msg), 'msg')

        pipe_lcid = self.next_pipe_lcid
        self.next_pipe_lcid += 1

        if 'query' in msg:
            if self.subprocess is None:
                await self.launch()
                self.bg = self.env.loop.create_task(self.loop())

        self.debug("subprocessus.sending to process: " + str({'lcid':msg['lcid'], 'query':'data'}), 'msg')
        self.pipe_channels[pipe_lcid] = {'prx_dst':msg['prx_src'], 'lcid':msg['lcid']} # reply_to

        self.send({'lcid':pipe_lcid, 'query':'data'})
        #return self.reply

    # Initiate a query (launching subprocess if not already running)
    async def aget(self, lcid = None):
        if self.subprocess is None:
            await self.launch()
            self.bg = self.env.loop.create_task(self.loop())
        #self.debug("Subprocessus {}s: Running on...".format(self.appname))
        #print("Running on...", file=sys.stderr, flush=True)
        # Try to write...
        self.send({'lcid':lcid, 'cmd':'get'})
        #TODO: Wait a little bit for the message reply !
        #await asyncio.sleep(1)

        return self.reply

