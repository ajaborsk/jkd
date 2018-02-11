import asyncio
from .logging import *

import xml.etree.ElementTree as ET

class Port:
    def __init__(self):
        self.input = asyncio.Queue()
        self.output = asyncio.Queue()

    # Low level API (but maybe using directly Queue API would be sufficent ?)
    async def send(self, message):
        await self.input.put(message)

    async def recv(self):
        return await self.output.get()

    # High level API
    async def get(self, address = None):
        #TODO
        pass

    async def set(self, value, address = None):
        #TODO
        pass

    # conditional / complex get
    async def request(self, query, address = None):
        #TODO
        pass


class Node:
    def __init__(self, env = None, name = ''):
        #print("setting env to", env)
        self.env = env
        self.next_qid = 0
        # name for debugging purpose
        self.name = name
        logger.debug(str(self.__class__)+" name :" + self.name)
        # Input queue
        self.input = asyncio.Queue()
        self.queries = {}
        # Output connections
        self.connections = []
        self.done = False
        if self.env is not None and hasattr(self.env, 'loop'):
            print("launching mainloop...")
            self.loop_task = self.env.loop.create_task(self.mainloop())

    async def mainloop(self):
        logger.debug(str(self.__class__)+self.name + ": Entering mainloop...")
        while not self.done:
            msg = await self.input.get()
            logger.debug(str(self.__class__)+self.name + ": Handling msg: " + str(msg))
            await self.msg_handle(msg)

    async def msg_handle(self, msg):
        if 'qid' in msg:
            qid = msg['qid']
            if qid in self.queries:
                await self.queries[qid].put(msg)
                if 'eoq' in msg and msg['eoq'] == True:
                    del self.queries[qid]
            else:
                logger.warning('No registred query id '+str(qid))
        else:
            logger.warning(str(self.__class__)+self.name + ": Unhandled msg: " + str(msg))

    def get_etnode(self):
        return ET.Element()

    async def query(self, destination, query):
        qid = self.next_qid
        query.update({'qid':qid, 'src':self})
        self.queries[qid] = asyncio.Queue()
        await destination.input.put(query)
        self.next_qid += 1
        return qid

    async def wait_for_reply(self, qid, timeout = 10.):
        return await asyncio.wait_for(self.queries[qid].get(), timeout, loop = self.env.loop)

    async def aget(self, portname = None):
        """Return a ElementTree that represent the Node full state (if possible) or the port value
        """
        logger.warning("Unimplemented aget() method.")

    def serialize(self):
        """
        """
        pass

    def connect(self, dest, **kwargs):
        #TODO: whole thing...
        pass
