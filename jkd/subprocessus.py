from .node import *
from .serialize import *

class Subprocessus(Node):
    #TODO: Manage subprocessus death (and get error message and backtrace if possible)...
    def __init__(self, appname, content=None, **kwargs):
        super().__init__(**kwargs)
        self.subprocess = None
        self.appname = appname
        self.reply = None
        self.subscription = None

    def subscribe(self, coro):
        self.subscription = coro

    async def launch(self):
        logger.debug("Subprocessus {}s : Launching subprocessus...".format(self.appname))
        self.subprocess = await asyncio.create_subprocess_exec("python", "-m", "jkd", "slave", self.appname, loop=self.env.loop, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
        self.done = False
        self.reply = ''

    async def loop(self):
        while not self.done:
            logger.debug("Subprocessus {}s : Waiting for messages...".format(self.appname))
            #print("Waiting...", file=sys.stderr, flush=True)
            msg = await self.recv()
            logger.debug("Subprocessus {}s : Handling message : {}".format(self.appname, str(msg)))
            if 0:#msg['reply'] == 'exited':
                self.done = True
            else:
                #self.reply = msg['reply']
                if self.subscription is not None:
#                if asyncio.iscoroutine(self.subscription):
                    pass
                    logger.debug("Subprocessus {}s : transfering message {}...".format(self.appname, str(msg)))
                    await self.subscription(msg)
                    logger.debug("Subprocessus {}s : message transfered : {}".format(self.appname, str(msg)))
        # end task
        await self.subprocess.wait()
        await self.bg
        self.subprocess = None

    def send(self, msg):
        logger.debug("Subprocessus {}s : Sending : {}".format(self.appname, str(msg)))
        #print("Sending : ", str(msg), file=sys.stderr, flush=True)
        self.subprocess.stdin.write(jkd_serialize(msg) + b'\n')

    async def recv(self):
        line = await self.subprocess.stdout.readline()
        msg = jkd_deserialize(line[:-1])
        return msg

    # Initiate a query (launching subprocess if not already running)
    async def aget(self, qid = None):
        if self.subprocess is None:
            await self.launch()
            self.bg = self.env.loop.create_task(self.loop())
        logger.debug("Subprocessus {}s: Running on...".format(self.appname))
        #print("Running on...", file=sys.stderr, flush=True)
        # Try to write...
        self.send({'qid':qid, 'cmd':'get'})
        #TODO: Wait a little bit for the message reply !
        #await asyncio.sleep(1)

        return self.reply

