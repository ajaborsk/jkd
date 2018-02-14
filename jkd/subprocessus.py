import inspect

from .node import *
from .serialize import *

class Subprocessus(Node):
    #TODO: Manage subprocessus death (and get error message and backtrace if possible)...
    def __init__(self, appname, content=None, elt = None, **kwargs):
        super().__init__(**kwargs)
        self.subprocess = None
        self.appname = appname
        self.reply = None
        self.subscription = None
        self.pipe_queries = {}

    def subscribe(self, coro):
        self.subscription = coro

    async def launch(self):
        self.debug("Subprocessus {}s : Launching subprocessus...".format(self.appname))
        self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", self.appname, loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        self.done = False
        self.reply = ''

    async def loop(self):
        while not self.done:
            #self.debug("Subprocessus {}s : Waiting for messages...".format(self.appname))
            #print("Waiting...", file=sys.stderr, flush=True)
            msg = await self.recv()
            self.debug("Subprocessus {} : Handling message : {}".format(self.appname, str(msg)))
            if 0:#msg['reply'] == 'exited':
                self.done = True
            else:
                if inspect.iscoroutinefunction(self.subscription):
                    #self.debug("Subprocessus {}s : transfering message {}...".format(self.appname, str(msg)))
                    await self.subscription(msg)
                    #self.debug("Subprocessus {}s : message transfered : {}".format(self.appname, str(msg)))
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
        "Handle message from python queue input"
        self.debug("subprocessus.msg_handle: " + str(msg))
        if 'query' in msg and msg['query'] == 'data':
            if self.subprocess is None:
                await self.launch()
                self.bg = self.env.loop.create_task(self.loop())
        self.debug("subprocessus.sending to process: " + str({'qid':msg['qid'], 'query':'data'}))
        self.pipe_queries[msg['qid']] = {'dst':msg['src']} # reply_to
        self.send({'qid':msg['qid'], 'query':'data'})
        return self.reply

    # Initiate a query (launching subprocess if not already running)
    async def aget(self, qid = None):
        if self.subprocess is None:
            await self.launch()
            self.bg = self.env.loop.create_task(self.loop())
        #self.debug("Subprocessus {}s: Running on...".format(self.appname))
        #print("Running on...", file=sys.stderr, flush=True)
        # Try to write...
        self.send({'qid':qid, 'cmd':'get'})
        #TODO: Wait a little bit for the message reply !
        #await asyncio.sleep(1)

        return self.reply

