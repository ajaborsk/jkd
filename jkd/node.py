import asyncio

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
        self.debug(str(self.__class__)+" name :" + self.name)
        # Global input queue
        self.input = asyncio.Queue()
        # Per-Query input queues
        self.queries = {}
        # Output connections
        self.connections = []
        self.done = False
        if self.env is not None and hasattr(self.env, 'loop'):
            print("launching mainloop...")
            self.loop_task = self.env.loop.create_task(self.mainloop())

    async def mainloop(self):
        self.debug(str(self.__class__)+self.name + ": Entering mainloop...")
        while not self.done:
            msg = await self.input.get()
            self.debug(str(self.__class__)+self.name + ": Handling msg: " + str(msg))
            await self.msg_handle(msg)

    async def msg_handle(self, msg):
        if 'query' not in msg:
            # This is a reply
            qid = msg['qid']
            if qid in self.queries:
                await self.queries[qid].put(msg)
                if 'eoq' in msg and msg['eoq'] == True:
                    # last message of the reply (eoq = End Of Query), so remove internal dedicated queue
                    del self.queries[qid]
            else:
                self.warning('No registred query id '+str(qid))
        else:
            self.warning(str(self.__class__)+self.name + ": Unhandled msg: " + str(msg))

    def get_etnode(self):
        return ET.Element()

    # Outgoing query
    async def query(self, destination, query):
        # get next query id (qid) and increment counter for next time
        qid = self.next_qid
        self.next_qid += 1
        # Add a internal dedicated queue for this query id
        self.queries[qid] = asyncio.Queue()
        # Update message with qid and source reference (as python object for now)
        query.update({'qid':qid, 'src':self})
        # Put the message into the destination (global) queue
        await destination.input.put(query)
        # Return the query id
        return qid
    
    async def delegate(self, destination, query):
        self.debug("Delegating to " + str(destination))
        await destination.input.put(query)
        

    async def wait_for_reply(self, qid, timeout = 10.):
        return await asyncio.wait_for(self.queries[qid].get(), timeout, loop = self.env.loop)

    async def aget(self, portname = None):
        """Return a ElementTree that represent the Node full state (if possible) or the port value
        """
        self.warning("Unimplemented aget() method.")

    def serialize(self):
        """
        """
        pass

    def connect(self, dest, **kwargs):
        #TODO: whole thing...
        pass

    def debug(self, *args, logger='main'):
        self.env.loggers[logger].debug(*args)

    def info(self, *args, logger='main'):
        self.env.loggers[logger].info(*args)

    def warning(self, *args, logger='main'):
        self.env.loggers[logger].warning(*args)

    def error(self, *args, logger='main'):
        self.env.loggers[logger].error(*args)
