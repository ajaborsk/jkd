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
    def __init__(self, env = None):
        #print("setting env to", env)
        self.env = env
        self.input = asyncio.Queue()
        self.triggers = []
        self.done = False

    async def mainloop(self):
        while not self.done:
            msg = await self.input.get()
            await self.msg_handle(msg)

    async def msg_handle(self, msg):
        logger.warning("Unimplemented msg_handle() method.")

    def get_etnode(self):
        return ET.Element()

    async def aget(self, portname = None):
        """Return a ElementTree that represent the Node full state (if possible) or the port value
        """
        logger.warning("Unimplemented aget() method.")

    def serialize(self):
        """
        """
        pass

